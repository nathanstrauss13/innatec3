#!/usr/bin/env python3
"""
Simple Raw Auditor - For Testing and Iteration
Minimal flow: Brand → AI infers competitors + generates prompts → User edits → Run audit → Show raw CSV data
"""

import os
import json
import csv
import logging
import requests
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _extract_urls(text: str) -> List[str]:
    """Extract URLs/domains from model text"""
    try:
        pattern = r'https?://[^\s\]\)<>"]+|www\.[^\s\]\)<>"]+'
        urls = re.findall(pattern, text or '')
        return list(set(urls))
    except Exception:
        return []

def fix_location_query(query: str, brand: str) -> str:
    """Fix location-based queries by replacing 'around me' or 'nearby' with city/state context
    
    For brands like Portland Center Stage, infer the location from the brand name.
    """
    query_lower = query.lower()
    
    # Check if query contains location-relative terms
    location_terms = ['around me', 'near me', 'nearby', 'in my area', 'local']
    needs_location_fix = any(term in query_lower for term in location_terms)
    
    if not needs_location_fix:
        return query
    
    # Try to infer location from brand name
    location = None
    brand_lower = brand.lower()
    
    # Common city names in brand names
    city_patterns = {
        'portland': 'Portland, Oregon',
        'seattle': 'Seattle, Washington',
        'boston': 'Boston, Massachusetts',
        'chicago': 'Chicago, Illinois',
        'denver': 'Denver, Colorado',
        'austin': 'Austin, Texas',
        'nashville': 'Nashville, Tennessee',
        'atlanta': 'Atlanta, Georgia',
        'miami': 'Miami, Florida',
        'phoenix': 'Phoenix, Arizona',
        'san francisco': 'San Francisco, California',
        'los angeles': 'Los Angeles, California',
        'new york': 'New York City',
        'philadelphia': 'Philadelphia, Pennsylvania',
        'houston': 'Houston, Texas',
        'dallas': 'Dallas, Texas'
    }
    
    for city, full_location in city_patterns.items():
        if city in brand_lower:
            location = full_location
            break
    
    # If no location found in brand, use a generic major city
    if not location:
        location = "major US cities"
    
    # Replace location-relative terms
    fixed_query = query
    for term in location_terms:
        if term in query_lower:
            # Replace with the inferred location
            fixed_query = re.sub(r'\b' + term + r'\b', f'in {location}', fixed_query, flags=re.IGNORECASE)
    
    return fixed_query



def infer_competitors(brand: str, openai_key: str) -> Dict[str, Any]:
    """Use OpenAI to infer competitors only"""
    if not openai_key:
        return {'competitors': [], 'industry': 'Unknown'}
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": f"""Analyze the brand "{brand}" and provide:
1. Top 3 direct competitors
2. Industry category

Respond in JSON format:
{{
  "competitors": ["Competitor 1", "Competitor 2", "Competitor 3"],
  "industry": "Industry Name"
}}"""
                }],
                "max_tokens": 300,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return result
        
    except Exception as e:
        logger.error(f"Error inferring competitors: {e}")
    
    return {'competitors': [], 'industry': 'Unknown'}


def generate_queries(brand: str, general_query: str, competitors: List[str], openai_key: str) -> List[str]:
    """Generate 5 intelligent queries based on brand, general query, and competitors
    
    CRITICAL: Only include brand name in queries if the user's original query is branded.
    Otherwise, generate unbiased queries to see which brands AI platforms naturally recommend.
    """
    
    # Fix location-based queries - replace "around me" or "nearby" with city/state context
    general_query = fix_location_query(general_query, brand)
    
    # Check if user's query is branded (mentions the brand name)
    is_branded_query = brand.lower() in general_query.lower()
    
    if not openai_key:
        # Fallback
        if is_branded_query:
            # User asked about the brand - generate branded variations
            return [
                general_query,
                f"Tell me about {brand}",
                f"What makes {brand} different?",
                f"Is {brand} a good choice?",
                f"Where can I find {brand}?"
            ]
        else:
            # User's query is generic - keep it unbiased
            return [
                general_query,
                general_query.replace('?', ' in 2025?'),
                f"Top recommendations for {general_query.replace('What are the best ', '').replace('?', '')}",
                f"Most recommended {general_query.replace('What are the best ', '').replace('?', '')}",
                f"Where to buy {general_query.replace('What are the best ', '').replace('?', '')}"
            ]
    
    try:
        comp_context = f"Competitors: {', '.join(competitors)}" if competitors else "No competitors specified"
        
        if is_branded_query:
            # Branded query - generate variations that mention the brand
            prompt_instructions = f"""CONTEXT: The user is a marketing/PR professional for "{brand}" testing AI visibility.

The user's query is BRANDED (mentions "{brand}").

Generate 5 queries that include the brand name, focusing on RECOMMENDATION-SEEKING formats:
1. The user's original query: "{general_query}"
2-5. Variations that ask for recommendations, suggestions, or "where to" find {brand}

PREFERRED FORMATS:
- "Where should I [action] for [category]?" → leads to brand recommendations
- "What are the best [category] options?" → leads to brand recommendations  
- "Where can I find [specific product/service]?" → leads to brand recommendations

AVOID FORMATS:
- "What criteria..." (too analytical)
- "How can I identify..." (too educational)
- "How does one evaluate..." (too academic)

Goal: Test if AI platforms recommend {brand} when users seek purchasing guidance."""
        else:
            # Unbiased query - do NOT mention the brand
            prompt_instructions = f"""CONTEXT: The user is a marketing/PR professional for "{brand}" testing AI visibility.

The user's query is UNBIASED (does not mention any specific brand).

CRITICAL: Do NOT insert "{brand}" or any competitor names into the generated queries.

Generate 5 GENERIC/UNBIASED queries using RECOMMENDATION-SEEKING formats:
1. The user's original query: "{general_query}"
2-5. Generic variations that consumers would ask when SEEKING RECOMMENDATIONS

PREFERRED FORMATS (no brand names):
- "Where should I shop for [category]?"
- "What are the best [category] brands?"
- "Where can I find quality [product/service]?"
- "Who makes the best [product]?"
- "What's the top choice for [need]?"

AVOID FORMATS:
- "What criteria define [category]?" (too analytical)
- "How can I identify [attribute]?" (too educational)
- "How does one evaluate [category]?" (too academic)

Goal: See which brands AI platforms naturally recommend when consumers seek buying advice.
We'll track if "{brand}" appears in recommendations without being prompted."""
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": f"""{prompt_instructions}

Brand we're tracking: {brand}
{comp_context}

Respond as a JSON array of exactly 5 queries:
["Query 1", "Query 2", "Query 3", "Query 4", "Query 5"]"""
                }],
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            queries = json.loads(content)
            return queries[:5]  # Ensure exactly 5
        
    except Exception as e:
        logger.error(f"Error generating queries: {e}")
    
    # Fallback
    if is_branded_query:
        return [
            general_query,
            f"Tell me about {brand}",
            f"What makes {brand} different?",
            f"Is {brand} worth it?",
            f"Reviews of {brand}"
        ]
    else:
        return [
            general_query,
            general_query.replace('?', ' in 2025?'),
            f"Top options for {general_query.replace('What are the best ', '').replace('?', '')}",
            f"Most recommended {general_query.replace('What are the best ', '').replace('?', '')}",
            f"Expert recommendations for {general_query.replace('What are the best ', '').replace('?', '')}"
        ]


class SimpleRawAuditor:
    """Simplified auditor that returns raw data"""
    
    def __init__(self, brand: str, competitors: List[str], prompts: List[str]):
        self.brand = brand
        self.competitors = competitors
        self.prompts = prompts
        self.results = []
    
    def run_audit(self) -> List[Dict[str, Any]]:
        """Run audit across all platforms for all prompts"""
        platforms = ['ChatGPT', 'Claude', 'Perplexity', 'Gemini']
        
        logger.info(f"Starting audit for {self.brand}")
        logger.info(f"Testing {len(self.prompts)} queries across {len(platforms)} platforms")
        
        total = len(self.prompts) * len(platforms)
        completed = 0
        
        for prompt in self.prompts:
            for platform in platforms:
                completed += 1
                logger.info(f"[{completed}/{total}] {platform}: {prompt[:50]}...")
                
                # Retry logic for timeouts and connection errors
                max_retries = 3
                retry_delay = 2
                result = None
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        result = self._query_platform(platform, prompt)
                        
                        if result:
                            analysis = self._analyze_response(result, prompt, platform)
                            self.results.append(analysis)
                            break  # Success, exit retry loop
                        else:
                            # No result but no exception - likely API key missing
                            if attempt == max_retries - 1:
                                self.results.append({
                                    'query': prompt,
                                    'platform': platform,
                                    'brand_mentioned': False,
                                    'competitors_mentioned': [],
                                    'actual_citations': [],
                                    'inferred_citations': [],
                                    'full_response': 'ERROR: No response (API key missing?)',
                                    'response_snippet': 'ERROR: No response (API key missing?)'
                                })
                            break  # Don't retry if no API key
                        
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Timeout/connection error on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Failed after {max_retries} attempts: {e}")
                            self.results.append({
                                'query': prompt,
                                'platform': platform,
                                'brand_mentioned': False,
                                'competitors_mentioned': [],
                                'actual_citations': [],
                                'inferred_citations': [],
                                'full_response': f'ERROR: Failed after {max_retries} retries: {str(e)}',
                                'response_snippet': f'ERROR: Failed after {max_retries} retries: {str(e)}'
                            })
                    
                    except Exception as e:
                        # Other errors - don't retry
                        logger.error(f"Error querying {platform}: {e}")
                        self.results.append({
                            'query': prompt,
                            'platform': platform,
                            'brand_mentioned': False,
                            'competitors_mentioned': [],
                            'actual_citations': [],
                            'inferred_citations': [],
                            'full_response': f'ERROR: {str(e)}',
                            'response_snippet': f'ERROR: {str(e)}'
                        })
                        break  # Don't retry non-timeout errors
                
                # Rate limiting (only if we got a result)
                if result:
                    time.sleep(random.uniform(1, 2))
        
        logger.info(f"Audit complete. Collected {len(self.results)} results.")
        return self.results
    
    def _query_platform(self, platform: str, query: str) -> Dict:
        """Query specific platform"""
        if platform == 'ChatGPT':
            return self._query_chatgpt(query)
        elif platform == 'Claude':
            return self._query_claude(query)
        elif platform == 'Perplexity':
            return self._query_perplexity(query)
        elif platform == 'Gemini':
            return self._query_gemini(query)
    
    def _query_chatgpt(self, query: str) -> Dict:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None
        
        enhanced_query = f"""{query}

Please cite at least 3 credible sources with full URLs.
End with a section titled "Recommended Resources:" listing websites users should visit."""
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that always cites credible sources with URLs and provides a 'Recommended Resources' section."},
                    {"role": "user", "content": enhanced_query}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            text = response.json()['choices'][0]['message']['content']
            urls = _extract_urls(text)
            return {'text': text, 'citations': urls}
        return None
    
    def _query_claude(self, query: str) -> Dict:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return None
        
        enhanced_query = f"""{query}

Please cite at least 3 credible sources with full URLs.
End with a section titled "Recommended Resources:" listing websites users should visit."""
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": enhanced_query}],
                "system": "You are a helpful assistant that always cites credible sources with URLs and provides a 'Recommended Resources' section."
            },
            timeout=30
        )
        
        if response.status_code == 200:
            text = ""
            for block in response.json().get('content', []):
                if block.get('type') == 'text':
                    text += block.get('text', '')
            urls = _extract_urls(text)
            return {'text': text, 'citations': urls}
        return None
    
    def _query_perplexity(self, query: str) -> Dict:
        api_key = os.getenv('PERPLEXITY_API_KEY') or os.getenv('PPLX_API_KEY')
        if not api_key:
            logger.warning("Perplexity skipped: PERPLEXITY_API_KEY not set")
            return None
        
        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [{"role": "user", "content": query}],
                    "max_tokens": 800,
                    "temperature": 0.1,
                    "return_citations": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Robust content parsing
                try:
                    text = data['choices'][0]['message']['content']
                except Exception:
                    text = json.dumps(data)[:2000]
                
                # Citations can be top-level or under choices[0]
                citations = []
                if isinstance(data.get('citations'), list):
                    citations = [c for c in data['citations'] if isinstance(c, str)]
                else:
                    try:
                        citations = data['choices'][0].get('citations') or []
                    except Exception:
                        citations = []
                
                # Fallback: scrape URLs from text if Perplexity omitted citations
                if not citations and isinstance(text, str):
                    import re
                    citations = re.findall(r"https?://[^\s\]\)]+", text)
                
                return {'text': text, 'citations': citations}
            else:
                status = response.status_code
                body_snip = response.text[:200]
                logger.error(f"Perplexity HTTP {status}: {body_snip}")
                # Fallback: some accounts do not have access to sonar-pro; try public 'sonar'
                if status in (401, 403):
                    try:
                        fallback_resp = requests.post(
                            "https://api.perplexity.ai/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                            },
                            json={
                                "model": "sonar",
                                "messages": [{"role": "user", "content": query}],
                                "max_tokens": 800,
                                "temperature": 0.2,
                                "return_citations": True
                            },
                            timeout=30
                        )
                        if fallback_resp.status_code == 200:
                            fd = fallback_resp.json()
                            try:
                                ftext = fd['choices'][0]['message']['content']
                            except Exception:
                                ftext = json.dumps(fd)[:2000]
                            fcites = []
                            if isinstance(fd.get('citations'), list):
                                fcites = [c for c in fd['citations'] if isinstance(c, str)]
                            else:
                                try:
                                    fcites = fd['choices'][0].get('citations') or []
                                except Exception:
                                    fcites = []
                            if not fcites and isinstance(ftext, str):
                                import re
                                fcites = re.findall(r"https?://[^\s\]\)]+", ftext)
                            logger.info("Perplexity fallback to 'sonar' succeeded")
                            return {'text': ftext, 'citations': fcites}
                        else:
                            logger.error(f"Perplexity fallback model 'sonar' HTTP {fallback_resp.status_code}: {fallback_resp.text[:200]}")
                    except Exception as fe:
                        logger.error(f"Perplexity fallback error: {fe}")
                return {'text': f"ERROR: Perplexity returned HTTP {status}", 'citations': []}
        except Exception as e:
            logger.error(f"Perplexity exception: {e}")
            return {'text': f"ERROR: Perplexity exception: {e}", 'citations': []}
    
    def _query_gemini(self, query: str) -> Dict:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return None
        
        enhanced_query = f"""{query}

Please cite at least 3 credible sources with full URLs.
End with a section titled "Recommended Resources:" listing websites users should visit."""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": enhanced_query}]}],
                "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7}
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                urls = _extract_urls(text)
                return {'text': text, 'citations': urls}
        return None
    
    def _analyze_response(self, result: Dict, query: str, platform: str) -> Dict:
        """Analyze response for brand/competitor mentions and citations"""
        text = result.get('text', '')
        citations = result.get('citations', [])  # Actual citations with URLs (from Perplexity)
        
        text_lower = text.lower()
        # Word-boundary entity detection to avoid false positives
        brand_mentioned = bool(re.search(r'\b' + re.escape(self.brand.lower()) + r'\b', text_lower))
        
        competitors_mentioned = []
        for comp in self.competitors:
            if re.search(r'\b' + re.escape(comp.lower()) + r'\b', text_lower):
                competitors_mentioned.append(comp)
        
        # Extract inferred citations (e.g., "According to Forbes...", "ESPN reports...")
        inferred_citations = self._extract_inferred_citations(text)
        
        # Extract recommended resources (e.g., "Visit Cars.com", "Check Edmunds...")
        recommended_resources = self._extract_recommended_resources(text)
        
        return {
            'query': query,
            'platform': platform,
            'brand_mentioned': brand_mentioned,
            'competitors_mentioned': competitors_mentioned,
            'actual_citations': citations,  # URLs from platform (Perplexity)
            'inferred_citations': inferred_citations,  # "According to X" mentions
            'recommended_resources': recommended_resources,  # "Visit X", "Check Y" suggestions
            'full_response': text,
            'response_snippet': text[:200] + '...' if len(text) > 200 else text
        }
    
    def _extract_inferred_citations(self, text: str) -> List[str]:
        """Extract inferred citations from text (e.g., 'According to Forbes...')"""
        import re
        
        inferred = []
        
        # Common citation patterns
        patterns = [
            r'[Aa]ccording to ([^,\.]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) reports',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) states',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) notes',
            r'[Aa]s reported by ([^,\.]+)',
            r'[Aa]s stated by ([^,\.]+)',
            r'[Ss]ource: ([^,\.]+)',
            r'[Cc]iting ([^,\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                source = match.strip()
                # Clean up common artifacts
                source = source.replace(' the', '').replace(' a', '').strip()
                if source and len(source) < 50:  # Reasonable source name length
                    inferred.append(source)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_inferred = []
        for source in inferred:
            source_lower = source.lower()
            if source_lower not in seen:
                seen.add(source_lower)
                unique_inferred.append(source)
        
        return unique_inferred
    
    def _extract_recommended_resources(self, text: str) -> List[str]:
        """Extract recommended resources that AI tells users to visit
        
        Examples:
        - 'Visit Cars.com or AutoTrader'
        - 'Check Edmunds for reviews'
        - 'Edmunds provides detailed reviews'
        - 'Use car-buying websites like Cars.com'
        - 'Direct Link: https://ev-database.org/'
        """
        import re
        
        resources = []
        
        # Patterns for recommendations
        patterns = [
            # Direct recommendations: "Visit X", "Check X", "Use X"
            r'[Vv]isit ([A-Za-z0-9\-\.]+(?:\.com|\.org|\.net|\.edu|\.co\.uk))',
            r'[Cc]heck ([A-Za-z0-9\-\.]+(?:\.com|\.org|\.net|\.edu|\.co\.uk))',
            r'[Uu]se ([A-Za-z0-9\-\.]+(?:\.com|\.org|\.net|\.edu|\.co\.uk))',
            r'[Gg]o to ([A-Za-z0-9\-\.]+(?:\.com|\.org|\.net|\.edu|\.co\.uk))',
            
            # Resource mentions with context: "Edmunds provides", "Cars.com offers"
            r'([A-Z][a-zA-Z0-9\-\.]+(?:\.com|\.org|\.net)) (?:provides|offers|has|features|includes)',
            r'([A-Z][a-zA-Z0-9\-]+) \((?:[^)]*(?:\.com|\.org|\.net)[^)]*)\)',
            
            # "Like X, Y, Z" patterns
            r'(?:like|such as|including) ([A-Z][a-zA-Z0-9\-\.]+\.(?:com|org|net))',
            r'(?:like|such as|including) ([A-Z][a-zA-Z][a-zA-Z0-9 ]*)',
            
            # Direct mentions in lists: "1. Cars.com", "- Edmunds"
            r'(?:^|\n)\s*[\d\*\-•]\s*([A-Z][a-zA-Z0-9\-\.]+\.(?:com|org|net))',
            r'(?:^|\n)\s*[\d\*\-•]\s*\*?\*?([A-Z][a-zA-Z][a-zA-Z ]+(?:\.com|\.org|\.net)?)\*?\*?:',
            
            # Explicit links
            r'(?:Direct Link|URL|Website):\s*(?:https?://)?([A-Za-z0-9\-\.]+(?:\.com|\.org|\.net|\.edu))',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                resource = match.strip().rstrip(':').rstrip(')')
                
                # Clean up
                resource = resource.replace('**', '').replace('*', '').strip()
                
                # Skip if too short or contains common words that aren't resources
                if len(resource) < 3:
                    continue
                    
                # Skip common false positives
                skip_terms = ['you can', 'they are', 'this is', 'there are', 'it is', 'that is', 
                             'these are', 'some of', 'one of', 'all of', 'many of']
                if any(skip in resource.lower() for skip in skip_terms):
                    continue
                
                # Add if reasonable length and looks like a resource
                if len(resource) < 100 and (
                    '.' in resource or  # Has domain extension
                    resource[0].isupper()  # Starts with capital (brand name)
                ):
                    resources.append(resource)
        
        # Also extract from explicit recommendation sections
        # Look for sections like "Where to find:" or "Resources:"
        section_patterns = [
            r'(?:Where to find|Resources|Recommended sites|Useful websites):([^\n]+(?:\n[^\n]+){0,10})',
            r'You can (?:visit|check|use):([^\n]+(?:\n[^\n]+){0,5})',
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for section in matches:
                # Extract resource names from the section
                for line in section.split('\n'):
                    # Look for capitalized names or domains
                    resource_matches = re.findall(r'([A-Z][a-zA-Z0-9\-\.]+(?:\.(?:com|org|net|edu))?)', line)
                    for res in resource_matches:
                        if len(res) > 3 and len(res) < 100:
                            resources.append(res)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_resources = []
        for resource in resources:
            resource_lower = resource.lower().replace('www.', '')
            if resource_lower not in seen:
                seen.add(resource_lower)
                unique_resources.append(resource)
        
        return unique_resources
    
    def to_csv(self, filepath: str):
        """Save results to CSV with full response and all citation types"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'query',
                'platform', 
                'brand_mentioned',
                'competitors_mentioned',
                'actual_citations',  # URLs from platform (Perplexity)
                'inferred_citations',  # "According to X" mentions
                'recommended_resources',  # "Visit X", "Check Y" suggestions
                'full_response'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                # Handle both old format (for errors) and new format
                actual_cites = result.get('actual_citations', result.get('citations', []))
                inferred_cites = result.get('inferred_citations', [])
                recommended_res = result.get('recommended_resources', [])
                full_resp = result.get('full_response', result.get('response_snippet', ''))
                
                writer.writerow({
                    'query': result['query'],
                    'platform': result['platform'],
                    'brand_mentioned': 'Yes' if result.get('brand_mentioned', False) else 'No',
                    'competitors_mentioned': ', '.join(result.get('competitors_mentioned', [])) if result.get('competitors_mentioned') else 'None',
                    'actual_citations': ' | '.join(actual_cites) if actual_cites else 'None',
                    'inferred_citations': ' | '.join(inferred_cites) if inferred_cites else 'None',
                    'recommended_resources': ' | '.join(recommended_res) if recommended_res else 'None',
                    'full_response': full_resp
                })
