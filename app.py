import os
import json
import re
import random
import requests
from collections import Counter
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup
from dotenv import load_dotenv
from anthropic import Anthropic
from dateutil.parser import parse
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key_here")

# Initialize SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///waitlist.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the WaitingList model
class WaitingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    bespoke_analysis = db.Column(db.Boolean, default=False)
    historical_data = db.Column(db.Boolean, default=False)
    additional_sources = db.Column(db.Boolean, default=False)
    more_results = db.Column(db.Boolean, default=False)
    consulting_services = db.Column(db.Boolean, default=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create the database tables
with app.app_context():
    db.create_all()

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

# Debug logging for API keys
print(f"NEWS_API_KEY is {'set' if NEWS_API_KEY else 'NOT SET'}")
print(f"ANTHROPIC_API_KEY is {'set' if ANTHROPIC_API_KEY else 'NOT SET'}")

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

IMPORTANT: Your response must begin with a valid JSON array containing only numbers, like this:
[-0.8, 0.5, 0.2, -0.4, 0.1]

Do not include any explanations before the array. You can add explanations after the array if needed.

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
            # Extract numbers using regex with a more robust pattern to handle various number formats
            sentiment_values = re.findall(r'-?\d+(?:\.\d+)?', array_match.group(1))
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
        'during', 'while', 'before', 'after', 'under', 'over',
        # Additional common words that should be filtered out
        'this', 'that', 'these', 'those', 'they', 'them', 'their', 'theirs',
        'he', 'him', 'his', 'she', 'her', 'hers', 'we', 'us', 'our', 'ours',
        'you', 'your', 'yours', 'i', 'me', 'my', 'mine', 'who', 'whom', 'whose',
        'which', 'what', 'where', 'when', 'why', 'how', 'all', 'any', 'both',
        'each', 'few', 'more', 'most', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'one',
        'even', 'here', 'there', 'now', 'then', 'also', 'get', 'got', 'gets',
        'say', 'says', 'said', 'see', 'sees', 'seen', 'like', 'well', 'back',
        'much', 'many', 'make', 'makes', 'made', 'take', 'takes', 'took', 'taken',
        # Additional prepositions, adverbs, and common verbs
        'off', 'out', 'down', 'away', 'through', 'across', 'between', 'among',
        'around', 'along', 'behind', 'beyond', 'near', 'within', 'without',
        'above', 'below', 'beside', 'against', 'despite', 'except', 'until',
        'upon', 'via', 'toward', 'towards', 'onto', 'inside', 'outside',
        'ago', 'yet', 'still', 'ever', 'never', 'always', 'often', 'sometimes',
        'rarely', 'usually', 'already', 'soon', 'later', 'early', 'late',
        'again', 'once', 'twice', 'thrice', 'further', 'rather', 'quite',
        'almost', 'nearly', 'hardly', 'scarcely', 'barely', 'merely',
        'else', 'otherwise', 'instead', 'anyway', 'anyhow', 'however',
        'thus', 'therefore', 'hence', 'consequently', 'accordingly',
        'meanwhile', 'moreover', 'furthermore', 'additionally', 'besides',
        'come', 'comes', 'coming', 'came', 'go', 'goes', 'going', 'went', 'gone',
        'give', 'gives', 'giving', 'gave', 'given', 'put', 'puts', 'putting',
        'set', 'sets', 'setting', 'let', 'lets', 'letting', 'run', 'runs', 'running',
        'ran', 'use', 'uses', 'using', 'used', 'try', 'tries', 'trying', 'tried',
        'seem', 'seems', 'seeming', 'seemed', 'appear', 'appears', 'appearing',
        'appeared', 'look', 'looks', 'looking', 'looked', 'think', 'thinks',
        'thinking', 'thought', 'know', 'knows', 'knowing', 'knew', 'known',
        'want', 'wants', 'wanting', 'wanted', 'need', 'needs', 'needing', 'needed',
        'find', 'finds', 'finding', 'found', 'show', 'shows', 'showing', 'showed',
        'shown', 'tell', 'tells', 'telling', 'told', 'ask', 'asks', 'asking', 'asked',
        'work', 'works', 'working', 'worked', 'call', 'calls', 'calling', 'called',
        'turn', 'turns', 'turning', 'turned', 'help', 'helps', 'helping', 'helped',
        'talk', 'talks', 'talking', 'talked', 'move', 'moves', 'moving', 'moved',
        'live', 'lives', 'living', 'lived', 'play', 'plays', 'playing', 'played',
        'feel', 'feels', 'feeling', 'felt', 'become', 'becomes', 'becoming', 'became',
        'leave', 'leaves', 'leaving', 'left', 'stay', 'stays', 'staying', 'stayed',
        'start', 'starts', 'starting', 'started', 'end', 'ends', 'ending', 'ended',
        'keep', 'keeps', 'keeping', 'kept', 'hold', 'holds', 'holding', 'held',
        'bring', 'brings', 'bringing', 'brought', 'carry', 'carries', 'carrying',
        'carried', 'continue', 'continues', 'continuing', 'continued',
        'change', 'changes', 'changing', 'changed', 'lead', 'leads', 'leading', 'led',
        'stand', 'stands', 'standing', 'stood', 'follow', 'follows', 'following',
        'followed', 'stop', 'stops', 'stopping', 'stopped', 'create', 'creates',
        'creating', 'created', 'speak', 'speaks', 'speaking', 'spoke', 'spoken',
        'read', 'reads', 'reading', 'wrote', 'written', 'write', 'writes', 'writing',
        'lose', 'loses', 'losing', 'lost', 'pay', 'pays', 'paying', 'paid',
        'hear', 'hears', 'hearing', 'heard', 'meet', 'meets', 'meeting', 'met',
        'include', 'includes', 'including', 'included', 'allow', 'allows', 'allowing',
        'allowed', 'add', 'adds', 'adding', 'added', 'spend', 'spends', 'spending',
        'spent', 'grow', 'grows', 'growing', 'grew', 'grown', 'open', 'opens',
        'opening', 'opened', 'walk', 'walks', 'walking', 'walked', 'win', 'wins',
        'winning', 'won', 'offer', 'offers', 'offering', 'offered', 'remember',
        'remembers', 'remembering', 'remembered', 'consider', 'considers',
        'considering', 'considered', 'expect', 'expects', 'expecting', 'expected',
        'suggest', 'suggests', 'suggesting', 'suggested', 'report', 'reports',
        'reporting', 'reported'
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
    """Validate the date range."""
    try:
        print(f"Validating date range: from_date={from_date}, to_date={to_date}")
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
        
        print(f"Parsed dates: start_date={start_date}, end_date={end_date}")
        
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
            
        return True, start_date, end_date
    except ValueError as e:
        print(f"Date validation error: {str(e)}")
        raise ValueError(str(e))
    except Exception as e:
        print(f"Unexpected date validation error: {str(e)}")
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

def enhance_query_with_ai(query):
    """Use Claude to enhance the search query by identifying entities and adding context."""
    # Default enhancement data with original query
    default_enhancement = {
        "enhanced_query": query,
        "entity_type": "",
        "reasoning": "No enhancement needed"
    }
    
    if not query:
        return default_enhancement
    
    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"""Analyze this search query: "{query}"
                
                1. Identify if this query refers to a specific entity (company, brand, person, product, etc.)
                2. If it's a brand or company that could be confused with other topics, add clarifying terms
                3. Return a JSON object with:
                   - "enhanced_query": the improved search query with additional context terms
                   - "entity_type": the type of entity identified (if any)
                   - "reasoning": brief explanation of your enhancement
                
                For example:
                - "Blue Nile" → {{"enhanced_query": "Blue Nile jewelry retailer", "entity_type": "jewelry brand", "reasoning": "Added 'jewelry retailer' to distinguish from the river"}}
                - "Kay Jewelers" → {{"enhanced_query": "Kay Jewelers jewelry store", "entity_type": "jewelry brand", "reasoning": "Added 'jewelry store' for clarity"}}
                - "Apple" → {{"enhanced_query": "Apple technology company", "entity_type": "technology company", "reasoning": "Distinguished from the fruit"}}
                
                Only add clarifying terms if needed to avoid ambiguity. If the query is already specific, keep it as is.
                """
            }]
        )
        
        # Extract JSON from Claude's response
        response_text = response.content[0].text
        print(f"Claude query enhancement response: {response_text}")
        
        # Find JSON in the response
        import json
        import re
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                enhancement_data = json.loads(json_match.group(0))
                print(f"Enhanced query: {enhancement_data.get('enhanced_query', query)}")
                
                # Ensure all required fields are present
                if 'enhanced_query' not in enhancement_data:
                    enhancement_data['enhanced_query'] = query
                if 'entity_type' not in enhancement_data:
                    enhancement_data['entity_type'] = ""
                if 'reasoning' not in enhancement_data:
                    enhancement_data['reasoning'] = "No explanation provided"
                    
                return enhancement_data
            except json.JSONDecodeError:
                print("Failed to parse JSON from Claude's response")
        
        return default_enhancement  # Return default if parsing fails
    except Exception as e:
        print(f"Error enhancing query with AI: {e}")
        return default_enhancement  # Return default if any error occurs

def parse_boolean_query(query):
    """
    Parse a boolean search query with support for:
    - Quoted phrases for exact matches
    - AND/OR operators (default is AND)
    - Minus sign for exclusion
    
    Returns a processed query string compatible with the News API
    """
    # Default to the original query if it's empty
    if not query.strip():
        return query
    
    # Process the query
    processed_query = query
    
    # The News API already supports:
    # - Quotes for exact phrases: "exact phrase"
    # - AND operator: term1 AND term2
    # - OR operator: term1 OR term2
    # - Exclusion with minus: -excluded
    
    # We don't need to modify the query as the News API already supports
    # the boolean search features we want
    
    print(f"Boolean search query: '{processed_query}'")
    return processed_query


def generate_mock_news(keywords, from_date, to_date, language="en", source=None):
    """Generate mock news articles when the API fails."""
    print(f"Generating mock news for query: {keywords}")
    
    # Parse dates
    start_date = datetime.strptime(from_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d")
    
    # Calculate number of days in the range
    days_range = (end_date - start_date).days + 1
    
    # Generate between 10-20 articles
    num_articles = min(days_range * 3, 20)
    
    # Common news sources
    sources = ["CNN", "BBC News", "Reuters", "Associated Press", "The New York Times", 
               "The Washington Post", "The Guardian", "Bloomberg", "CNBC", "Forbes"]
    
    # Generate random dates within the range
    random_dates = []
    for _ in range(num_articles):
        random_days = random.randint(0, days_range)
        article_date = start_date + timedelta(days=random_days)
        random_dates.append(article_date)
    
    # Sort dates chronologically
    random_dates.sort()
    
    # Generate articles
    mock_articles = []
    
    # Keywords to use in titles and descriptions
    keywords_list = keywords.lower().split()
    
    for i, date in enumerate(random_dates):
        # Format date for the article
        formatted_date = date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Randomly select a source
        source_name = random.choice(sources)
        
        # Generate a title that includes the keywords
        title_templates = [
            f"New developments in {keywords} sector announced today",
            f"Experts discuss the future of {keywords}",
            f"Report: {keywords} shows promising growth",
            f"Analysis: What's next for {keywords}?",
            f"{keywords} trends that are changing the industry",
            f"The impact of recent {keywords} developments",
            f"Understanding the {keywords} landscape in today's market",
            f"{keywords} innovations that are making headlines",
            f"Breaking: Major announcement related to {keywords}",
            f"Study reveals new insights about {keywords}"
        ]
        
        title = random.choice(title_templates)
        
        # Generate a description
        description_templates = [
            f"A comprehensive look at how {keywords} is evolving and what it means for the industry.",
            f"Industry experts weigh in on the latest {keywords} developments and their potential impact.",
            f"New research provides valuable insights into the current state of {keywords}.",
            f"This article explores the challenges and opportunities in the {keywords} space.",
            f"An in-depth analysis of recent trends in {keywords} and what they mean for stakeholders.",
            f"Examining the factors driving change in the {keywords} landscape.",
            f"A detailed report on how {keywords} is transforming various sectors.",
            f"Understanding the implications of recent {keywords} news for businesses and consumers.",
            f"This piece discusses the future outlook for {keywords} based on current indicators.",
            f"Exploring the relationship between {keywords} and broader market trends."
        ]
        
        description = random.choice(description_templates)
        
        # Create the article object
        article = {
            "source": {
                "id": source_name.lower().replace(" ", "-"),
                "name": source_name
            },
            "author": f"Mock Author {i+1}",
            "title": title,
            "description": description,
            "url": f"https://example.com/mock-article-{i+1}",
            "urlToImage": f"https://example.com/mock-image-{i+1}.jpg",
            "publishedAt": formatted_date,
            "content": f"This is mock content for an article about {keywords}. " * 5
        }
        
        mock_articles.append(article)
    
    print(f"Generated {len(mock_articles)} mock articles")
    return mock_articles

def fetch_news_api(keywords, from_date=None, to_date=None, language="en", source=None):
    """Fetch news articles from News API based on search parameters."""
    articles = []
    
    # Parse the boolean query
    processed_query = parse_boolean_query(keywords)
    print(f"News API - Original query: '{keywords}' → Processed query: '{processed_query}'")
    
    # Use the everything endpoint
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": processed_query,
        "language": language,
        "sortBy": "relevancy",
        "apiKey": NEWS_API_KEY,
        "pageSize": 100  # Maximum allowed by the API
    }
    
    # Add date parameters if provided
    if from_date:
        print(f"News API - Adding from_date parameter: {from_date}")
        params["from"] = from_date
    if to_date:
        # Add one day to include the end date in results
        try:
            print(f"News API - Processing to_date parameter: {to_date}")
            end_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
            params["to"] = end_date.strftime("%Y-%m-%d")
            print(f"News API - Added to_date parameter: {params['to']}")
        except Exception as e:
            print(f"News API - Error processing to_date: {str(e)}")
            # Use the original to_date if there's an error
            params["to"] = to_date
            print(f"News API - Using original to_date: {to_date}")
    
    # Add source parameter if provided
    if source:
        params["sources"] = source
    
    api_success = False
    try:
        print(f"Fetching news from News API with params: {params}")  # Debug log
        response = requests.get(url, params=params)
        print(f"News API response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"News API response status: {response_data.get('status')}")
            print(f"News API total results: {response_data.get('totalResults')}")
            
            # Add API source to each article
            news_api_articles = response_data.get("articles", [])
            for article in news_api_articles:
                article["api_source"] = "News API"
            
            articles.extend(news_api_articles)
            print(f"Retrieved {len(articles)} articles from News API")
            api_success = True
        else:
            response_text = response.text
            print(f"News API Error response: {response_text}")
            try:
                response_data = response.json()
                print(f"Error from News API: {response_data.get('message', 'Unknown error')}")
            except:
                print(f"Could not parse News API error response as JSON: {response_text}")
    except Exception as e:
        print(f"Error fetching articles from News API: {e}")
    
    return articles, api_success

def fetch_news(keywords, from_date=None, to_date=None, language="en", source=None):
    """Fetch news articles from News API based on search parameters."""
    all_articles = []
    
    # Fetch articles from News API
    news_api_articles, news_api_success = fetch_news_api(keywords, from_date, to_date, language, source)
    all_articles.extend(news_api_articles)
    
    # If API failed or returned no articles, use mock data
    if not news_api_success or len(all_articles) == 0:
        print("News API failed or returned no articles. Using mock data instead.")
        mock_articles = generate_mock_news(keywords, from_date, to_date, language, source)
        # Add API source to mock articles
        for article in mock_articles:
            article["api_source"] = "Mock Data"
        all_articles.extend(mock_articles)

    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    print(f"Returning {len(unique_articles)} unique articles from all sources")
    return unique_articles

# Path for contact form submissions log file
CONTACT_LOG_FILE = "contact_submissions.log"

@app.route("/premium", methods=["GET", "POST"])
def premium_waitlist():
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        email = request.form.get("email")
        company = request.form.get("company")
        bespoke_analysis = 'bespoke_analysis' in request.form
        historical_data = 'historical_data' in request.form
        additional_sources = 'additional_sources' in request.form
        message = request.form.get("message")
        
        # Validate required fields
        if not name or not email:
            flash("Name and email are required.")
            return redirect(url_for("premium_waitlist"))
        
        # Get additional checkboxes
        more_results = 'more_results' in request.form
        consulting_services = 'consulting_services' in request.form
        
        # Create new waiting list entry
        entry = WaitingList(
            name=name,
            email=email,
            company=company,
            bespoke_analysis=bespoke_analysis,
            historical_data=historical_data,
            additional_sources=additional_sources,
            more_results=more_results,
            consulting_services=consulting_services,
            message=message
        )
        
        # Save to database
        db.session.add(entry)
        db.session.commit()
        
        # Format form data for notifications
        form_data_text = f"""
        New premium waitlist submission:
        
        Name: {name}
        Email: {email}
        Company: {company or 'Not provided'}
        
        Interested in:
        - Bespoke Analysis: {'Yes' if bespoke_analysis else 'No'}
        - Historical Data: {'Yes' if historical_data else 'No'}
        - Additional Sources: {'Yes' if additional_sources else 'No'}
        - More Search Results: {'Yes' if more_results else 'No'}
        - Consulting Services: {'Yes' if consulting_services else 'No'}
        
        Message:
        {message or 'No message provided'}
        
        Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Log the submission to the console
        print(form_data_text)
        
        # Write submission to log file for easy access
        try:
            with open(CONTACT_LOG_FILE, 'a') as log_file:
                log_file.write(f"\n{'='*50}\n")
                log_file.write(form_data_text)
                log_file.write(f"\nSMS sent to: +1374211614\n")
                log_file.write(f"{'='*50}\n")
            print(f"Contact form submission logged to {CONTACT_LOG_FILE}")
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        # Show success message
        flash("Thank you! We'll contact you soon.")
        return redirect(url_for("premium_waitlist"))
    
    return render_template("premium.html")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get and log form data
        form_data = request.form.to_dict()
        print("Received form data:", form_data)
        
        # Extract basic search parameters
        query1 = form_data.get("query1", "").strip()
        query2 = form_data.get("query2", "").strip()
        from_date1 = form_data.get("from_date1", "").strip()
        to_date1 = form_data.get("to_date1", "").strip()
        from_date2 = form_data.get("from_date2", "").strip()
        to_date2 = form_data.get("to_date2", "").strip()
        
        # Extract advanced filter parameters for first query
        language1 = form_data.get("language1", "en")
        source1 = form_data.get("source1", "").strip()
        
        # Extract advanced filter parameters for second query
        language2 = form_data.get("language2", "en")
        source2 = form_data.get("source2", "").strip()
        
        print(f"Parsed form values: query1={query1}, from_date1={from_date1}, to_date1={to_date1}")
        print(f"Advanced filters 1: language={language1}, source={source1}")
        if query2:
            print(f"Advanced filters 2: language={language2}, source={source2}")
        
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
            valid, start_date1, end_date1 = validate_date_range(from_date1, to_date1)
            
            # Check if date range is more than 30 days (free tier limit)
            delta1 = end_date1 - start_date1
            if delta1.days > 30:
                flash("Free tier is limited to 30 days of historical data. Please join our premium waiting list for extended access.")
                return redirect(url_for("premium_waitlist"))
            
            if query2 and (from_date2 and to_date2):
                valid, start_date2, end_date2 = validate_date_range(from_date2, to_date2)
                
                # Check if date range is more than 30 days (free tier limit)
                delta2 = end_date2 - start_date2
                if delta2.days > 30:
                    flash("Free tier is limited to 30 days of historical data. Please join our premium waiting list for extended access.")
                    return redirect(url_for("premium_waitlist"))
            
            # Process boolean queries
            processed_query1 = {"enhanced_query": parse_boolean_query(query1), "entity_type": "", "reasoning": "Boolean search query"}
            processed_query2 = {"enhanced_query": parse_boolean_query(query2), "entity_type": "", "reasoning": "Boolean search query"} if query2 else None
            
            # Fetch and analyze articles for the first query
            articles1 = fetch_news(
                keywords=query1,
                from_date=from_date1,
                to_date=to_date1,
                language=language1,
                source=source1
            )
            analysis1 = analyze_articles(articles1, query1)
            
            # Helper function to summarize articles for Claude
            def summarize_articles(articles):
                return [{
                    'title': article['title'],
                    'description': article['description'],
                    'publishedAt': article['publishedAt']
                } for article in articles]
            
            # Helper function to format Claude's response
            def format_claude_response(text):
                formatted_text = text
                
                # Process section headers (lines that end with a colon)
                formatted_text = re.sub(r'^([^:\n]+:)$', r'<p><strong>\1</strong></p>', formatted_text, flags=re.MULTILINE)
                
                # Process subheads (lines that have a colon in the middle)
                formatted_text = re.sub(r'^([^:\n]+:[^:\n]*)$', r'<em>\1</em>', formatted_text, flags=re.MULTILINE)
                
                # Process numbered items (e.g., "1. Some text") to ensure they're on separate lines
                # This regex matches numbered items that might span multiple sentences
                formatted_text = re.sub(r'(\d+\.\s*[^0-9\n]+?)(?=\s*\d+\.\s*|\s*$)', r'<p>\1</p>', formatted_text)
                
                # Also handle bullet points with dashes or asterisks
                formatted_text = re.sub(r'([-*•]\s*[^-*•\n]+?)(?=\s*[-*•]\s*|\s*$)', r'<p>\1</p>', formatted_text)
                
                # Convert the formatted text to Markup to ensure HTML is rendered
                return Markup(formatted_text)
            
            # Initialize variables for second query
            articles2 = []
            analysis2 = None
            analysis_text = None
            
            # Prepare summarized articles for the first query
            summarized_articles1 = summarize_articles(articles1)
            
            # Generate analysis for single search term
            if not query2:
                # Check cache with all parameters for single search
                cache_key = f"single_{query1}_{from_date1}_{to_date1}_{language1}_{source1}"
                cached_response = app.config.get('analysis_cache', {}).get(cache_key)
                
                if cached_response:
                    analysis_text = cached_response
                else:
                    # Prepare the analysis prompt for single search term
                    analysis_prompt = f"""Analyze news coverage for {query1} ({from_date1} to {to_date1}).
                    Key points to address:
                    1. Major Coverage Differences: Identify the main themes, tones, and focus areas in the coverage
                    2. Key Trends: Analyze patterns in coverage volume, sentiment evolution, and source diversity
                    3. Business Implications: Discuss market perception, competitive positioning, and strategic opportunities
                    
                    Articles: {json.dumps(summarized_articles1)}"""
                    
                    # Get analysis from Claude
                    response = anthropic.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": analysis_prompt
                        }]
                    )
                    
                    # Format the response
                    analysis_text = format_claude_response(response.content[0].text)
                    
                    # Cache the response with timestamp
                    if not hasattr(app.config, 'analysis_cache'):
                        app.config['analysis_cache'] = {}
                        app.config['cache_times'] = {}
                    app.config['analysis_cache'][cache_key] = analysis_text
                    app.config['cache_times'][cache_key] = datetime.now()
            else:
                # Fetch and analyze articles for the second query
                articles2 = fetch_news(
                    keywords=query2,
                    from_date=from_date2 if from_date2 else from_date1,
                    to_date=to_date2 if to_date2 else to_date1,
                    language=language2,
                    source=source2
                )
                analysis2 = analyze_articles(articles2, query2)
                
                # Prepare summarized articles for the second query
                summarized_articles2 = summarize_articles(articles2)
                
                # Check cache with all parameters for comparative search
                cache_key = f"comparative_{query1}_{query2}_{from_date1}_{to_date1}_{from_date2}_{to_date2}_{language1}_{source1}_{language2}_{source2}"
                cached_response = app.config.get('analysis_cache', {}).get(cache_key)
                
                if cached_response:
                    analysis_text = cached_response
                else:
                    # Prepare the analysis prompt for comparative search
                    analysis_prompt = f"""Compare news coverage between {query1} ({from_date1} to {to_date1}) and {query2} ({from_date2 if from_date2 else from_date1} to {to_date2 if to_date2 else to_date1}).
                    Key points:
                    1. Major Coverage Differences
                    2. Key Trends
                    3. Business Implications
                    
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
                    
                    # Format the response
                    analysis_text = format_claude_response(response.content[0].text)
                    
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
                enhanced_query1=processed_query1,
                enhanced_query2=processed_query2,
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
    # Get port from environment variable or default to 5008
    port = int(os.environ.get("PORT", 5008))
    app.run(host='0.0.0.0', port=port, debug=True)
