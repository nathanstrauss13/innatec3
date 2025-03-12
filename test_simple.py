import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
MEDIASTACK_API_KEY = os.environ.get("MEDIASTACK_API_KEY")

# Write to a file
with open("test_output.txt", "w") as f:
    f.write(f"MEDIASTACK_API_KEY is {'set' if MEDIASTACK_API_KEY else 'NOT SET'}\n")
    f.write(f"MEDIASTACK_API_KEY value: {MEDIASTACK_API_KEY}\n")
    
    # Test Media Stack API
    url = "http://api.mediastack.com/v1/news"
    params = {
        "access_key": MEDIASTACK_API_KEY,
        "keywords": "technology",
        "languages": "en",
        "limit": 10
    }
    
    try:
        f.write(f"Fetching news from MediaStack API with params: {params}\n")
        response = requests.get(url, params=params)
        f.write(f"MediaStack API response status: {response.status_code}\n")
        
        if response.status_code == 200:
            response_data = response.json()
            f.write(f"MediaStack API response data: {response_data.get('pagination')}\n")
            
            # Print articles
            articles = response_data.get("data", [])
            f.write(f"Retrieved {len(articles)} articles from MediaStack API\n")
            
            # Print first article
            if articles:
                f.write("\nFirst article:\n")
                f.write(f"Title: {articles[0].get('title')}\n")
                f.write(f"Source: {articles[0].get('source')}\n")
                f.write(f"URL: {articles[0].get('url')}\n")
                f.write(f"Published at: {articles[0].get('published_at')}\n")
        else:
            response_text = response.text
            f.write(f"MediaStack API Error response: {response_text}\n")
            try:
                response_data = response.json()
                f.write(f"Error from MediaStack API: {response_data.get('error', {}).get('message', 'Unknown error')}\n")
            except:
                f.write(f"Could not parse MediaStack API error response as JSON: {response_text}\n")
    except Exception as e:
        f.write(f"Error fetching articles from MediaStack API: {e}\n")

print("Test completed. Check test_output.txt for results.")
