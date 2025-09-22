const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY || '');
const puppeteer = require('puppeteer');
const nodemailer = require('nodemailer');
const Redis = require('ioredis');
const winston = require('winston');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const { QueryGenerator } = require('./services/queryGenerator');
const { AIQueryExecutor } = require('./services/aiExecutor');

const app = express();
const PORT = process.env.PORT || 3000;

// Logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: path.join(__dirname, '../../error.log'), level: 'error' }),
    new winston.transports.File({ filename: path.join(__dirname, '../../combined.log') }),
    new winston.transports.Console({ format: winston.format.simple() })
  ]
});

// Initialize Redis (graceful fallback)
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT ? parseInt(process.env.REDIS_PORT, 10) : 6379,
  password: process.env.REDIS_PASSWORD || undefined
});
redis.on('error', (err) => logger.warn(`Redis error: ${err.message}`));

const redisGet = async (key) => {
  try {
    return await redis.get(key);
  } catch (e) {
    logger.warn(`Redis GET failed: ${e.message}`);
    return null;
  }
};
const redisSetEx = async (key, ttl, value) => {
  try {
    await redis.set(key, value, 'EX', ttl);
  } catch (e) {
    logger.warn(`Redis SET failed: ${e.message}`);
  }
};

// Email transporter
const emailTransporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: process.env.SMTP_PORT ? parseInt(process.env.SMTP_PORT, 10) : 587,
  secure: false,
  auth: (process.env.SMTP_USER && process.env.SMTP_PASS) ? {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  } : undefined
});

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3001',
  credentials: true
}));
app.use(express.json({ limit: '1mb' }));

// Rate limiting
const apiLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
const analysisLimiter = rateLimit({ windowMs: 60 * 60 * 1000, max: 10 });
app.use('/api/', apiLimiter);
app.use('/api/analyze', analysisLimiter);

// In-memory database
const db = {
  analyses: new Map(),
  reports: new Map(),
  payments: new Map()
};

// Ensure reports directory
const reportsDir = path.join(__dirname, '../../reports');
fs.mkdirSync(reportsDir, { recursive: true });

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.post('/api/analyze/preview', async (req, res) => {
  try {
    const { brandName, email } = req.body || {};
    if (!brandName || !email) {
      return res.status(400).json({ error: 'Brand name and email required' });
    }
    const analysisId = uuidv4();

    // cached?
    const cacheKey = `analysis:${String(brandName).toLowerCase()}`;
    const cached = await redisGet(cacheKey);
    if (cached) {
      const data = JSON.parse(cached);
      db.analyses.set(analysisId, {
        id: analysisId,
        brand: brandName,
        email,
        data,
        status: 'completed',
        createdAt: new Date()
      });
      logger.info(`Served cached analysis for ${brandName}`);
      return res.json({ analysisId, status: 'completed', cached: true });
    }

    // create processing record
    db.analyses.set(analysisId, {
      id: analysisId,
      brand: brandName,
      email,
      status: 'processing',
      createdAt: new Date()
    });

    performAnalysis(analysisId, brandName, email).catch((err) => {
      logger.error(`performAnalysis error: ${err.stack || err.message}`);
    });

    res.json({ analysisId, status: 'processing', estimatedTime: 60 });
  } catch (error) {
    logger.error(`Analysis preview error: ${error.stack || error.message}`);
    res.status(500).json({ error: 'Failed to start analysis' });
  }
});

app.get('/api/analyze/status/:analysisId', async (req, res) => {
  try {
    const { analysisId } = req.params;
    const analysis = db.analyses.get(analysisId);
    if (!analysis) return res.status(404).json({ error: 'Analysis not found' });

    if (analysis.status === 'completed') {
      const data = analysis.data || {};
      return res.json({
        status: 'completed',
        preview: {
          visibilityScore: data.visibilityScore,
          competitorComparison: data.competitorComparison,
          topPublishers: data.topPublishers || [],
          totalMentions: data.totalMentions || 0
        }
      });
    } else if (analysis.status === 'failed') {
      return res.json({ status: 'failed', error: analysis.error || 'Unknown error' });
    } else {
      return res.json({ status: 'processing' });
    }
  } catch (error) {
    logger.error(`Status error: ${error.stack || error.message}`);
    res.status(500).json({ error: 'Failed to get status' });
  }
});

// Payment stub
app.post('/api/purchase', async (req, res) => {
  try {
    const { analysisId } = req.body || {};
    if (!analysisId) return res.status(400).json({ error: 'analysisId required' });
    if (!db.analyses.has(analysisId)) return res.status(404).json({ error: 'Analysis not found' });

    const paymentId = uuidv4();
    db.payments.set(analysisId, {
      id: paymentId,
      analysisId,
      status: 'succeeded',
      createdAt: new Date()
    });
    res.json({ success: true, paymentId });
  } catch (error) {
    logger.error(`Purchase error: ${error.stack || error.message}`);
    res.status(500).json({ error: 'Payment failed' });
  }
});

// Report generation
app.post('/api/report/generate', async (req, res) => {
  try {
    const { analysisId } = req.body || {};
    if (!analysisId) return res.status(400).json({ error: 'analysisId required' });
    const analysis = db.analyses.get(analysisId);
    if (!analysis || analysis.status !== 'completed') {
      return res.status(400).json({ error: 'Analysis not ready' });
    }

    // Require payment (stub)
    const payment = db.payments.get(analysisId);
    if (!payment || payment.status !== 'succeeded') {
      return res.status(402).json({ error: 'Payment required' });
    }

    const templatePath = path.join(__dirname, 'templates', 'report.html');
    let html = fs.readFileSync(templatePath, 'utf8');
    const rows = (analysis.data.topPublishers || [])
      .map(p => `<tr><td>${p.name}</td><td>${p.citations}</td></tr>`)
      .join('');

    // Support both {{placeholders}} and __PLACEHOLDERS__ to avoid CSS lint issues
    html = html
      // double-curly style
      .replace(/{{\s*brandName\s*}}/g, analysis.brand)
      .replace(/{{\s*visibilityScore\s*}}/g, String(analysis.data.visibilityScore))
      .replace(/{{\s*competitorComparison\s*}}/g, analysis.data.competitorComparison)
      .replace(/{{\s*totalMentions\s*}}/g, String(analysis.data.totalMentions || 0))
      .replace(/{{\s*publishers_rows\s*}}/g, rows)
      .replace(/{{\s*date\s*}}/g, new Date().toLocaleDateString())
      // underscored
      .replace(/__BRAND__/g, analysis.brand)
      .replace(/__VISIBILITY_SCORE__/g, String(analysis.data.visibilityScore))
      .replace(/__VISIBILITY_PCT__/g, String(analysis.data.visibilityScore))
      .replace(/__COMP__/g, analysis.data.competitorComparison)
      .replace(/__TOTAL__/g, String(analysis.data.totalMentions || 0))
      .replace(/__PUBLISHERS_ROWS__/g, rows)
      .replace(/__DATE__/g, new Date().toLocaleDateString());

    const browser = await puppeteer.launch({
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'load' });
    await page.emulateMediaType('screen');
    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      margin: { top: '20mm', bottom: '20mm', left: '15mm', right: '15mm' }
    });
    await browser.close();

    const reportId = uuidv4();
    const pdfPath = path.join(reportsDir, `${reportId}.pdf`);
    fs.writeFileSync(pdfPath, pdf);

    db.reports.set(reportId, {
      id: reportId,
      analysisId,
      path: pdfPath,
      brand: analysis.brand,
      email: analysis.email,
      createdAt: new Date()
    });

    // Email delivery (best-effort)
    if (process.env.SMTP_USER && process.env.SMTP_PASS && analysis.email) {
      try {
        await emailTransporter.sendMail({
          from: {
            name: process.env.REPORT_FROM_NAME || 'AI PRism',
            address: process.env.REPORT_FROM_EMAIL || process.env.SMTP_USER
          },
          to: analysis.email,
          subject: `Your AI PRism Report - ${analysis.brand}`,
          text: `Attached is your AI PRism PDF report for ${analysis.brand}.`,
          attachments: [{ filename: `ai-prism-${analysis.brand}.pdf`, path: pdfPath }]
        });
        logger.info(`Report emailed to ${analysis.email}`);
      } catch (mailErr) {
        logger.warn(`Email failed: ${mailErr.message}`);
      }
    }

    res.json({ reportId, url: `/api/report/${reportId}/pdf` });
  } catch (error) {
    logger.error(`Report generation error: ${error.stack || error.message}`);
    res.status(500).json({ error: 'Failed to generate report' });
  }
});

app.get('/api/report/:reportId/pdf', async (req, res) => {
  try {
    const { reportId } = req.params;
    const report = db.reports.get(reportId);
    if (!report) return res.status(404).json({ error: 'Report not found' });
    return res.sendFile(report.path);
  } catch (error) {
    logger.error(`Report fetch error: ${error.stack || error.message}`);
    res.status(500).json({ error: 'Failed to fetch report' });
  }
});

// Analysis worker
async function performAnalysis(analysisId, brandName, email) {
  try {
    const plan = QueryGenerator.generate(brandName);
    // Simulated execution (extend to real providers if keys present)
    const result = await AIQueryExecutor.run(plan, { brandName });

    const data = {
      visibilityScore: result.visibilityScore,
      competitorComparison: result.competitorComparison,
      topPublishers: result.topPublishers,
      totalMentions: result.totalMentions,
      providersQueried: result.providersQueried,
      queryPlan: plan
    };

    db.analyses.set(analysisId, {
      id: analysisId,
      brand: brandName,
      email,
      data,
      status: 'completed',
      createdAt: new Date()
    });

    // Cache by brand
    const cacheKey = `analysis:${String(brandName).toLowerCase()}`;
    await redisSetEx(cacheKey, 60 * 60 * 24, JSON.stringify(data));
    logger.info(`Analysis completed for ${brandName} (${analysisId})`);
  } catch (error) {
    db.analyses.set(analysisId, {
      id: analysisId,
      brand: brandName,
      email,
      status: 'failed',
      error: error.message || 'Unknown error',
      createdAt: new Date()
    });
    logger.error(`Analysis failed for ${brandName}: ${error.stack || error.message}`);
  }
}

app.listen(PORT, () => {
  logger.info(`AI PRism backend listening on port ${PORT}`);
});
