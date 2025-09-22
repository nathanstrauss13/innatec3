import os
import json
import re
import random
import requests
import html
from collections import Counter
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from markupsafe import Markup
from dotenv import load_dotenv
from anthropic import Anthropic
from dateutil.parser import parse
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from utils.file_processor import MediaFileProcessor

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key_here")

# File upload configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'pdf', 'pptx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize file processor
file_processor = MediaFileProcessor(os.environ.get("ANTHROPIC_API_KEY"))

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
    # Check if the cache exists in app.config using dictionary access
    if 'analysis_cache' in app.config:
        current_time = datetime.now()
        # Log the cache cleanup operation
        print(f"Cleaning up cache at {current_time}. Before cleanup: {len(app.config.get('cache_times', {}))} entries")
        
        # Update cache_times dictionary, removing entries older than 1 hour
        app.config['cache_times'] = {k: v for k, v in app.config.get('cache_times', {}).items()
                                   if (current_time - v).total_seconds() < 3600}
        
        # Update analysis_cache to only include entries that still exist in cache_times
        app.config['analysis_cache'] = {k: v for k, v in app.config['analysis_cache'].items()
                                      if k in app.config['cache_times']}
        
        print(f"After cleanup: {len(app.config['cache_times'])} entries remaining")

# Initialize APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Create scheduler with proper shutdown
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_cache, trigger="interval", hours=1)
scheduler.start()

# Register the scheduler shutdown function to be called when the application exits
@atexit.register
def shutdown_scheduler():
    print("Shutting down scheduler...")
    scheduler.shutdown()
    print("Scheduler shut down successfully")

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
    
    # News source distribution with HTML entity decoding
    sources = Counter()
    for article in articles:
        try:
            source_name = html.unescape(article['source']['name']) if article['source']['name'] else ""
            sources[source_name] += 1
        except Exception as e:
            print(f"Error decoding source name: {e}")
            source_name = article['source']['name'] if article['source']['name'] else ""
            sources[source_name] += 1
    
    top_sources = []
    for name, count in sources.most_common(10):
        try:
            decoded_name = html.unescape(name) if name else ""
            top_sources.append({'name': decoded_name, 'count': count})
        except Exception as e:
            print(f"Error decoding source name in most_common: {e}")
            top_sources.append({'name': name, 'count': count})
    
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
    Parse a boolean search query with enhanced support for:
    - Quoted phrases for exact matches (e.g., "artificial intelligence")
    - AND/OR operators with proper precedence (e.g., "AI" AND "machine learning" OR robotics)
    - Nested expressions with parentheses (e.g., AI AND (robotics OR "machine learning"))
    - Minus sign for exclusion (e.g., AI -"machine learning")
    
    Returns a processed query string compatible with the News API
    """
    # Default to the original query if it's empty
    if not query.strip():
        return query
    
    # Helper function to process quoted phrases
    def process_quotes(text):
        # Find all quoted phrases and replace spaces with underscores temporarily
        quoted_phrases = re.findall(r'"([^"]*)"', text)
        processed_text = text
        for phrase in quoted_phrases:
            if ' ' in phrase:  # Only process phrases with spaces
                processed_text = processed_text.replace(
                    f'"{phrase}"', 
                    f'"{phrase}"'  # Keep the quotes to ensure exact phrase matching
                )
        return processed_text
    
    # Helper function to process boolean operators
    def process_operators(text):
        # Standardize boolean operators to uppercase
        text = re.sub(r'\bAND\b|\band\b', 'AND', text)
        text = re.sub(r'\bOR\b|\bor\b', 'OR', text)
        
        # Handle implicit AND operations (space-separated terms)
        # But only if they're not already part of a quoted phrase
        parts = []
        current_pos = 0
        in_quotes = False
        current_term = ''
        
        for i, char in enumerate(text):
            if char == '"':
                in_quotes = not in_quotes
                current_term += char
            elif char == ' ' and not in_quotes:
                if current_term:
                    parts.append(current_term.strip())
                current_term = ''
            else:
                current_term += char
        
        if current_term:
            parts.append(current_term.strip())
        
        # Join terms with explicit AND if not already joined by OR
        processed_text = ''
        for i, part in enumerate(parts):
            if i > 0:
                if 'OR' not in parts[i-1] and 'OR' not in part:
                    processed_text += ' AND '
                else:
                    processed_text += ' '
            processed_text += part
        
        return processed_text
    
    # Process the query
    processed_query = query.strip()
    
    # Handle quoted phrases first
    processed_query = process_quotes(processed_query)
    
    # Handle boolean operators if not already in proper format
    if not (re.search(r'\bAND\b|\bOR\b', processed_query, re.IGNORECASE) and '"' in processed_query):
        processed_query = process_operators(processed_query)
    
    print(f"Boolean search query: Original='{query}' → Processed='{processed_query}'")
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
    
    # Only use actual API results, no mock data
    if news_api_success:
        all_articles.extend(news_api_articles)
    else:
        print("News API request failed")
        return []  # Return empty list if API request failed
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    print(f"Returning {len(unique_articles)} unique articles from News API")
    return unique_articles

# Path for contact form submissions log file
CONTACT_LOG_FILE = "contact_submissions.log"

# File upload utility functions
def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_uploaded_files():
    """Clean up old uploaded files to save disk space."""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            current_time = datetime.now()
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                if os.path.isfile(file_path):
                    # Delete files older than 1 hour
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_time).total_seconds() > 3600:
                        os.remove(file_path)
                        print(f"Deleted old uploaded file: {filename}")
    except Exception as e:
        print(f"Error cleaning up uploaded files: {e}")

# File upload routes
@app.route("/upload", methods=["GET", "POST"])
def upload_files():
    """Handle file uploads and process media coverage data."""
    if request.method == "POST":
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('No files selected')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        if not files or all(file.filename == '' for file in files):
            flash('No files selected')
            return redirect(request.url)
        
        # Process uploaded files
        all_articles = []
        processed_files = []
        
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    # Secure the filename
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{timestamp}_{filename}"
                    
                    # Save the file
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    # Process the file
                    articles = file_processor.process_file(file_path, file.filename)
                    
                    if articles:
                        all_articles.extend(articles)
                        processed_files.append({
                            'filename': file.filename,
                            'articles_count': len(articles)
                        })
                        print(f"Processed {file.filename}: {len(articles)} articles extracted")
                    else:
                        flash(f"No data could be extracted from {file.filename}")
                    
                    # Clean up the uploaded file
                    try:
                        os.remove(file_path)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"Error processing file {file.filename}: {str(e)}")
                    flash(f"Error processing {file.filename}: {str(e)}")
            else:
                flash(f"File type not allowed: {file.filename}")
        
        if not all_articles:
            flash("No articles could be extracted from the uploaded files")
            return redirect(request.url)
        
        # Analyze the extracted articles
        try:
            # Use a generic query for file-based analysis
            query = "Local File Analysis"
            analysis = analyze_articles(all_articles, query)
            
            # Generate analysis text
            def summarize_articles(articles):
                return [{
                    'title': article['title'],
                    'description': article['description'],
                    'publishedAt': article['publishedAt']
                } for article in articles]
            
            summarized_articles = summarize_articles(all_articles)
            
            # Get analysis from Claude
            analysis_prompt = f"""Analyze this media coverage data extracted from uploaded files.

IMPORTANT: Format your response carefully with these guidelines:
- Use clear section headers for each main point
- Format numbered lists consistently
- Use paragraph breaks between sections

Key points to address:
1. Major Coverage Themes: Identify the main themes, tones, and focus areas in the coverage
2. Key Trends: Analyze patterns in coverage volume, sentiment evolution, and source diversity
3. Business Implications: Discuss market perception, competitive positioning, and strategic opportunities

Articles: {json.dumps(summarized_articles[:50])}"""  # Limit to first 50 articles to avoid token limits
            
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": analysis_prompt
                }]
            )
            
            # Format the response
            def format_claude_response(text):
                formatted_text = re.sub(r'^([^:\n]+:)
, r'<p><strong>\1</strong></p>', text, flags=re.MULTILINE)
                formatted_text = re.sub(r'^([^:\n]+:[^:\n]*)
, r'<em>\1</em>', formatted_text, flags=re.MULTILINE)
                formatted_text = re.sub(r'(\d+\.\s*[^0-9\n]+?)(?=\s*\d+\.\s*|\s*$)', r'<p>\1</p>', formatted_text)
                formatted_text = re.sub(r'([-*•]\s*[^-*•\n]+?)(?=\s*[-*•]\s*|\s*$)', r'<p>\1</p>', formatted_text)
                return Markup(formatted_text)
            
            analysis_text = format_claude_response(response.content[0].text)
            
            # Create form data for template compatibility
            form_data = {
                'analysis_type': 'file_upload',
                'processed_files': processed_files
            }
            
            return render_template(
                "result.html",
                query1="File Upload Analysis",
                query2=None,
                enhanced_query1={"enhanced_query": "File Upload Analysis", "entity_type": "file_analysis", "reasoning": "Analysis of uploaded files"},
                enhanced_query2=None,
                textual_analysis=analysis_text,
                analysis1=analysis,
                analysis2=None,
                articles1=all_articles,
                articles2=[],
                request=type('obj', (object,), {'form': form_data})
            )
            
        except Exception as e:
            print(f"Error analyzing articles: {str(e)}")
            flash(f"Error analyzing data: {str(e)}")
            return redirect(request.url)
    
    return render_template("upload.html")

if __name__ == "__main__":
    # Get port from environment variable or default to 5009
    port = int(os.environ.get("PORT", 5009))
    app.run(host='0.0.0.0', port=port, debug=True)
