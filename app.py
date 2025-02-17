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
from dateutil.relativedelta import relativedelta
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
        # Common English words
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
        'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over',
        'after', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'can', 'could', 'may', 'might', 'must', 'it', 'its',
        'this', 'that', 'these', 'those', 'he', 'she', 'they', 'we', 'you',
        
        # Common content words
        'said', 'says', 'one', 'two', 'three', 'first', 'last', 'year',
        'years', 'month', 'months', 'day', 'days', 'today', 'tomorrow',
        'here', 'there', 'where', 'when', 'why', 'how', 'what', 'which',
        'who', 'whom', 'whose', 'get', 'got', 'getting', 'make', 'made',
        'making', 'take', 'took', 'taking', 'see', 'saw', 'seeing',
        'come', 'came', 'coming', 'go', 'went', 'going', 'know', 'knew',
        'knowing', 'think', 'thought', 'thinking', 'say', 'saying',
        'said', 'just', 'now', 'like', 'also', 'then', 'than',
        'more', 'most', 'some', 'all', 'any', 'many', 'much',
        'your', 'my', 'our', 'their', 'his', 'her', 'its',
        'during', 'while', 'before', 'after', 'under', 'over',
        
        # Numbers and time-related
        '2024', '2025', 'january', 'february', 'march', 'april', 'may',
        'june', 'july', 'august', 'september', 'october', 'november',
        'december', 'monday', 'tuesday', 'wednesday', 'thursday',
        'friday', 'saturday', 'sunday'
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
    """Validate that the date range is within the last 30 days."""
    try:
        today = datetime.today()
        thirty_days_ago = today - relativedelta(days=30)
        
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        if start_date < thirty_days_ago or end_date > today:
            raise ValueError("Date range must be within the last 30 days")
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
        "pageSize": 100  # Get more articles for better analysis
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
        query = request.form.get("query", "").strip()
        from_date = request.form.get("from_date", "").strip()
        to_date = request.form.get("to_date", "").strip()
        
        # Validate inputs
        errors = []
        if not query:
            errors.append("Please enter a search query")
        if not from_date or not to_date:
            errors.append("Please select a date range")
            
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for("index"))
        
        try:
            # Validate date range
            validate_date_range(from_date, to_date)
            
            # Fetch news articles
            articles = fetch_news(
                keywords=query,
                from_date=from_date,
                to_date=to_date
            )
            
            # Analyze articles
            analysis = analyze_articles(articles, query)
            
            # Get Claude's text analysis
            prompt = f"""Analyze these news articles about {query} and provide key insights about major themes, trends, and developments. 
            Focus on:
            1. Major news stories and developments
            2. Key statistics and metrics
            3. Notable trends or patterns
            4. Business/industry implications
            
            Format your response with clear sections and bullet points for readability.
            
            Articles data:
            {json.dumps(articles, indent=2)}"""
            
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
                query=query,
                textual_analysis=response.content[0].text,
                analysis=analysis,
                articles=articles
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
    # Get port from environment variable or default to 5001
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
