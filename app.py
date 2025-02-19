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
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric,
    Dimension
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key_here")

# API keys and configuration
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID")

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_articles(articles, query):
    """Extract key metrics and patterns from articles."""
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

    return {
        'timeline': timeline,
        'sources': top_sources,
        'topics': top_topics,
        'total_articles': len(articles),
        'date_range': {
            'start': timeline[0]['date'] if timeline else None,
            'end': timeline[-1]['date'] if timeline else None
        }
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

def get_analytics_data():
    """Fetch analytics data from GA4."""
    try:
        client = BetaAnalyticsDataClient()
        property_id = f"properties/{os.environ.get('GA4_PROPERTY_ID')}"

        request = RunReportRequest(
            property=property_id,
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="screenPageViews"),
                Metric(name="averageSessionDuration")
            ],
            dimensions=[Dimension(name="date")]
        )
        
        response = client.run_report(request)
        
        analytics_data = {
            'total_users': 0,
            'total_pageviews': 0,
            'avg_session_duration': 0,
            'daily_data': []
        }
        
        for row in response.rows:
            date = row.dimension_values[0].value
            users = int(row.metric_values[0].value)
            pageviews = int(row.metric_values[1].value)
            duration = float(row.metric_values[2].value)
            
            analytics_data['total_users'] += users
            analytics_data['total_pageviews'] += pageviews
            analytics_data['daily_data'].append({
                'date': date,
                'users': users,
                'pageviews': pageviews,
                'duration': duration
            })
        
        if response.rows:
            analytics_data['avg_session_duration'] = sum(
                float(row.metric_values[2].value) for row in response.rows
            ) / len(response.rows)
            
        return analytics_data
    except Exception as e:
        print(f"Analytics error: {str(e)}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query1 = request.form.get("query1", "").strip()
        query2 = request.form.get("query2", "").strip()
        from_date = request.form.get("from_date", "").strip()
        to_date = request.form.get("to_date", "").strip()
        
        # Validate inputs
        errors = []
        if not query1 or not query2:
            errors.append("Please enter both search terms")
        if not from_date or not to_date:
            errors.append("Please select a date range")
            
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for("index"))
        
        try:
            # Validate date range
            validate_date_range(from_date, to_date)
            
            # Fetch news articles for both queries
            articles1 = fetch_news(
                keywords=query1,
                from_date=from_date,
                to_date=to_date
            )
            
            articles2 = fetch_news(
                keywords=query2,
                from_date=from_date,
                to_date=to_date
            )
            
            # Analyze articles for both queries
            analysis1 = analyze_articles(articles1, query1)
            analysis2 = analyze_articles(articles2, query2)
            
            # Get Claude's comparative analysis
            prompt = f"""Compare and analyze news coverage between {query1} and {query2}. 
            Focus on:
            1. Major differences in coverage and themes
            2. Comparative statistics and metrics
            3. Notable trends or patterns unique to each
            4. Business/industry implications for both
            
            Format your response with clear sections and bullet points for readability.
            
            Articles for {query1}:
            {json.dumps(articles1, indent=2)}
            
            Articles for {query2}:
            {json.dumps(articles2, indent=2)}"""
            
            response = anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return render_template(
                "result.html",
                query1=query1,
                query2=query2,
                textual_analysis=response.content[0].text,
                analysis1=analysis1,
                analysis2=analysis2,
                articles1=articles1,
                articles2=articles2
            )
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for("index"))
            
    analytics_data = None
    if request.method == "GET":
        try:
            analytics_data = get_analytics_data()
        except Exception as e:
            print(f"Failed to fetch analytics: {str(e)}")
    
    return render_template(
        "index.html",
        ga_measurement_id=GA_MEASUREMENT_ID,
        analytics_data=analytics_data
    )

if __name__ == "__main__":
    # Get port from environment variable or default to 5005
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port, debug=True)
