#!/usr/bin/env python3
"""
Simple LLM Training Optimizer - Basic version for testing
"""
import os
from flask import Flask, render_template_string, request, jsonify
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "test_key")

# Simple HTML template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LLM Training Optimizer - Simple Version</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #4f46e5; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        input[type="url"] { width: 70%; padding: 10px; border: 1px solid #ddd; }
        button { background: #4f46e5; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .results { background: #f9f9f9; padding: 20px; margin-top: 20px; }
        .loading { display: none; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>LLM Training Optimizer</h1>
        <p>Simple URL Analysis Tool</p>
    </div>

    <form id="analyzeForm">
        <div class="form-group">
            <label>Enter URL to analyze:</label><br>
            <input type="url" id="url" placeholder="https://example.com" required>
            <button type="submit">Analyze</button>
        </div>
    </form>

    <div class="loading" id="loading">Analyzing URL...</div>
    <div id="results"></div>

    <script>
        document.getElementById('analyzeForm').onsubmit = async function(e) {
            e.preventDefault();
            const url = document.getElementById('url').value;
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            loading.style.display = 'block';
            results.innerHTML = '';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await response.json();
                loading.style.display = 'none';
                
                if (data.error) {
                    results.innerHTML = '<div style="color: red;">Error: ' + data.error + '</div>';
                } else {
                    results.innerHTML = '<div class="results"><h2>Analysis Results</h2>' +
                        '<p><strong>Title:</strong> ' + (data.title || 'No title found') + '</p>' +
                        '<p><strong>Word Count:</strong> ' + data.word_count + '</p>' +
                        '<p><strong>Analysis:</strong></p><div>' + data.analysis + '</div></div>';
                }
            } catch (error) {
                loading.style.display = 'none';
                results.innerHTML = '<div style="color: red;">Error: ' + error.message + '</div>';
            }
        };
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch the webpage
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; LLM-Optimizer/1.0)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic info
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        # Get text content
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        word_count = len(text.split())
        
        # Simple analysis
        analysis = f"""
        <strong>Basic Technical Analysis:</strong><br>
        • Title: {title_text}<br>
        • Word Count: {word_count:,} words<br>
        • Has meta description: {'Yes' if soup.find('meta', attrs={'name': 'description'}) else 'No'}<br>
        • Number of headings: {len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))}<br>
        • Number of images: {len(soup.find_all('img'))}<br>
        • Number of links: {len(soup.find_all('a', href=True))}<br><br>
        
        <strong>Quick LLM Training Recommendations:</strong><br>
        • Ensure clear heading hierarchy (H1 → H2 → H3)<br>
        • Add structured data (JSON-LD) for better machine understanding<br>
        • Include comprehensive meta descriptions<br>
        • Use semantic HTML5 elements (article, section, nav)<br>
        • Ensure content is well-organized and factual<br>
        • Add alt text to all images<br>
        • Use descriptive link text instead of "click here"
        """
        
        return jsonify({
            "title": title_text,
            "word_count": word_count,
            "analysis": analysis,
            "url": url
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    print("🚀 Starting Simple LLM Training Optimizer...")
    print("📱 Access the app at: http://localhost:5012")
    print("🔍 Enter any URL to analyze for LLM training optimization")
    print("🛑 Press Ctrl+C to stop")
    
    app.run(host='127.0.0.1', port=5012, debug=False)