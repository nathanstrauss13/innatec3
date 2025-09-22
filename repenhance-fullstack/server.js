const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const rateLimit = require('rate-limiter-flexible');
const NodeCache = require('node-cache');
const winston = require('winston');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Cache setup (1 hour default)
const cache = new NodeCache({ stdTTL: 3600 });

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console()
  ]
});

// Rate limiting
const rateLimiter = new rateLimit.RateLimiterMemory({
  keyGenerator: (req) => req.ip,
  points: 10, // Number of requests
  duration: 60, // Per 60 seconds
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Serve static files from React build
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'client/build')));
}

// Rate limiting middleware
app.use('/api', async (req, res, next) => {
  try {
    await rateLimiter.consume(req.ip);
    next();
  } catch (rejRes) {
    res.status(429).json({ error: 'Too many requests' });
  }
});

// AI Service Integrations
const Anthropic = require('@anthropic-ai/sdk');
const OpenAI = require('openai');
const axios = require('axios');

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Core Services
class QueryGenerator {
  static generateSearchQueries(name, location, affiliation) {
    const baseQuery = `"${name}" ${location}`;
    
    return {
      chatgpt: [
        `${baseQuery} professional profile`,
        `${baseQuery} ${affiliation}`,
        `${baseQuery} LinkedIn`,
        `${baseQuery} recent news achievements`
      ],
      claude: [
        `${baseQuery} career background`,
        `${baseQuery} ${affiliation} student alumni`,
        `${baseQuery} professional experience`,
        `${baseQuery} social media presence`
      ],
      gemini: [
        `${baseQuery} public information`,
        `${baseQuery} education work history`,
        `${baseQuery} online presence`,
        `${baseQuery} publications projects`
      ],
      perplexity: [
        `${baseQuery} recent activity`,
        `${baseQuery} industry involvement`,
        `${baseQuery} professional network`,
        `${baseQuery} public appearances`
      ]
    };
  }
}

class AISearchService {
  static async searchChatGPT(queries) {
    try {
      const results = [];
      
      for (const query of queries.slice(0, 2)) { // Limit to 2 queries for cost
        const response = await openai.chat.completions.create({
          model: "gpt-3.5-turbo",
          messages: [{
            role: "user",
            content: `Search for information about: "${query}". 
                     Provide what you would typically find about this person online.
                     Rate the quality and recency of information found (high/medium/low).
                     Format: {confidence: "high/medium/low", summary: "brief summary", sources: ["source1", "source2"]}`
          }],
          max_tokens: 300,
          temperature: 0.3
        });
        
        results.push({
          query,
          response: response.choices[0].message.content,
          platform: 'ChatGPT'
        });
      }
      
      return results;
    } catch (error) {
      logger.error('ChatGPT search error:', error);
      return [{ error: 'ChatGPT search failed', platform: 'ChatGPT' }];
    }
  }

  static async searchClaude(queries) {
    try {
      const results = [];
      
      for (const query of queries.slice(0, 2)) {
        const response = await anthropic.messages.create({
          model: "claude-3-haiku-20240307",
          max_tokens: 300,
          messages: [{
            role: "user",
            content: `Search for information about: "${query}".
                     What would you typically find about this person online?
                     Rate the information quality and recency (high/medium/low).
                     Format: {confidence: "high/medium/low", summary: "brief summary", sources: ["source1", "source2"]}`
          }]
        });
        
        results.push({
          query,
          response: response.content[0].text,
          platform: 'Claude'
        });
      }
      
      return results;
    } catch (error) {
      logger.error('Claude search error:', error);
      return [{ error: 'Claude search failed', platform: 'Claude' }];
    }
  }

  static async searchWeb(queries) {
    try {
      const results = [];
      
      for (const query of queries.slice(0, 3)) {
        if (!process.env.SERPER_API_KEY) {
          // Mock web search if no API key
          results.push({
            query,
            results: [
              { title: 'LinkedIn Profile', link: 'linkedin.com/in/...' },
              { title: 'University Directory', link: 'university.edu/...' }
            ],
            platform: 'Web Search (Mock)'
          });
          continue;
        }

        const response = await axios.post('https://google.serper.dev/search', {
          q: query,
          num: 5
        }, {
          headers: {
            'X-API-KEY': process.env.SERPER_API_KEY,
            'Content-Type': 'application/json'
          }
        });
        
        results.push({
          query,
          results: response.data.organic || [],
          platform: 'Web Search'
        });
      }
      
      return results;
    } catch (error) {
      logger.error('Web search error:', error);
      return [{ error: 'Web search failed', platform: 'Web Search' }];
    }
  }
}

class ReputationAnalyzer {
  static analyzeResults(aiResults, webResults) {
    const analysis = {
      overall: 0,
      professional: 0,
      visibility: 0,
      accuracy: 0,
      findings: [],
      recommendations: []
    };

    // Analyze AI results
    let totalConfidence = 0;
    let highConfidenceCount = 0;
    
    aiResults.forEach(result => {
      if (!result.error) {
        try {
          const content = result.response.toLowerCase();
          
          // Extract confidence level
          if (content.includes('high')) {
            totalConfidence += 3;
            highConfidenceCount++;
          } else if (content.includes('medium')) {
            totalConfidence += 2;
          } else {
            totalConfidence += 1;
          }
          
          // Analyze content quality
          if (content.includes('linkedin') || content.includes('professional')) {
            analysis.professional += 20;
          }
          if (content.includes('recent') || content.includes('current')) {
            analysis.visibility += 15;
          }
          if (content.includes('accurate') || content.includes('verified')) {
            analysis.accuracy += 20;
          }
        } catch (e) {
          logger.error('Error parsing AI result:', e);
        }
      }
    });

    // Analyze web results
    const totalWebResults = webResults.reduce((sum, result) => 
      sum + (result.results ? result.results.length : 0), 0);
    
    analysis.visibility += Math.min(totalWebResults * 5, 40);
    
    // Calculate overall score (add base scores to avoid zeros)
    analysis.professional = Math.max(analysis.professional, 60);
    analysis.visibility = Math.max(analysis.visibility, 45);
    analysis.accuracy = Math.max(analysis.accuracy, 65);
    analysis.overall = Math.round((analysis.professional + analysis.visibility + analysis.accuracy) / 3);
    
    // Cap scores at 100
    Object.keys(analysis).forEach(key => {
      if (typeof analysis[key] === 'number') {
        analysis[key] = Math.min(analysis[key], 100);
      }
    });

    // Generate findings
    analysis.findings = this.generateFindings(aiResults, webResults);
    
    // Generate recommendations
    analysis.recommendations = this.generateRecommendations(analysis);

    return analysis;
  }

  static generateFindings(aiResults, webResults) {
    const findings = [];
    
    // Check LinkedIn presence
    const hasLinkedIn = aiResults.some(result => 
      result.response && result.response.toLowerCase().includes('linkedin')
    );
    
    findings.push({
      category: 'LinkedIn Profile',
      status: hasLinkedIn ? 'found' : 'limited',
      description: hasLinkedIn ? 
        'Found recent professional information' : 
        'Limited or outdated profile information'
    });

    // Check web presence
    const totalResults = webResults.reduce((sum, result) => 
      sum + (result.results ? result.results.length : 0), 0);
    
    findings.push({
      category: 'Web Presence',
      status: totalResults > 10 ? 'strong' : totalResults > 5 ? 'moderate' : 'weak',
      description: `Found ${totalResults} relevant web results`
    });

    findings.push({
      category: 'Social Media',
      status: 'limited',
      description: 'Limited professional presence'
    });

    findings.push({
      category: 'Recent Projects',
      status: 'none',
      description: 'No recent professional content found'
    });

    return findings;
  }

  static generateRecommendations(analysis) {
    const recommendations = [];
    
    if (analysis.professional < 80) {
      recommendations.push({
        title: 'Optimize LinkedIn Profile',
        description: 'Update your headline, summary, and recent experiences to improve AI discoverability',
        impact: 'high',
        effort: 'low',
        automated: false,
        actionType: 'linkedin'
      });
    }

    if (analysis.visibility < 70) {
      recommendations.push({
        title: 'Create Professional Website',
        description: 'Build a simple portfolio site with your name in the domain for better search results',
        impact: 'high',
        effort: 'medium',
        automated: false,
        actionType: 'website'
      });
      
      recommendations.push({
        title: 'Publish Content',
        description: 'Write articles or posts about your field to create fresh, relevant content',
        impact: 'medium',
        effort: 'medium',
        automated: false,
        actionType: 'content'
      });
    }

    recommendations.push({
      title: 'Update University Profile',
      description: 'Contact your alumni office to update your directory listing',
      impact: 'low',
      effort: 'low',
      automated: true
    });

    recommendations.push({
      title: 'Google Knowledge Panel',
      description: 'Claim and optimize your Google Knowledge Panel if eligible',
      impact: 'high',
      effort: 'high',
      automated: false
    });

    recommendations.push({
      title: 'Professional Social Media',
      description: 'Clean up and optimize your social media profiles for professional viewing',
      impact: 'medium',
      effort: 'low',
      automated: true
    });

    return recommendations;
  }
}

// API Routes
app.post('/api/analyze-reputation', async (req, res) => {
  try {
    const { name, location, affiliation } = req.body;
    
    // Validation
    if (!name || !location) {
      return res.status(400).json({ 
        error: 'Name and location are required' 
      });
    }

    // Check cache
    const cacheKey = `${name}_${location}_${affiliation}`.replace(/\s+/g, '_');
    const cached = cache.get(cacheKey);
    if (cached) {
      return res.json(cached);
    }

    logger.info(`Starting reputation analysis for: ${name}`);

    // Generate search queries
    const queries = QueryGenerator.generateSearchQueries(name, location, affiliation);
    
    // Perform AI searches
    const [chatgptResults, claudeResults] = await Promise.all([
      AISearchService.searchChatGPT(queries.chatgpt),
      AISearchService.searchClaude(queries.claude)
    ]);

    // Perform web search
    const webResults = await AISearchService.searchWeb([
      `"${name}" ${location}`,
      `${name} ${affiliation}`,
      `${name} professional`
    ]);

    // Analyze results
    const allAiResults = [...chatgptResults, ...claudeResults];
    const analysis = ReputationAnalyzer.analyzeResults(allAiResults, webResults);

    const result = {
      timestamp: new Date().toISOString(),
      person: { name, location, affiliation },
      scores: {
        overall: analysis.overall,
        professional: analysis.professional,
        visibility: analysis.visibility,
        accuracy: analysis.accuracy
      },
      searchQueries: {
        chatgpt: { confidence: 'high', scope: 'LinkedIn, news, social media, professional directories' },
        claude: { confidence: 'medium', scope: 'LinkedIn, news, social media, professional directories' },
        gemini: { confidence: 'high', scope: 'LinkedIn, news, social media, professional directories' },
        perplexity: { confidence: 'low', scope: 'LinkedIn, news, social media, professional directories' }
      },
      findings: analysis.findings,
      recommendations: analysis.recommendations,
      aiResults: allAiResults.map(r => ({ platform: r.platform, hasData: !r.error }))
    };

    // Cache result
    cache.set(cacheKey, result, 1800); // 30 minutes

    logger.info(`Completed reputation analysis for: ${name}`);
    res.json(result);

  } catch (error) {
    logger.error('Reputation analysis error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Analysis failed'
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Get recommendations details
app.get('/api/recommendations/:type', (req, res) => {
  const { type } = req.params;
  
  const guides = {
    linkedin: {
      steps: [
        'Update your headline to include your target role and key skills',
        'Write a compelling summary with relevant keywords',
        'Add recent projects and achievements',
        'Get recommendations from colleagues or professors',
        'Post regularly about your industry'
      ],
      tools: ['LinkedIn optimization guide', 'Keyword research tool', 'Profile strength analyzer'],
      estimatedTime: '2-3 hours',
      impact: 'High - LinkedIn is the first place AI looks for professional info'
    },
    website: {
      steps: [
        'Register a domain with your name (yourname.com)',
        'Choose a professional template (Squarespace, Wix, or custom)',
        'Add your bio, portfolio, and contact information',
        'Optimize for search engines with relevant keywords',
        'Set up Google Analytics and Search Console'
      ],
      tools: ['Website builder', 'SEO optimization', 'Domain registration', 'Analytics setup'],
      estimatedTime: '1-2 days',
      impact: 'High - Creates authoritative source about you'
    },
    content: {
      steps: [
        'Identify topics in your field of expertise',
        'Write 1-2 articles per month on LinkedIn or Medium',
        'Share insights about industry trends',
        'Engage with others\' content in your field',
        'Cross-post content across platforms'
      ],
      tools: ['Content calendar', 'Writing assistant', 'Social media scheduler', 'Analytics tracker'],
      estimatedTime: '1-2 hours per week',
      impact: 'Medium - Shows thought leadership and expertise'
    }
  };

  const guide = guides[type];
  if (!guide) {
    return res.status(404).json({ error: 'Guide not found' });
  }

  res.json(guide);
});

// Serve React app for all other routes in production
if (process.env.NODE_ENV === 'production') {
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
  });
}

// Error handling middleware
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, () => {
  logger.info(`RepEnhance server running on port ${PORT}`);
  console.log(`🚀 RepEnhance server running on http://localhost:${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
  if (process.env.NODE_ENV !== 'production') {
    console.log(`🎨 Frontend dev server: http://localhost:3000`);
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

module.exports = app;
