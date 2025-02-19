import os
import json
import re
from collections import Counter
from datetime import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup
from dotenv import load_dotenv
from anthropic import Anthropic
from dateutil.parser import parse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key_here")

# Initialize cache cleanup
def cleanup_cache():
    """Remove old cache entries (older than 1 hour)"""
    if hasattr(app.config, 'analysis_cache'):
        current_time = datetime.now()
        app.config['cache_times'] = {k: v for k, v in app.config.get('cache_times', {}).items() 
                                   if (current_time - v).total_seconds() < 3600}
        app.config['analysis_cache'] = {k: v for k, v in app.config['analysis_cache'].items() 
                                      if k in app.config['cache_times']}

# Initialize APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_cache, trigger="interval", hours=1)
scheduler.start()

# API keys and configuration
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_articles(articles, query):
    """Extract key metrics and patterns from articles."""
    # Batch sentiment analysis for all articles
    texts = [f"{article['title']} {article['description'] or ''}" for article in articles]
    batch_text = "\n---\n".join(texts)
    
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Analyze the sentiment of each text block separated by '---' and respond with ONLY a comma-separated list of numbers between -1 (most negative) and 1 (most positive).
            Example response format: 0.5,-0.2,0.8
            
            {batch_text}"""
        }]
    )
    
    try:
        sentiments = [float(s.strip()) for s in response.content[0].text.strip().split(',')]
        # Ensure we have the right number of sentiments
        if len(sentiments) == len(articles):
            for article, sentiment in zip(articles, sentiments):
                article['sentiment'] = max(-1, min(1, sentiment))  # Ensure value is between -1 and 1
        else:
            # If mismatch, default to neutral
            for article in articles:
                article['sentiment'] = 0
    except (ValueError, TypeError, IndexError):
        # Default to neutral if parsing fails
        for article in articles:
            article['sentiment'] = 0
    
    # Publication timeline
    dates = {}
    for article in articles:
        date = parse(article['publishedAt']).strftime('%Y-%m-%d')
        dates[date] = dates.get(date, 0) + 1
    timeline = [{'date': k, 'count': v} for k, v in sorted(dates.items())]
    
    # News source distribution
    sources = Counter(article['source']['name'] for article in articles)
    top_sources = [{'name': name, 'count': count} 
                   for name, count in sources.most_common(10)]
    
    # Extended stop words list
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
        'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over',
        'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'can', 'could', 'may', 'might', 'must', 'it', 'its',
        'during', 'while', 'before', 'after', 'under', 'over'
    }
    
    # Add search terms to stop words
    search_terms = set(query.lower().split())
    stop_words.update(search_terms)
    
    # Topic extraction with better filtering
    text = ' '.join(article['title'] + ' ' + (article['description'] or '')
                   for article in articles).lower()
    words = re.findall(r'\b\w+\b', text)
    topics = Counter(word for word in words 
                    if word not in stop_words 
                    and len(word) > 2 
                    and not word.isnumeric()
                    and not any(char.isdigit() for char in word))
    
    top_topics = [{'topic': topic, 'count': count} 
                  for topic, count in topics.most_common(30)
                  if count > 2]  # Only include topics mentioned more than twice

    # Calculate average sentiment
    total_sentiment = sum(article['sentiment'] for article in articles)
    avg_sentiment = total_sentiment / len(articles) if articles else 0

    return {
        'timeline': timeline,
        'sources': top_sources,
        'topics': top_topics,
        'total_articles': len(articles),
        'date_range': {
            'start': timeline[0]['date'] if timeline else None,
            'end': timeline[-1]['date'] if timeline else None
        },
        'avg_sentiment': avg_sentiment
    }

def validate_date_range(from_date, to_date):
    """Validate that the date range is no more than 30 days."""
    try:
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        date_difference = (end_date - start_date).days
        
        if date_difference > 30:
            raise ValueError("Date range cannot exceed 30 days")
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
            
        return True
    except ValueError as e:
        raise ValueError(str(e))
    except Exception:
        raise ValueError("Invalid date format")

def fetch_news(keywords, from_date=None, to_date=None, language="en", domains=None):
    """Fetch news articles from News API."""
    base_url = "https://newsapi.org/v2/everything"
    query_params = {
        "q": keywords,
        "language": language,
        "apiKey": NEWS_API_KEY,
        "sortBy": "relevancy",
        "pageSize": 30  # Reduced page size for better performance
    }
    
    if from_date:
        query_params["from"] = from_date
    if to_date:
        query_params["to"] = to_date
    if domains:
        query_params["domains"] = domains

    response = requests.get(base_url, params=query_params)
    if response.status_code != 200:
        raise Exception(f"News API error: {response.text}")
    return response.json().get("articles", [])

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query1 = request.form.get("query1", "").strip()
        query2 = request.form.get("query2", "").strip()
        from_date1 = request.form.get("from_date1", "").strip()
        to_date1 = request.form.get("to_date1", "").strip()
        from_date2 = request.form.get("from_date2", "").strip()
        to_date2 = request.form.get("to_date2", "").strip()
        
        # Validate inputs
        errors = []
        if not query1:
            errors.append("Please enter at least one search term")
        if not from_date1 or not to_date1:
            errors.append("Please select a date range for the first query")
        if query2 and (not from_date2 or not to_date2):
            errors.append("Please select a date range for the second query")
            
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for("index"))
        
        try:
            # Validate date ranges
            validate_date_range(from_date1, to_date1)
            if query2 and (from_date2 and to_date2):
                validate_date_range(from_date2, to_date2)
            
            # Fetch and analyze articles for the first query
            articles1 = fetch_news(
                keywords=query1,
                from_date=from_date1,
                to_date=to_date1
            )
            analysis1 = analyze_articles(articles1, query1)
            
            # Initialize variables for second query
            articles2 = []
            analysis2 = None
            analysis_text = None
            
            if query2:
                # Use second date range if provided, otherwise use first date range
                query2_from_date = from_date2 if from_date2 else from_date1
                query2_to_date = to_date2 if to_date2 else to_date1
                
                # Fetch and analyze articles for the second query
                articles2 = fetch_news(
                    keywords=query2,
                    from_date=query2_from_date,
                    to_date=query2_to_date
                )
                analysis2 = analyze_articles(articles2, query2)
                
                # Get Claude's comparative analysis only if query2 is provided
                def summarize_articles(articles):
                    return [{
                        'title': article['title'],
                        'description': article['description'],
                        'publishedAt': article['publishedAt']
                    } for article in articles]

                # Check cache with both date ranges
                cache_key = f"{query1}_{query2}_{from_date1}_{to_date1}_{from_date2}_{to_date2}"
                cached_response = app.config.get('analysis_cache', {}).get(cache_key)
                
                if cached_response:
                    analysis_text = cached_response
                else:
                    summarized_articles1 = summarize_articles(articles1)
                    summarized_articles2 = summarize_articles(articles2)
                    
                    # Prepare the analysis prompt
                    analysis_prompt = f"""Compare news coverage between {query1} ({from_date1} to {to_date1}) and {query2} ({query2_from_date} to {query2_to_date}).
                    Key points:
                    1. Major coverage differences
                    2. Key trends
                    3. Business implications
                    
                    {query1} articles: {json.dumps(summarized_articles1)}
                    {query2} articles: {json.dumps(summarized_articles2)}"""
                
                # Get analysis from Claude
                response = anthropic.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": analysis_prompt
                    }]
                )
                
                analysis_text = response.content[0].text
                
                # Cache the response with timestamp
                if not hasattr(app.config, 'analysis_cache'):
                    app.config['analysis_cache'] = {}
                    app.config['cache_times'] = {}
                app.config['analysis_cache'][cache_key] = analysis_text
                app.config['cache_times'][cache_key] = datetime.now()
            
            return render_template(
                "result.html",
                query1=query1,
                query2=query2,
                textual_analysis=analysis_text,
                analysis1=analysis1,
                analysis2=analysis2,
                articles1=articles1,
                articles2=articles2
            )
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for("index"))
            
    return render_template("index.html")

if __name__ == "__main__":
    # Get port from environment variable or default to 5005
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port, debug=True)
