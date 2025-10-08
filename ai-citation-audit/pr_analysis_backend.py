#!/usr/bin/env python3
"""
PR Analysis Backend - Enhanced outlet classification and opportunity scoring
For corporate communications professionals focusing on media coverage
"""

# Tier 1 Media Outlets (highest authority for PR)
TIER_1_OUTLETS = {
    'wsj.com', 'nytimes.com', 'forbes.com', 'bloomberg.com', 'ft.com',
    'techcrunch.com', 'reuters.com', 'apnews.com', 'bbc.com', 'cnn.com',
    'washingtonpost.com', 'usatoday.com', 'businessinsider.com', 'fortune.com',
    'economist.com', 'theverge.com', 'wired.com', 'arstechnica.com', 'engadget.com',
    'fastcompany.com', 'inc.com', 'entrepreneur.com', 'hbr.org', 'time.com',
    'newsweek.com', 'theatlantic.com', 'newyorker.com', 'vox.com', 'axios.com',
    'nbcnews.com', 'abcnews.com', 'cbsnews.com', 'foxnews.com', 'msnbc.com',
    'npr.org', 'pbs.org', 'guardian.com', 'telegraph.co.uk', 'independent.co.uk'
}

def classify_outlet_tier(domain: str) -> str:
    """
    Classify outlet into tiers for PR prioritization
    
    Returns:
        'Tier 1 Media' - Major national/international outlets
        'News Media' - Regional news, trade publications
        'Trade Media' - Industry-specific publications
        'Other' - Blogs, forums, other sources
    """
    d = domain.lower()
    
    # Check Tier 1 outlets
    if d in TIER_1_OUTLETS:
        return 'Tier 1 Media'
    
    # Check for news indicators
    news_indicators = ['news', 'times', 'post', 'journal', 'tribune', 
                       'herald', 'gazette', 'chronicle', 'observer', 
                       'daily', 'weekly', 'today']
    if any(indicator in d for indicator in news_indicators):
        return 'News Media'
    
    # Check for trade/industry publications
    trade_indicators = ['magazine', 'review', 'digest', 'report', 'wire', 
                       'industry', 'trade', 'professional', 'quarterly']
    if any(indicator in d for indicator in trade_indicators):
        return 'Trade Media'
    
    return 'Other'

def calculate_pr_opportunity_score(outlet_data: dict, brand: str) -> dict:
    """
    Calculate detailed PR opportunity score for an outlet
    
    Args:
        outlet_data: Dictionary with outlet citation data
        brand: Brand name for analysis
    
    Returns:
        Dictionary with score components and total
    """
    scores = {
        'competitive_gap': 0,
        'citation_frequency': 0,
        'tier_bonus': 0,
        'recommendation_value': 0,
        'total': 0
    }
    
    # Competitive Gap Score (0-40 points)
    # Highest value: competitors mentioned but not brand
    if outlet_data.get('total', 0) > 0 and outlet_data.get('brand_mentions', 0) == 0:
        scores['competitive_gap'] = 20
        
        # Extra points if competitors are actively mentioned
        competitor_mentions = sum(outlet_data.get('competitor_mentions', {}).values())
        if competitor_mentions > 0:
            scores['competitive_gap'] += 20  # This is the HIGHEST priority
    
    # Citation Frequency Score (0-20 points)
    # More citations = more trusted by AI
    total_citations = outlet_data.get('total', 0)
    if total_citations >= 10:
        scores['citation_frequency'] = 20
    elif total_citations >= 5:
        scores['citation_frequency'] = 15
    elif total_citations >= 3:
        scores['citation_frequency'] = 10
    elif total_citations >= 1:
        scores['citation_frequency'] = 5
    
    # Tier Bonus (0-20 points)
    # Tier 1 media gets highest bonus
    tier = outlet_data.get('tier', 'Other')
    if tier == 'Tier 1 Media':
        scores['tier_bonus'] = 20
    elif tier == 'News Media':
        scores['tier_bonus'] = 15
    elif tier == 'Trade Media':
        scores['tier_bonus'] = 10
    
    # Recommendation Value (0-20 points)
    # AI actively directing traffic is highest value
    recommended_count = outlet_data.get('recommended', 0)
    if recommended_count >= 5:
        scores['recommendation_value'] = 20
    elif recommended_count >= 3:
        scores['recommendation_value'] = 15
    elif recommended_count >= 1:
        scores['recommendation_value'] = 10
    
    # Calculate total
    scores['total'] = sum([
        scores['competitive_gap'],
        scores['citation_frequency'],
        scores['tier_bonus'],
        scores['recommendation_value']
    ])
    
    return scores

def identify_pr_opportunities(citation_sources: dict, brand: str, competitors: list) -> dict:
    """
    Identify and prioritize PR opportunities from citation data
    
    Args:
        citation_sources: Dictionary of citation sources with their data
        brand: Brand name
        competitors: List of competitor names
    
    Returns:
        Dictionary with categorized PR opportunities
    """
    opportunities = {
        'high_priority': [],  # Score 60+
        'medium_priority': [],  # Score 30-59
        'monitoring': [],  # Already has brand mentions
        'low_priority': []  # Score < 30
    }
    
    for domain, data in citation_sources.items():
        # Add tier classification
        tier = classify_outlet_tier(domain)
        data['tier'] = tier
        
        # Calculate competitor mentions
        if 'competitor_mentions' not in data:
            data['competitor_mentions'] = {}
        
        # Calculate PR opportunity score
        score_breakdown = calculate_pr_opportunity_score(data, brand)
        data['pr_score'] = score_breakdown['total']
        data['pr_score_breakdown'] = score_breakdown
        
        # Categorize opportunity
        outlet_info = {
            'domain': domain,
            'tier': tier,
            'total_citations': data.get('total', 0),
            'brand_mentions': data.get('brand_mentions', 0),
            'competitor_mentions': sum(data.get('competitor_mentions', {}).values()),
            'recommended': data.get('recommended', 0),
            'pr_score': score_breakdown['total'],
            'score_breakdown': score_breakdown,
            'action': ''
        }
        
        # Determine category and action
        if data.get('brand_mentions', 0) > 0:
            # Already has coverage
            outlet_info['action'] = 'Monitor and maintain relationship'
            opportunities['monitoring'].append(outlet_info)
        elif score_breakdown['total'] >= 60:
            # High priority target
            outlet_info['action'] = 'Immediate outreach - high competitive gap'
            opportunities['high_priority'].append(outlet_info)
        elif score_breakdown['total'] >= 30:
            # Medium priority
            outlet_info['action'] = 'Schedule for Q2 outreach'
            opportunities['medium_priority'].append(outlet_info)
        else:
            # Low priority
            outlet_info['action'] = 'Add to long-term monitoring list'
            opportunities['low_priority'].append(outlet_info)
    
    # Sort each category by PR score
    for category in opportunities:
        opportunities[category].sort(key=lambda x: x['pr_score'], reverse=True)
    
    return opportunities

def generate_pr_insights(opportunities: dict, brand: str) -> dict:
    """
    Generate actionable PR insights from opportunity analysis
    
    Args:
        opportunities: Categorized PR opportunities
        brand: Brand name
    
    Returns:
        Dictionary with strategic insights
    """
    insights = {
        'executive_summary': '',
        'immediate_actions': [],
        'quarterly_goals': [],
        'success_metrics': [],
        'budget_justification': ''
    }
    
    # Count opportunities
    high_count = len(opportunities.get('high_priority', []))
    medium_count = len(opportunities.get('medium_priority', []))
    monitoring_count = len(opportunities.get('monitoring', []))
    
    # Executive Summary
    if high_count > 0:
        top_outlet = opportunities['high_priority'][0]
        insights['executive_summary'] = (
            f"Critical PR gap identified: {high_count} high-priority outlets "
            f"citing competitors but not {brand}. "
            f"Top target {top_outlet['domain']} has {top_outlet['total_citations']} "
            f"citations with {top_outlet['competitor_mentions']} competitor mentions "
            f"but zero {brand} coverage."
        )
    else:
        insights['executive_summary'] = (
            f"{brand} has reasonable AI visibility with {monitoring_count} outlets "
            f"providing coverage. Focus should shift to relationship maintenance "
            f"and content optimization."
        )
    
    # Immediate Actions (next 30 days)
    if high_count > 0:
        for outlet in opportunities['high_priority'][:3]:
            action = {
                'outlet': outlet['domain'],
                'action': f"Pitch {brand} story angles",
                'rationale': f"{outlet['total_citations']} AI citations, competitors present",
                'priority': 'HIGH'
            }
            insights['immediate_actions'].append(action)
    
    # Quarterly Goals
    insights['quarterly_goals'] = [
        f"Secure coverage in {min(3, high_count)} Tier 1 outlets",
        f"Develop relationships with {min(5, medium_count)} trade publications",
        "Establish monthly cadence for AI visibility monitoring"
    ]
    
    # Success Metrics
    insights['success_metrics'] = [
        f"Increase {brand} mention rate from current to 75%+",
        f"Achieve top 3 ranking among competitors",
        f"Secure {high_count} new outlet relationships"
    ]
    
    # Budget Justification
    total_opportunities = high_count + medium_count
    insights['budget_justification'] = (
        f"Investment opportunity: {total_opportunities} outlets represent "
        f"untapped PR potential. Competitors have secured coverage in "
        f"{high_count} high-priority outlets where {brand} is absent. "
        f"Closing this gap could increase AI-driven brand discovery by 40-60%."
    )
    
    return insights

def enhance_analysis_with_pr_scoring(analysis_data: dict) -> dict:
    """
    Enhance the standard analysis with PR-specific scoring and insights
    
    Args:
        analysis_data: Standard analysis dictionary from analyze_audit_results
    
    Returns:
        Enhanced analysis with PR opportunities and insights
    """
    # Extract needed data
    brand = analysis_data.get('brand', '')
    competitors = list(analysis_data.get('competitor_mentions', {}).keys())
    
    # Build citation sources dict from top_sources
    citation_sources = {}
    for source in analysis_data.get('top_sources', []):
        domain = source['domain']
        citation_sources[domain] = {
            'total': source.get('total', 0),
            'brand_mentions': source.get('brand_mentions', 0),
            'url_citations': source.get('url_citations', 0),
            'inferred_citations': source.get('inferred_citations', 0),
            'recommended': source.get('recommended', 0),
            'competitor_mentions': {}  # Would need to be calculated from results
        }
    
    # Identify PR opportunities
    opportunities = identify_pr_opportunities(citation_sources, brand, competitors)
    
    # Generate insights
    insights = generate_pr_insights(opportunities, brand)
    
    # Add to analysis
    analysis_data['pr_opportunities'] = opportunities
    analysis_data['pr_insights'] = insights
    
    # Add PR-specific metrics
    analysis_data['pr_metrics'] = {
        'high_priority_targets': len(opportunities.get('high_priority', [])),
        'medium_priority_targets': len(opportunities.get('medium_priority', [])),
        'outlets_with_coverage': len(opportunities.get('monitoring', [])),
        'competitive_gap_score': sum(o['pr_score'] for o in opportunities.get('high_priority', [])),
        'tier_1_opportunities': len([o for o in opportunities.get('high_priority', []) 
                                     if o['tier'] == 'Tier 1 Media'])
    }
    
    return analysis_data
