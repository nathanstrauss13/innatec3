# Render Deployment Guide for AI Citation Audit

## Prerequisites
- GitHub account
- Render account (free tier works)
- API keys for OpenAI, Anthropic, Perplexity, and Google (Gemini)

## Step 1: Push to GitHub

1. Create a new GitHub repository
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit - AI Citation Audit with PR backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-citation-audit.git
git push -u origin main
```

## Step 2: Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: ai-citation-audit
   - **Region**: Choose nearest to you
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web_app:app`

## Step 3: Set Environment Variables

In Render dashboard, go to Environment tab and add:

### Required API Keys:
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `PERPLEXITY_API_KEY` or `PPLX_API_KEY` - Your Perplexity API key
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - Your Google/Gemini API key

### Optional:
- `FLASK_SECRET_KEY` - Will be auto-generated if not set
- `PORT` - Default is 5030

## Step 4: Deploy

1. Click "Create Web Service"
2. Wait for deployment (takes 2-5 minutes)
3. Your app will be available at: `https://ai-citation-audit.onrender.com`

## Available Endpoints

Once deployed, you can access:

- **Main Dashboard**: `/` - Original audit interface
- **Typeform Audit**: `/typeform-audit` - Enhanced PR-focused audit
- **Simple Audit**: `/simple-audit` - 3-step simplified flow
- **Lead Gen**: `/lead-gen` - Lead generation form

## API Endpoints (for integration):

### Run Typeform Audit
```bash
curl -X POST https://your-app.onrender.com/typeform-audit \
  -H "Content-Type: application/json" \
  -d '{
    "action": "run_audit",
    "brand": "Tesla",
    "competitors": ["Rivian", "Lucid Motors"],
    "prompts": [
      "What are the best electric vehicles?",
      "Which EV brands are most reliable?"
    ]
  }'
```

Response includes:
- PR opportunity scores
- Outlet classifications (Tier 1, News, Trade, Other)
- Competitive gap analysis
- Strategic recommendations

## Testing the Deployment

1. Visit `/typeform-audit`
2. Enter test brand: "Tesla"
3. Enter test query: "What are the best electric vehicles?"
4. Review competitors (auto-detected)
5. Run audit
6. Check results dashboard for:
   - PR opportunities
   - Media outlet matrix
   - Citation type breakdown
   - Strategic recommendations

## Monitoring

- Render provides automatic HTTPS
- Check logs in Render dashboard
- Free tier includes 750 hours/month
- Automatic deploys on git push

## Troubleshooting

### If API calls fail:
- Check environment variables are set correctly
- Verify API keys are valid
- Check Render logs for errors

### If deployment fails:
- Ensure all imports in web_app.py are in requirements.txt
- Check Python version compatibility (3.9+)
- Review build logs in Render dashboard

## Cost Considerations

### Render (hosting):
- **Free tier**: 750 hours/month, spins down after 15 min inactivity
- **Paid tier**: $7/month for always-on

### API Costs (per audit):
- OpenAI: ~$0.02-0.05
- Anthropic: ~$0.02-0.04
- Perplexity: ~$0.01-0.02
- Google: ~$0.01-0.02
- **Total per audit**: ~$0.06-0.13

## Support

For issues or questions:
- Check Render status: https://status.render.com/
- Review logs in Render dashboard
- Ensure all API keys are valid and have credits

## Next Steps

After deployment:
1. Test all endpoints
2. Set up custom domain (optional)
3. Configure auto-deploy from GitHub
4. Monitor usage and costs
5. Consider upgrading to paid tier for production use
