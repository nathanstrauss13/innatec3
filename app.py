import os
import json
import re
from collections import Counter
from datetime import datetime, timedelta
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
    
    # Create a numbered list for Claude to reference
    numbered_texts = "\n\n".join(f"Text {i+1}:\n{text}" for i, text in enumerate(texts))
    
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Analyze the sentiment of each numbered text and respond with a JSON array of sentiment scores between -1 (most negative) and 1 (most positive).

For each text:
- Consider the overall tone, word choice, and context
- Score negative news/criticism closer to -1
- Score positive news/achievements closer to +1
- Score neutral/factual content closer to 0

Example response format: [-0.8, 0.5, 0.2]

Here are the texts to analyze:

{numbered_texts}"""
        }]
    )
    
    try:
        # Extract the array from Claude's response by finding text between [ and ]
        sentiment_text = response.content[0].text
        print("Anthropic API Response:", sentiment_text)  # Log the response for debugging
        array_match = re.search(r'\[(.*?)\]', sentiment_text, re.DOTALL)
        if array_match:
            # Parse the comma-separated values into floats
            # Extract numbers using regex
            sentiment_values = re.findall(r'-?\d+\.?\d*', array_match.group(1))
            sentiments = []
            for value in sentiment_values:
                try:
                    parsed_value = float(value)
                    print(f"Successfully parsed value: {parsed_value}")  # Debug log
                    sentiments.append(parsed_value)
                except ValueError as e:
                    print(f"Failed to parse value: '{value}'")  # Debug log
            print(f"Found {len(sentiments)} sentiments for {len(articles)} articles")
            # Use available sentiments, pad with 0 if needed
            for i, article in enumerate(articles):
                if i < len(sentiments):
                    sentiment = max(-1, min(1, sentiments[i]))
                    article['sentiment'] = sentiment
                    print(f"Assigned sentiment {sentiment} to article: {article['title'][:50]}...")
                else:
                    article['sentiment'] = 0
                    print(f"Using neutral sentiment for article: {article['title'][:50]}...")
        else:
            # If no array found, use neutral sentiment
            for article in articles:
                article['sentiment'] = 0
    except (ValueError, TypeError, IndexError, AttributeError) as e:
        print("Error parsing sentiment response:", e)  # Log parsing errors
        # Default to neutral if parsing fails
        for article in articles:
            article['sentiment'] = 0
    
    # Publication timeline with articles
    dates = {}
    articles_by_date = {}
    for article in articles:
        date = parse(article['publishedAt']).strftime('%Y-%m-%d')
        dates[date] = dates.get(date, 0) + 1
        
        # Store articles for each date
        if date not in articles_by_date:
            articles_by_date[date] = []
        articles_by_date[date].append({
            'title': article['title'],
            'source': article['source']['name'],
            'url': article['url'],
            'sentiment': article['sentiment']
        })
    
    # Create timeline with articles
    timeline = []
    for date, count in sorted(dates.items()):
        # Get the article with the highest absolute sentiment score for this date
        date_articles = articles_by_date[date]
        peak_article = max(date_articles, key=lambda x: abs(x['sentiment']))
        
        timeline.append({
            'date': date,
            'count': count,
            'peak_article': peak_article
        })
    
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
    sentiments = [article['sentiment'] for article in articles]
    print(f"All sentiment values: {sentiments}")
    total_sentiment = sum(sentiments)
    print(f"Total sentiment: {total_sentiment}")
    avg_sentiment = total_sentiment / len(articles) if articles else 0
    print(f"Average sentiment: {avg_sentiment}")

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
            
        return True, start_date, end_date
    except ValueError as e:
        raise ValueError(str(e))
    except Exception:
        raise ValueError("Invalid date format")

# List of major news sources and their variations
MAJOR_NEWS_SOURCES = {
    # Top-tier business sources
    'bloomberg', 'bloomberg.com',
    'reuters', 'reuters.com',
    'wsj', 'wall street journal', 'wsj.com',
    'financial times', 'ft.com', 'ft',
    'cnbc', 'cnbc.com',
    'marketwatch', 'marketwatch.com',
    'seeking alpha', 'seekingalpha.com',
    'barron', 'barrons',
    'economist',
    
    # Major news organizations
    'nytimes', 'new york times', 'ny times',
    'washington post', 'washingtonpost',
    'bbc', 'bbc news',
    'associated press', 'ap news', 'ap',
    'cnn', 'cnn business',
    
    # Business-focused outlets
    'business insider', 'businessinsider',
    'forbes', 'forbes.com',
    'fortune', 'fortune.com',
    'yahoo finance', 'yahoo',
    'benzinga',
    'investing.com',
    'motley fool',
    
    # Tech business coverage
    'techcrunch',
    'venturebeat',
    'wired',
    'zdnet'
}

def fetch_news(keywords, from_date=None, to_date=None, language="en"):
    """Fetch news articles combining top business headlines and relevant articles."""
    articles = []
    
    # First, get top business headlines from major sources
    headlines_url = "https://newsapi.org/v2/top-headlines"
    headlines_params = {
        "q": keywords,
        "language": language,
        "category": "business",
        "apiKey": NEWS_API_KEY,
        "pageSize": 30,  # Reduced to ensure we get articles from both endpoints
        "domains": "wsj.com,reuters.com,bloomberg.com,ft.com,cnbc.com,forbes.com"  # Top business domains
    }
    
    try:
        headlines_response = requests.get(headlines_url, params=headlines_params)
        if headlines_response.status_code == 200:
            articles.extend(headlines_response.json().get("articles", []))
    except Exception as e:
        print(f"Error fetching headlines: {e}")
    
    # Then, get additional relevant articles from business sections and other quality sources
    everything_url = "https://newsapi.org/v2/everything"
    everything_params = {
        "q": f"{keywords} AND (business OR earnings OR market OR industry OR company OR revenue)",
        "language": language,
        "sortBy": "relevancy",
        "apiKey": NEWS_API_KEY,
        "pageSize": 30,  # Reduced to ensure we get a balanced mix
        "domains": "nytimes.com,washingtonpost.com,bbc.com,economist.com,businessinsider.com,marketwatch.com"  # Additional quality sources
    }
    
    # Add date parameters if provided
    if from_date:
        everything_params["from"] = from_date
    if to_date:
        # Add one day to include the end date in results
        end_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        everything_params["to"] = end_date.strftime("%Y-%m-%d")
    
    try:
        everything_response = requests.get(everything_url, params=everything_params)
        if everything_response.status_code == 200:
            articles.extend(everything_response.json().get("articles", []))
    except Exception as e:
        print(f"Error fetching articles: {e}")

    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    for article in articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    # Filter articles by source and sort by publishedAt
    filtered_articles = []
    for article in unique_articles:
        source_name = article['source'].get('name', '').lower()
        source_domain = article.get('url', '').lower().split('/')[2] if article.get('url') else ''
        
        # Check if source name contains any major source variation
        # or if the article URL domain matches a major source
        is_major_source = any(source.lower() in source_name or source.lower() in source_domain 
                            for source in MAJOR_NEWS_SOURCES)
        
        # Also include if it's from a business section
        is_business_section = 'business' in source_name.lower() or '/business/' in article.get('url', '').lower()
        
        if is_major_source or is_business_section:
            filtered_articles.append(article)
    
    # Sort by published date, newest first
    filtered_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    # Return top 100 articles
    return filtered_articles[:100]

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
                # Fetch and analyze articles for the second query
                articles2 = fetch_news(
                    keywords=query2,
                    from_date=from_date2 if from_date2 else from_date1,
                    to_date=to_date2 if to_date2 else to_date1
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
                    analysis_prompt = f"""Compare news coverage between {query1} ({from_date1} to {to_date1}) and {query2} ({from_date2 if from_date2 else from_date1} to {to_date2 if to_date2 else to_date1}).
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
    # Get port from environment variable or default to 5007
    port = int(os.environ.get("PORT", 5007))
    app.run(host='0.0.0.0', port=port, debug=True)
