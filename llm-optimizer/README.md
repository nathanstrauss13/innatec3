# LLM Training Optimizer

A Flask web application that analyzes URLs and provides technical and content recommendations to improve the likelihood that the information will be used to train large language models.

## Features

- **URL Content Analysis**: Fetches and analyzes webpage content, structure, and metadata
- **Technical Recommendations**: HTML structure, semantic markup, and SEO improvements
- **Content Quality Assessment**: Clarity, comprehensiveness, and knowledge preservation recommendations
- **LLM Training Optimization**: Specific guidance for making content more valuable for AI training data
- **Real-time Analysis**: Instant feedback on webpage optimization opportunities

## How It Works

1. **Content Extraction**: Fetches webpage content and parses HTML structure
2. **Technical Analysis**: Evaluates semantic HTML, structured data, metadata, and heading hierarchy
3. **AI-Powered Recommendations**: Uses Claude API to generate specific optimization suggestions
4. **Actionable Results**: Provides categorized recommendations for technical and content improvements

## Installation

1. Clone or download the application files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   FLASK_SECRET_KEY=your_secret_key
   ```
4. Run the application:
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5010`

## API Endpoints

- `GET /` - Main application interface
- `POST /analyze` - Analyze a URL (expects JSON with `url` field)
- `GET /health` - Health check endpoint

## Usage

1. Enter any URL in the input field
2. Click "Analyze" to start the analysis
3. Review the content overview and technical analysis
4. Implement the AI-generated recommendations to optimize your content for LLM training

## Deployment

The application is configured for deployment on Render or Heroku:
- Uses `Procfile` for process configuration
- Uses `render.yaml` for Render deployment
- Gunicorn serves the application in production

## Technical Stack

- **Backend**: Python Flask
- **AI Analysis**: Anthropic Claude API
- **Content Parsing**: BeautifulSoup4
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Deployment**: Gunicorn, Render/Heroku compatible

## About

Created by Innate C3 - Corporate Communications & Content Strategy specialists.