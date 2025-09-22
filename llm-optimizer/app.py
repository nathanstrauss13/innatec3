import os
import requests
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from anthropic import Anthropic
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key_here")

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class LLMOptimizer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_url_content(self, url):
        """Fetch and parse content from a URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract key elements
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_desc_text = meta_desc.get('content', '') if meta_desc else ""
            
            # Extract headings
            headings = {}
            for i in range(1, 7):
                h_tags = soup.find_all(f'h{i}')
                headings[f'h{i}'] = [h.get_text().strip() for h in h_tags]
            
            # Extract main content (remove script, style, nav, footer)
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
            content_text = main_content.get_text() if main_content else soup.get_text()
            
            # Clean up text
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') or href.startswith('/'):
                    links.append({
                        'url': urljoin(url, href),
                        'text': link.get_text().strip()
                    })
            
            # Extract images
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '')
                if src:
                    images.append({
                        'src': urljoin(url, src),
                        'alt': alt
                    })
            
            return {
                'url': url,
                'title': title_text,
                'meta_description': meta_desc_text,
                'headings': headings,
                'content': content_text,
                'word_count': len(content_text.split()),
                'links': links[:20],  # Limit to first 20 links
                'images': images[:10],  # Limit to first 10 images
                'html': response.text
            }
            
        except Exception as e:
            raise Exception(f"Error fetching URL: {str(e)}")
    
    def analyze_technical_structure(self, content_data):
        """Analyze technical aspects of the webpage."""
        soup = BeautifulSoup(content_data['html'], 'html.parser')
        
        # Check for structured data
        structured_data = []
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except:
                pass
        
        # Check semantic HTML usage
        semantic_tags = ['article', 'section', 'nav', 'header', 'footer', 'aside', 'main']
        semantic_usage = {}
        for tag in semantic_tags:
            elements = soup.find_all(tag)
            semantic_usage[tag] = len(elements)
        
        # Check heading hierarchy
        heading_structure = []
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            if h_tags:
                heading_structure.append({
                    'level': i,
                    'count': len(h_tags),
                    'examples': [h.get_text().strip()[:100] for h in h_tags[:3]]
                })
        
        # Check meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                meta_tags[name] = content
        
        return {
            'structured_data': structured_data,
            'semantic_usage': semantic_usage,
            'heading_structure': heading_structure,
            'meta_tags': meta_tags,
            'has_title': bool(content_data['title']),
            'has_meta_description': bool(content_data['meta_description']),
            'title_length': len(content_data['title']),
            'meta_description_length': len(content_data['meta_description'])
        }
    
    def generate_recommendations(self, content_data, technical_analysis):
        """Generate LLM training optimization recommendations using Claude."""
        
        analysis_prompt = f"""Analyze this webpage content for optimizing it for LLM training data. Provide specific, actionable recommendations in the following categories:

TECHNICAL RECOMMENDATIONS:
- HTML structure and semantic markup improvements
- Metadata optimization (title, description, structured data)
- Content organization and hierarchy
- Accessibility improvements that aid machine parsing

CONTENT QUALITY RECOMMENDATIONS:
- Content clarity and comprehensiveness
- Information density and factual accuracy
- Language and writing style improvements
- Knowledge preservation and context enhancement

DISCOVERABILITY RECOMMENDATIONS:
- SEO improvements for better indexing
- Internal linking strategies
- Content categorization and tagging
- Cross-referencing and citation improvements

URL: {content_data['url']}
Title: {content_data['title']}
Meta Description: {content_data['meta_description']}
Word Count: {content_data['word_count']}

Content Sample (first 2000 characters):
{content_data['content'][:2000]}

Technical Analysis:
- Has structured data: {len(technical_analysis['structured_data']) > 0}
- Semantic HTML usage: {technical_analysis['semantic_usage']}
- Heading structure: {[h['level'] for h in technical_analysis['heading_structure']]}
- Meta tags present: {len(technical_analysis['meta_tags'])}

Please provide specific, actionable recommendations organized by category. Focus on changes that would make this content more valuable for training language models while maintaining human readability."""

        try:
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": analysis_prompt
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"

# Initialize optimizer
optimizer = LLMOptimizer()

@app.route("/")
def index():
    """Main page with URL input form."""
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_url():
    """Analyze a URL and return recommendations."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.netloc:
            return jsonify({"error": "Invalid URL format"}), 400
        
        # Fetch and analyze content
        content_data = optimizer.fetch_url_content(url)
        technical_analysis = optimizer.analyze_technical_structure(content_data)
        recommendations = optimizer.generate_recommendations(content_data, technical_analysis)
        
        return jsonify({
            "success": True,
            "url": url,
            "content_data": content_data,
            "technical_analysis": technical_analysis,
            "recommendations": recommendations,
            "analyzed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5011))
    print(f"Starting Flask app on port {port}")
    print(f"Access the app at: http://localhost:{port}")
    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False)