# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains multiple Flask-based web applications for Innate C3, a corporate communications consulting firm. The main applications are:

1. **Media Analysis App** (`app.py`) - The primary application for analyzing media coverage and generating comparative insights
2. **News Analyzer** (`news-analyzer/`) - A focused news analysis tool 
3. **Writing Assistant** (`writing-assistant-repo/`) - A content generation tool for communications professionals

## Common Development Commands

### Running Applications Locally

```bash
# Main media analysis app (runs on port 5009)
python app.py

# News analyzer (runs on port 5008)
cd news-analyzer && python app.py

# Writing assistant (runs on port 5000)
cd writing-assistant-repo && python app.py
```

### Environment Setup

All applications require these environment variables in a `.env` file:
- `ANTHROPIC_API_KEY` - Required for all AI functionality
- `NEWS_API_KEY` - Required for news API integration
- `FLASK_SECRET_KEY` - Required for Flask sessions
- `DATABASE_URL` - SQLite database path (defaults to sqlite:///waitlist.db)

### Installing Dependencies

```bash
# Install main app dependencies
pip install -r requirements.txt

# Install news analyzer dependencies
cd news-analyzer && pip install -r requirements.txt

# Install writing assistant dependencies  
cd writing-assistant-repo && pip install -r requirements.txt
```

### Database Operations

The main app uses SQLAlchemy with a SQLite database:
```bash
# Database tables are auto-created on app startup
# Database file: instance/waitlist.db
```

### Deployment

Applications are configured for deployment on Render:
- Uses `Procfile` for process configuration
- Uses `render.yaml` for service configuration
- Gunicorn serves the applications in production

## Architecture Overview

### Main Application Structure

- **Flask Backend**: Handles web requests, API integrations, and database operations
- **Anthropic Integration**: Uses Claude API for sentiment analysis and content generation  
- **File Processing**: Supports Excel, PDF, and PowerPoint file uploads with intelligent data extraction
- **News API Integration**: Fetches real-time news data for analysis
- **Database Layer**: SQLAlchemy models for waitlist management

### Key Components

- `app.py` - Main Flask application with routes and core functionality
- `utils/file_processor.py` - File processing utilities for media data extraction
- `utils/simple_file_processor.py` - Simplified file processor for basic operations
- `templates/` - Jinja2 HTML templates for UI
- `static/` - CSS, JavaScript, and media assets

### File Upload System

The application supports uploading:
- Excel files (.xlsx, .xls) - Media coverage tracking spreadsheets
- PDF files - Reports and documents
- PowerPoint files (.pptx) - Presentation content
- Maximum file size: 16MB
- Files are processed and then deleted automatically

### AI Integration Patterns

1. **Sentiment Analysis**: Batch processing of article sentiment using Claude API
2. **Content Generation**: Template-based prompts for various content types
3. **Data Extraction**: Intelligent column mapping from uploaded files using AI

## Development Guidelines

### Adding New Analysis Features

1. Update the `analyze_articles()` function in `app.py`
2. Modify templates in `templates/result.html` for new visualizations
3. Add new route handlers for additional analysis types

### Working with File Processors

- Extend `MediaFileProcessor` class for new file types
- Use intelligent column mapping for data extraction
- Always clean up uploaded files after processing

### API Integration

- All external API calls should include error handling
- Use environment variables for API keys
- Implement rate limiting for API-heavy operations

### Database Changes

- Models are defined in `app.py` using SQLAlchemy
- Database auto-creates tables on startup
- Use Flask-SQLAlchemy patterns for queries and updates