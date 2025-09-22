# RepEnhance - AI Reputation Enhancement Platform

A complete full-stack application that analyzes your AI reputation across ChatGPT, Claude, and other AI platforms, providing actionable insights to enhance your digital presence.

## 🚀 Features

### Backend (Node.js + Express)
- ✅ Real AI integrations (Anthropic Claude + OpenAI ChatGPT)
- ✅ Web search via Serper API
- ✅ Production-ready with caching, rate limiting, logging
- ✅ RESTful API endpoints
- ✅ Error handling and validation

### Frontend (React)
- ✅ Modern dark theme UI
- ✅ Real-time API communication
- ✅ Interactive recommendation system
- ✅ Responsive design with Tailwind CSS
- ✅ Loading states and error handling
- ✅ Expandable action guides

### Key Features
- 🔍 **Real AI Analysis**: Actually queries ChatGPT and Claude APIs
- 📊 **Smart Scoring**: Analyzes AI responses to calculate reputation scores
- 📝 **Actionable Recommendations**: Provides specific, prioritized improvement steps
- 🎯 **Interactive Guides**: Click "Get guide" for detailed step-by-step instructions
- ⚡ **Auto-fix Options**: Simulates automated profile improvements
- 🔒 **Production Ready**: Security, monitoring, and scalability built-in

## 🛠️ Quick Setup (5 minutes)

### 1. Prerequisites
- Node.js 16+ installed
- API keys for:
  - **Anthropic API Key** (required) - Get from https://console.anthropic.com/
  - **OpenAI API Key** (required) - Get from https://platform.openai.com/
  - **Serper API Key** (optional) - Get from https://serper.dev/ (will use mock data if missing)

### 2. Installation
Dependencies are already installed! If you need to reinstall:
```bash
npm run install-all
```

### 3. Environment Setup
Update the `.env` file in the root directory with your API keys:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
PORT=3001
NODE_ENV=development
```

### 4. Run the Application
```bash
# Start both backend and frontend
npm run dev

# Or run separately:
# Backend only: npm run server
# Frontend only: npm run client
```

### 5. Open in Browser
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **Health Check**: http://localhost:3001/api/health

## 📁 Project Structure
```
repenhance-fullstack/
├── server.js              # Express backend server
├── package.json           # Backend dependencies
├── .env                   # Environment variables
├── client/                # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styles
│   │   └── index.js       # React entry point
│   ├── public/
│   │   └── index.html     # HTML template
│   └── package.json       # Frontend dependencies
└── README.md              # This file
```

## 🔧 API Endpoints

### POST /api/analyze-reputation
Analyzes a person's AI reputation across multiple platforms.

**Request Body:**
```json
{
  "name": "John Doe",
  "location": "San Francisco, CA",
  "affiliation": "Stanford University"
}
```

**Response:**
```json
{
  "timestamp": "2025-01-01T00:00:00.000Z",
  "person": { "name": "John Doe", "location": "San Francisco, CA", "affiliation": "Stanford University" },
  "scores": {
    "overall": 75,
    "professional": 80,
    "visibility": 65,
    "accuracy": 85
  },
  "findings": [...],
  "recommendations": [...]
}
```

### GET /api/recommendations/:type
Gets detailed guides for specific recommendation types (linkedin, website, content).

### GET /api/health
Health check endpoint.

## 🎯 How It Works

1. **User Input**: Enter name, location, and recent affiliation
2. **Query Generation**: Creates optimized search queries for each AI platform
3. **AI Analysis**: Actually queries ChatGPT and Claude APIs with the generated queries
4. **Web Search**: Performs web searches to gather additional context (optional)
5. **Score Calculation**: Analyzes AI responses to calculate reputation scores
6. **Recommendations**: Generates personalized, actionable improvement suggestions
7. **Interactive Guides**: Provides detailed step-by-step guides for each recommendation

## 🔐 Security Features

- Rate limiting (10 requests per minute per IP)
- Input validation and sanitization
- CORS protection
- Helmet security headers
- Request logging
- Error handling and monitoring

## 💡 Usage Tips

1. **API Keys**: Make sure to add your real API keys to the `.env` file for full functionality
2. **Serper API**: Optional but recommended for real web search results
3. **Rate Limits**: The app includes built-in rate limiting to prevent API abuse
4. **Caching**: Results are cached for 30 minutes to improve performance
5. **Mock Data**: If Serper API key is missing, the app will use mock web search data

## 🚀 Deployment

### Environment Variables for Production
```env
ANTHROPIC_API_KEY=your_production_anthropic_key
OPENAI_API_KEY=your_production_openai_key
SERPER_API_KEY=your_production_serper_key
PORT=3001
NODE_ENV=production
```

### Build for Production
```bash
npm run build
npm start
```

## 🛠️ Development

### Available Scripts
- `npm run dev` - Start both frontend and backend in development mode
- `npm run server` - Start only the backend server
- `npm run client` - Start only the frontend development server
- `npm run build` - Build the frontend for production
- `npm run install-all` - Install all dependencies (backend + frontend)
- `npm test` - Run tests

### Tech Stack
- **Backend**: Node.js, Express, Winston (logging), Node-Cache
- **Frontend**: React 18, Tailwind CSS (via CDN), Lucide React (icons)
- **AI APIs**: Anthropic Claude, OpenAI ChatGPT
- **Search**: Serper API for web search
- **Security**: Helmet, CORS, Rate Limiting

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
1. Check the console logs for error details
2. Verify your API keys are correct
3. Ensure all dependencies are installed
4. Check that ports 3000 and 3001 are available

---

**Ready to enhance your AI reputation? Start by adding your API keys to the `.env` file and running `npm run dev`!**
