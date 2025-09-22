const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 3002;

app.use(cors());
app.use(express.json());

// Mock data for testing
const generateMockAnalysis = (formData) => {
  const { name, location, affiliation } = formData;
  
  return {
    timestamp: new Date().toISOString(),
    person: { name, location, affiliation },
    scores: {
      overall: Math.floor(Math.random() * 30) + 70, // 70-100
      professional: Math.floor(Math.random() * 25) + 75, // 75-100
      visibility: Math.floor(Math.random() * 40) + 45, // 45-85
      accuracy: Math.floor(Math.random() * 20) + 65, // 65-85
    },
    searchQueries: {
      chatgpt: { 
        confidence: 'high', 
        scope: 'LinkedIn, news, social media, professional directories',
        recognitionRate: 0.8,
        sentiment: 'positive'
      },
      claude: { 
        confidence: 'medium', 
        scope: 'LinkedIn, news, social media, professional directories',
        recognitionRate: 0.6,
        sentiment: 'neutral'
      },
      gemini: { 
        confidence: 'high', 
        scope: 'LinkedIn, news, social media, professional directories',
        recognitionRate: 0.9,
        sentiment: 'positive'
      },
      perplexity: { 
        confidence: 'low', 
        scope: 'LinkedIn, news, social media, professional directories',
        recognitionRate: 0.4,
        sentiment: 'mixed'
      }
    },
    findings: [
      {
        category: 'LinkedIn Profile',
        status: 'found',
        description: `Found recent professional information for ${name}`
      },
      {
        category: 'Web Presence',
        status: 'moderate',
        description: 'Found 8 relevant web results'
      },
      {
        category: 'Social Media',
        status: 'limited',
        description: 'Limited professional presence detected'
      },
      {
        category: 'Recent Projects',
        status: 'none',
        description: 'No recent professional content found'
      }
    ],
    recommendations: [
      {
        title: 'Optimize LinkedIn Profile',
        description: 'Update your headline, summary, and recent experiences to improve AI discoverability',
        impact: 'high',
        effort: 'low',
        automated: false,
        actionType: 'linkedin'
      },
      {
        title: 'Create Professional Website',
        description: 'Build a simple portfolio site with your name in the domain for better search results',
        impact: 'high',
        effort: 'medium',
        automated: false,
        actionType: 'website'
      },
      {
        title: 'Publish Content',
        description: 'Write articles or posts about your field to create fresh, relevant content',
        impact: 'medium',
        effort: 'medium',
        automated: false,
        actionType: 'content'
      },
      {
        title: 'Update University Profile',
        description: 'Contact your alumni office to update your directory listing',
        impact: 'low',
        effort: 'low',
        automated: true
      },
      {
        title: 'Professional Social Media',
        description: 'Clean up and optimize your social media profiles for professional viewing',
        impact: 'medium',
        effort: 'low',
        automated: true
      }
    ],
    aiResults: [
      { platform: 'ChatGPT', hasData: true },
      { platform: 'Claude', hasData: true },
      { platform: 'Gemini', hasData: true },
      { platform: 'Perplexity', hasData: false }
    ]
  };
};

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.0-mock'
  });
});

// Main analysis endpoint
app.post('/api/analyze-reputation', (req, res) => {
  const { name, location, affiliation } = req.body;
  
  // Validation
  if (!name || !location) {
    return res.status(400).json({ 
      error: 'Name and location are required' 
    });
  }

  console.log(`Mock analysis request for: ${name} from ${location}`);
  
  // Simulate processing delay
  setTimeout(() => {
    const mockData = generateMockAnalysis({ name, location, affiliation });
    res.json(mockData);
  }, 1000); // 1 second delay to simulate real API
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

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Mock server error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Mock RepEnhance API server running on http://localhost:${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
  console.log(`🎯 This server provides mock data for testing the iOS app`);
});

module.exports = app;
