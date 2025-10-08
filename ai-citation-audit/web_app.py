#!/usr/bin/env python3
import os
import subprocess
import shlex
import requests
import logging
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, flash

# Load environment variables from .env for web context (ensures Perplexity, etc. available in Typeform flow)
try:
    from load_env import load_env as _load_env
    _load_env()
except Exception as _e:
    print(f"Warning: .env not loaded in web_app.py: {_e}")

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

REPORTS_DIR = os.path.join("news-analyzer", "static", "reports")

# Inline templates (keeps this MVP to a single file)
TPL_INDEX = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AI Citation Audit (MVP)</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; color:#222; padding:24px; max-width: 980px; margin: 0 auto; }
    h1,h2,h3 { margin: 0.4em 0; }
    label { display:block; margin-top:10px; font-weight:600; }
    input[type=text], input[type=date], textarea, select { width:100%; padding:8px; margin-top:6px; border:1px solid #ddd; border-radius:6px; font-size:14px; }
    .row { display:flex; gap:12px; }
    .col { flex:1; }
    .btns { margin-top:16px; display:flex; gap:12px; }
    button { padding:10px 14px; border:1px solid #0c6; color:#fff; background:#0c6; border-radius:6px; cursor:pointer; }
    button.secondary { background:#666; border-color:#666; }
    .muted { color:#666; font-size: 12px; }
    .card { border:1px solid #eee; border-radius:8px; padding:12px 16px; margin:12px 0; }
    pre { background:#f7f7f7; padding:10px; border-radius:6px; overflow:auto; }
    ul { margin-top: 6px; }
  </style>
</head>
<body>
  <h1>AI Citation Visibility Audit (MVP)</h1>
  <p class="muted">Enter a brand, date range, and (optionally) competitors. Preview the standardized prompts, then run the audit. Output: HTML report + CSV.</p>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="card">
        {% for m in messages %}
          <div>{{ m }}</div>
        {% endfor %}
      </div>
    {% endif %}
  {% endwith %}

  <form method="post">
    <input type="hidden" name="action" value="preview">
    <label>Brand</label>
    <input type="text" name="brand" required value="{{ brand or '' }}">

    <label>Competitors (comma separated)</label>
    <input type="text" name="competitors" placeholder="e.g., Smithfield, Carando, Omaha Steaks, Harry & David, Wild Fork" value="{{ competitors or '' }}">

    <div class="row">
      <div class="col">
        <label>Region</label>
        <input type="text" name="region" value="{{ region or 'US' }}">
      </div>
      <div class="col">
        <label>Language</label>
        <input type="text" name="language" value="{{ language or 'English' }}">
      </div>
    </div>

    <div class="row">
      <div class="col">
        <label>Start date</label>
        <input type="date" name="start_date" value="{{ start_date or '' }}">
      </div>
      <div class="col">
        <label>End date</label>
        <input type="date" name="end_date" value="{{ end_date or '' }}">
      </div>
    </div>

    <div class="btns">
      <button type="submit">Preview Prompts</button>
      {% if prompts %}
        <button type="submit" name="action" value="run" class="secondary">Run Audit</button>
      {% endif %}
    </div>

    {% if prompts %}
      <div class="card">
        <h3>Prompt Pack (Auto‑generated)</h3>
        <p class="muted">These are the standardized prompts currently used by the CLI runner. Editing is for validation only in this MVP (override wiring is planned).</p>
        <textarea name="prompts" rows="8">{{ prompts }}</textarea>
        <p class="muted">Note: The current CLI runner uses its internal prompt pack and a time hint. Custom overrides are coming in a next iteration.</p>
      </div>
    {% endif %}
  </form>

  {% if report %}
    <div class="card">
      <h3>Report</h3>
      <ul>
        <li>HTML: <a href="{{ url_for('serve_report', filename=report['html_name']) }}" target="_blank">{{ report['html_name'] }}</a></li>
        <li>CSV: <a href="{{ url_for('serve_report', filename=report['csv_name']) }}" target="_blank">{{ report['csv_name'] }}</a></li>
      </ul>
      <div class="muted">Inline preview:</div>
      <iframe src="{{ url_for('serve_report', filename=report['html_name']) }}" style="width:100%; height:600px; border:1px solid #eee; border-radius:8px;"></iframe>
    </div>
  {% endif %}

  <div class="card">
    <h3>Engine Keys (Env)</h3>
    <ul class="muted">
      <li>PERPLEXITY_API_KEY: {{ 'SET' if env_flags.perplexity else 'NOT SET' }}</li>
      <li>BRAVE_API_KEY: {{ 'SET' if env_flags.brave else 'NOT SET' }}</li>
      <li>SERPAPI_API_KEY: {{ 'SET' if env_flags.serp else 'NOT SET' }}</li>
      <li>OPENAI_API_KEY (ChatGPT): {{ 'SET' if env_flags.openai else 'NOT SET' }}</li>
      <li>ANTHROPIC_API_KEY (Claude): {{ 'SET' if env_flags.anthropic else 'NOT SET' }}</li>
    </ul>
  </div>
</body>
</html>
"""

def _build_time_hint(start_date: str, end_date: str) -> str:
    sd = (start_date or "").strip()
    ed = (end_date or "").strip()
    if sd and ed:
        # Format “YYYY-MM-DD to YYYY-MM-DD”
        return f"{sd} to {ed}"
    if sd:
        return f"from {sd}"
    if ed:
        return f"up to {ed}"
    return ""

def _build_prompts_preview(brand, competitors_csv, region, language, time_hint):
    """
    Build intelligent prompts preview using the same system as the CLI runner
    """
    try:
        # Import intelligent prompt system
        from intelligent_prompts import build_intelligent_prompt_pack
        
        # Get OpenAI key for brand analysis
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        # Build intelligent prompts
        competitors = [c.strip() for c in (competitors_csv or "").split(",") if c.strip()]
        prompts, brand_analysis = build_intelligent_prompt_pack(
            brand, competitors, region, language, time_hint or "", openai_key
        )
        
        # Add industry context to the preview
        industry = brand_analysis.get('industry', 'Unknown Industry')
        key_attributes = brand_analysis.get('key_attributes', [])
        
        prompt_text = f"# Industry Analysis: {industry}\n"
        if key_attributes:
            prompt_text += f"# Key Attributes: {', '.join(key_attributes)}\n"
        prompt_text += f"# Generated {len(prompts)} personalized prompts:\n\n"
        prompt_text += "\n".join(prompts)
        
        return prompt_text
        
    except Exception as e:
        print(f"Intelligent prompt preview failed: {e}")
        # Fallback to basic prompts
        return _build_basic_prompts_preview(brand, competitors_csv, region, language, time_hint)

def _build_basic_prompts_preview(brand, competitors_csv, region, language, time_hint):
    """
    Fallback basic prompt preview
    """
    in_region = f"in {region}" if region else ""
    lang_hint = f"Respond in {language}." if language else ""
    time_suffix = f" Focus on {time_hint}." if (time_hint and time_hint.strip()) else ""
    comps = [c.strip() for c in (competitors_csv or "").split(",") if c.strip()]
    
    # Basic industry detection
    brand_lower = brand.lower()
    if any(term in brand_lower for term in ["food", "ham", "chicken", "turkey", "meat", "restaurant"]):
        industry_type = "food companies"
        attribute_queries = [
            f"best premium food brands {in_region}. {lang_hint}{time_suffix}",
            f"highest quality food brands {in_region}. {lang_hint}{time_suffix}",
        ]
    elif any(term in brand_lower for term in ["tech", "software", "app", "digital", "ai"]):
        industry_type = "technology companies"
        attribute_queries = [
            f"most innovative tech companies {in_region}. {lang_hint}{time_suffix}",
            f"leading software companies {in_region}. {lang_hint}{time_suffix}",
        ]
    elif any(term in brand_lower for term in ["bank", "financial", "invest", "capital"]):
        industry_type = "financial services companies"
        attribute_queries = [
            f"leading investment firms {in_region}. {lang_hint}{time_suffix}",
            f"most trusted financial institutions {in_region}. {lang_hint}{time_suffix}",
        ]
    else:
        industry_type = "companies in this industry"
        attribute_queries = [
            f"top brands in this market {in_region}. {lang_hint}{time_suffix}",
            f"most trusted companies {in_region}. {lang_hint}{time_suffix}",
        ]
    
    presence = [
        f"Tell me about {brand}. {lang_hint}{time_suffix}",
        f"Please tell me about recent news from {brand}.{(' ' + lang_hint) if lang_hint else ''}{time_suffix}",
    ]
    
    industry_prompts = [
        f"Who are the top {industry_type} {in_region}? {lang_hint}{time_suffix}",
    ] + attribute_queries[:2]
    
    comparative = []
    for c in comps[:2]:
        comparative.append(f"Compare {brand} and {c}. {lang_hint}{time_suffix}")
    
    prompts = presence + industry_prompts + comparative
    return f"# Enhanced prompts based on detected industry context:\n\n" + "\n".join(prompts)

@app.route("/", methods=["GET", "POST"])
def index():
    ctx = {
        "brand": request.form.get("brand", ""),
        "competitors": request.form.get("competitors", ""),
        "region": request.form.get("region", "US"),
        "language": request.form.get("language", "English"),
        "start_date": request.form.get("start_date", ""),
        "end_date": request.form.get("end_date", ""),
        "prompts": None,
        "report": None,
        "env_flags": type("Env", (), {
            "perplexity": bool(os.environ.get("PERPLEXITY_API_KEY")),
            "brave": bool(os.environ.get("BRAVE_API_KEY")),
            "serp": bool(os.environ.get("SERPAPI_API_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        })()
    }

    if request.method == "POST":
        action = request.form.get("action", "preview")
        brand = ctx["brand"].strip()
        if not brand:
            flash("Brand is required")
            return render_template_string(TPL_INDEX, **ctx)

        time_hint = _build_time_hint(ctx["start_date"], ctx["end_date"])

        if action == "preview":
            ctx["prompts"] = _build_prompts_preview(brand, ctx["competitors"], ctx["region"], ctx["language"], time_hint)
            return render_template_string(TPL_INDEX, **ctx)

        if action == "run":
            # Build command to invoke CLI runner
            competitors_csv = ctx["competitors"]
            posted_prompts_text = request.form.get("prompts", "")
            override_list = []
            if posted_prompts_text:
                # Extract prompts from textarea, ignoring comment/header lines
                override_list = [ln.strip() for ln in posted_prompts_text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
            prompts_arg = ""
            if override_list:
                try:
                    import json as _json
                    prompts_arg = f" --prompts_json {shlex.quote(_json.dumps(override_list))}"
                except Exception:
                    prompts_arg = ""
            cmd = f"python3 run_audit.py --brand {shlex.quote(brand)} --competitors {shlex.quote(competitors_csv)} --region {shlex.quote(ctx['region'])} --language {shlex.quote(ctx['language'])} --time_hint {shlex.quote(time_hint)}{prompts_arg}"
            env = os.environ.copy()
            # Add API keys to environment for web execution
            env.update({
                "PERPLEXITY_API_KEY": os.environ.get("PERPLEXITY_API_KEY", ""),
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "")
            })
            # Ensure report directory exists
            os.makedirs(REPORTS_DIR, exist_ok=True)
            try:
                proc = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True, timeout=900)
                out = (proc.stdout or "") + "\n" + (proc.stderr or "")
                # parse lines like: HTML: path ... and CSV: path ...
                html_path = None
                csv_path = None
                for line in out.splitlines():
                    if line.strip().startswith("HTML: "):
                        html_path = line.strip().split("HTML: ", 1)[1].strip()
                    if line.strip().startswith("CSV: "):
                        csv_path = line.strip().split("CSV: ", 1)[1].strip()
                if proc.returncode != 0:
                    flash("Runner returned a non‑zero exit code. See console output below.")
                    flash(f"<pre>{out}</pre>")
                elif not html_path or not csv_path:
                    flash("Could not locate generated HTML/CSV paths in runner output.")
                    flash(f"<pre>{out}</pre>")
                else:
                    # Convert to filenames served by /reports
                    html_name = os.path.basename(html_path)
                    csv_name = os.path.basename(csv_path)
                    ctx["report"] = {"html_name": html_name, "csv_name": csv_name}
            except subprocess.TimeoutExpired:
                flash("Run timed out. Please try again with fewer prompts or check API quotas.")
            except Exception as e:
                flash(f"Error executing runner: {e}")

            return render_template_string(TPL_INDEX, **ctx)

    return render_template_string(TPL_INDEX, **ctx)

@app.route("/reports/<path:filename>")
def serve_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=False)

@app.route("/lead-gen", methods=["GET", "POST"])
def lead_gen():
    """Lead generation audit form and results"""
    if request.method == "GET":
        return render_template_string(TPL_LEAD_GEN_FORM)
    
    # POST - Run the audit
    brand = request.form.get("brand", "").strip()
    email = request.form.get("email", "").strip()
    competitors_csv = request.form.get("competitors", "").strip()
    sample_query = request.form.get("sample_query", "").strip()
    
    if not brand or not email or not sample_query:
        flash("Brand, email, and sample query are required")
        return render_template_string(TPL_LEAD_GEN_FORM)
    
    # Parse competitors
    competitors = [c.strip() for c in competitors_csv.split(",") if c.strip()]
    
    try:
        # Run the simple audit
        from simple_lead_auditor import SimpleLeadAuditor
        
        auditor = SimpleLeadAuditor(brand, competitors, sample_query, email)
        summary = auditor.run_audit()
        files = auditor.save_results()
        
        # Store results path for CSV download
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        # Render results template
        from flask import render_template
        return render_template(
            'lead_gen_results.html',
            summary=summary,
            csv_download_url=f"/download-sample/{files['timestamp']}/{os.path.basename(files['csv'])}"
        )
        
    except Exception as e:
        flash(f"Error running audit: {e}")
        return render_template_string(TPL_LEAD_GEN_FORM)

@app.route("/download-sample/<timestamp>/<filename>")
def download_sample(timestamp, filename):
    """Download sample CSV file"""
    return send_from_directory('lead_audits', filename, as_attachment=True)

@app.route("/download-sample/raw/<filename>")
def download_sample_raw(filename):
    """Alias route for legacy/raw download links"""
    return send_from_directory('lead_audits', filename, as_attachment=True)

@app.route("/simple-audit", methods=["GET", "POST"])
def simple_audit():
    """Simplified 3-step audit: Step 1: Brand + Query → Step 2: Review Competitors → Step 3: Review Queries → Run"""
    if request.method == "GET":
        return render_template_string(TPL_SIMPLE_AUDIT_STEP1)
    
    action = request.form.get("action", "step1")
    
    if action == "step1":
        # Step 1 → Step 2: Infer competitors
        brand = request.form.get("brand", "").strip()
        general_query = request.form.get("general_query", "").strip()
        
        if not brand or not general_query:
            flash("Both brand name and general query are required")
            return render_template_string(TPL_SIMPLE_AUDIT_STEP1)
        
        try:
            from simple_raw_auditor import infer_competitors
            
            openai_key = os.environ.get('OPENAI_API_KEY')
            analysis = infer_competitors(brand, openai_key)
            
            # Render step 2 with competitors
            return render_template_string(
                TPL_SIMPLE_AUDIT_STEP2,
                brand=brand,
                general_query=general_query,
                competitors=analysis.get('competitors', []),
                industry=analysis.get('industry', 'Unknown')
            )
            
        except Exception as e:
            flash(f"Error detecting competitors: {e}")
            return render_template_string(TPL_SIMPLE_AUDIT_STEP1)
    
    elif action == "step2":
        # Step 2 → Step 3: Generate queries
        brand = request.form.get("brand", "").strip()
        general_query = request.form.get("general_query", "").strip()
        
        # Get edited competitors
        competitors = []
        for i in range(10):
            comp = request.form.get(f"competitor_{i}", "").strip()
            if comp:
                competitors.append(comp)
        
        try:
            from simple_raw_auditor import generate_queries
            
            openai_key = os.environ.get('OPENAI_API_KEY')
            prompts = generate_queries(brand, general_query, competitors, openai_key)
            
            # Render step 3 with queries
            return render_template_string(
                TPL_SIMPLE_AUDIT_STEP3,
                brand=brand,
                general_query=general_query,
                competitors=competitors,
                prompts=prompts
            )
            
        except Exception as e:
            flash(f"Error generating queries: {e}")
            import traceback
            traceback.print_exc()
            return render_template_string(TPL_SIMPLE_AUDIT_STEP1)
    
    elif action == "run":
        # Step 3 → Results: Run the audit
        brand = request.form.get("brand", "").strip()
        
        # Get competitors
        competitors = []
        for i in range(10):
            comp = request.form.get(f"competitor_{i}", "").strip()
            if comp:
                competitors.append(comp)
        
        # Get edited prompts
        prompts = []
        for i in range(10):
            prompt = request.form.get(f"prompt_{i}", "").strip()
            if prompt:
                prompts.append(prompt)
        
        if not brand or not prompts:
            flash("Brand and at least one prompt are required")
            return render_template_string(TPL_SIMPLE_AUDIT_STEP1)
        
        try:
            from simple_raw_auditor import SimpleRawAuditor
            
            # Run the audit
            auditor = SimpleRawAuditor(brand, competitors, prompts)
            results = auditor.run_audit()
            
            # Save CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            safe_brand = "".join(c for c in brand if c.isalnum() or c in (' ', '-', '_')).strip()
            csv_filename = f"{safe_brand}_raw_{timestamp}.csv"
            csv_path = f"lead_audits/{csv_filename}"
            auditor.to_csv(csv_path)
            
            # Render results
            return render_template_string(
                TPL_SIMPLE_AUDIT_RESULTS,
                brand=brand,
                competitors=competitors,
                prompts=prompts,
                results=results,
                csv_filename=csv_filename,
                csv_timestamp=timestamp
            )
            
        except Exception as e:
            flash(f"Error running audit: {e}")
            import traceback
            traceback.print_exc()
            return render_template_string(TPL_SIMPLE_AUDIT_STEP1)
    
    return render_template_string(TPL_SIMPLE_AUDIT_STEP1)

# Lead gen form template
TPL_LEAD_GEN_FORM = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Free AI Visibility Sample Audit</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .container {
      background: white;
      max-width: 600px;
      width: 100%;
      padding: 40px;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    h1 { color: #333; margin-bottom: 10px; font-size: 2rem; }
    .subtitle { color: #666; margin-bottom: 30px; font-size: 1.1rem; }
    label {
      display: block;
      margin-top: 20px;
      font-weight: 600;
      color: #333;
      margin-bottom: 8px;
    }
    input, textarea {
      width: 100%;
      padding: 12px;
      border: 2px solid #ddd;
      border-radius: 6px;
      font-size: 1rem;
      transition: border-color 0.3s;
    }
    input:focus, textarea:focus {
      outline: none;
      border-color: #667eea;
    }
    textarea { resize: vertical; min-height: 80px; }
    .help-text {
      font-size: 0.85rem;
      color: #999;
      margin-top: 5px;
    }
    button {
      width: 100%;
      padding: 15px;
      margin-top: 30px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 1.1rem;
      font-weight: bold;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .notice {
      background: #e3f2fd;
      padding: 15px;
      border-radius: 6px;
      margin-bottom: 20px;
      border-left: 4px solid #2196f3;
    }
    .notice strong { color: #1976d2; }
    .flash {
      background: #ffebee;
      color: #c62828;
      padding: 15px;
      border-radius: 6px;
      margin-bottom: 20px;
      border-left: 4px solid #c62828;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔍 Free AI Visibility Audit</h1>
    <p class="subtitle">See how AI platforms recommend YOUR brand</p>
    
    <div class="notice">
      <strong>Sample Analysis</strong><br>
      Get a free snapshot with 5 queries across 4 AI platforms (ChatGPT, Claude, Perplexity, Gemini).
      Takes ~2-3 minutes to run.
    </div>
    
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash">
          {% for m in messages %}{{ m }}{% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    
    <form method="post">
      <label>Your Brand *</label>
      <input type="text" name="brand" required placeholder="e.g., ACME Corp">
      
      <label>Your Email *</label>
      <input type="email" name="email" required placeholder="your@email.com">
      <div class="help-text">We'll send you the full results</div>
      
      <label>Top 3 Competitors (comma-separated)</label>
      <input type="text" name="competitors" placeholder="e.g., Dunder Mifflin, Wayne Enterprises, Stark Industries">
      <div class="help-text">Optional but recommended for competitive analysis</div>
      
      <label>Sample Query *</label>
      <textarea name="sample_query" required placeholder="What are the best widgets for holiday gift giving?"></textarea>
      <div class="help-text">A question your customers might ask AI platforms</div>
      
      <button type="submit">🚀 Run Free Sample Audit</button>
    </form>
    
    <p style="text-align: center; margin-top: 30px; color: #999; font-size: 0.9rem;">
      Powered by <strong>Innate C3</strong> | No credit card required
    </p>
  </div>
</body>
</html>
"""

# Simple Audit Templates
TPL_SIMPLE_AUDIT_STEP1 = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Simple AI Audit - Step 1</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
    h1 { color: #333; }
    label { display: block; margin-top: 20px; font-weight: bold; }
    input, textarea { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; }
    textarea { min-height: 80px; }
    button { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 10px; }
    button:hover { background: #0056b3; }
    .flash { background: #ffebee; color: #c62828; padding: 10px; margin: 10px 0; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Simple AI Visibility Audit</h1>
  <p>Step 1: Enter your brand and a query to test</p>
  
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="flash">{% for m in messages %}{{ m }}{% endfor %}</div>
    {% endif %}
  {% endwith %}
  
  <form method="post">
    <input type="hidden" name="action" value="step1">
    
    <label>1. Brand Name</label>
    <input type="text" name="brand" placeholder="e.g., HoneyBaked Ham" required>
    
    <label>2. General Query to Test</label>
    <textarea name="general_query" placeholder="e.g., What are the best holiday hams?" required></textarea>
    
    <button type="submit">Detect Competitors →</button>
  </form>
</body>
</html>
"""

TPL_SIMPLE_AUDIT_STEP2 = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Simple AI Audit - Step 2</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; }
    h1 { color: #333; }
    h2 { color: #666; margin-top: 20px; }
    input { width: 100%; padding: 10px; margin: 5px 0; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; }
    button { padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }
    button:hover { background: #218838; }
    .section { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 4px; }
    .help { color: #666; font-size: 13px; font-style: italic; margin-bottom: 10px; }
    .info { background: #e3f2fd; padding: 12px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #2196f3; }
  </style>
</head>
<body>
  <h1>Step 2: Review Detected Competitors</h1>
  
  <div class="info">
    <strong>Brand:</strong> {{ brand }}<br>
    <strong>Your Query:</strong> "{{ general_query }}"<br>
    <strong>Industry:</strong> {{ industry }}
  </div>
  
  <form method="post">
    <input type="hidden" name="action" value="step2">
    <input type="hidden" name="brand" value="{{ brand }}">
    <input type="hidden" name="general_query" value="{{ general_query }}">
    
    <div class="section">
      <h2>AI-Detected Competitors</h2>
      <p class="help">Add, remove, or edit competitors as needed</p>
      {% for comp in competitors %}
        <input type="text" name="competitor_{{ loop.index0 }}" value="{{ comp }}">
      {% endfor %}
      {% for i in range(3 - competitors|length) %}
        <input type="text" name="competitor_{{ competitors|length + i }}" placeholder="Additional competitor...">
      {% endfor %}
    </div>
    
    <button type="submit">Generate Test Queries →</button>
  </form>
</body>
</html>
"""

TPL_SIMPLE_AUDIT_STEP3 = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Simple AI Audit - Step 3</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
    h1 { color: #333; }
    h2 { color: #666; margin-top: 20px; }
    textarea { width: 100%; padding: 10px; margin: 5px 0; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; min-height: 60px; font-family: Arial, sans-serif; }
    button { padding: 12px 24px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }
    button:hover { background: #c82333; }
    .section { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 4px; }
    .help { color: #666; font-size: 13px; font-style: italic; margin-bottom: 10px; }
    .info { background: #e3f2fd; padding: 12px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #2196f3; }
    .warning { background: #fff3cd; padding: 12px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #ffc107; }
  </style>
</head>
<body>
  <h1>Step 3: Review Generated Queries</h1>
  
  <div class="info">
    <strong>Brand:</strong> {{ brand }}<br>
    <strong>Your Query:</strong> "{{ general_query }}"<br>
    <strong>Competitors:</strong> {{ ', '.join(competitors) if competitors else 'None' }}
  </div>
  
  <div class="warning">
    <strong>Ready to run!</strong> These 5 queries will be tested across ChatGPT, Claude, Perplexity, and Gemini (20 total API calls).
    Takes ~2-3 minutes.
  </div>
  
  <form method="post">
    <input type="hidden" name="action" value="run">
    <input type="hidden" name="brand" value="{{ brand }}">
    
    {% for comp in competitors %}
      <input type="hidden" name="competitor_{{ loop.index0 }}" value="{{ comp }}">
    {% endfor %}
    
    <div class="section">
      <h2>AI-Generated Test Queries</h2>
      <p class="help">Edit any query before running the audit</p>
      {% for prompt in prompts %}
        <textarea name="prompt_{{ loop.index0 }}">{{ prompt }}</textarea>
      {% endfor %}
    </div>
    
    <button type="submit">🚀 Run Full Audit (~2-3 min)</button>
  </form>
</body>
</html>
"""

TPL_SIMPLE_AUDIT_RESULTS = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Simple AI Audit - Results</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; padding: 20px; }
    h1 { color: #333; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 12px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f8f9fa; font-weight: bold; position: sticky; top: 0; }
    tr:nth-child(even) { background: #f8f9fa; }
    .yes { color: #28a745; font-weight: bold; }
    .no { color: #dc3545; }
    .response { max-width: 600px; font-size: 11px; color: #444; max-height: 100px; overflow-y: auto; }
    .citations { font-size: 11px; color: #666; }
    .download { margin: 20px 0; }
    .download a { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
    .download a:hover { background: #0056b3; }
    .info { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 15px 0; }
  </style>
</head>
<body>
  <h1>Raw Audit Results: {{ brand }}</h1>
  
  <div class="info">
    <strong>Competitors Tracked:</strong> {{ ', '.join(competitors) if competitors else 'None' }}<br>
    <strong>Queries Tested:</strong> {{ prompts|length }}<br>
    <strong>Total Tests:</strong> {{ results|length }} ({{ prompts|length }} queries × 4 platforms)
  </div>
  
    <div class="download">
    <a href="/download-sample/{{ csv_timestamp }}/{{ csv_filename }}">⬇ Download Complete CSV with Full Responses & Citations</a>
  </div>
  
  <table>
    <thead>
      <tr>
        <th style="width: 180px;">Query</th>
        <th style="width: 80px;">Platform</th>
        <th style="width: 80px;">Brand Mentioned</th>
        <th style="width: 120px;">Competitors Mentioned</th>
        <th style="width: 150px;">Actual Citations (URLs)</th>
        <th style="width: 150px;">Inferred Citations</th>
        <th>Full Response (excerpt)</th>
      </tr>
    </thead>
    <tbody>
      {% for result in results %}
      <tr>
        <td>{{ result.query[:60] }}{% if result.query|length > 60 %}...{% endif %}</td>
        <td><strong>{{ result.platform }}</strong></td>
        <td class="{% if result.brand_mentioned %}yes{% else %}no{% endif %}">
          {% if result.brand_mentioned %}✓ YES{% else %}✗ NO{% endif %}
        </td>
        <td>{{ ', '.join(result.competitors_mentioned) if result.competitors_mentioned else '-' }}</td>
        <td class="citations">
          {% if result.actual_citations %}
            {% for cite in result.actual_citations %}
              <a href="{{ cite }}" target="_blank" style="display: block; margin: 2px 0; font-size: 10px;">{{ cite }}</a>
            {% endfor %}
          {% else %}
            None
          {% endif %}
        </td>
        <td class="citations">
          {% if result.inferred_citations %}
            {{ ', '.join(result.inferred_citations) }}
          {% else %}
            None
          {% endif %}
        </td>
        <td class="response">{{ result.full_response[:300] }}{% if result.full_response|length > 300 %}...{% endif %}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  
    <div class="download">
    <a href="/download-sample/{{ csv_timestamp }}/{{ csv_filename }}">⬇ Download CSV (includes full responses & all citation URLs)</a>
  </div>
  
  <p style="margin-top: 40px; color: #666; font-size: 14px;">
    <a href="/simple-audit">← Run Another Audit</a>
  </p>
</body>
</html>
"""

def generate_smart_query_suggestion(brand: str, openai_key: str) -> str:
    """Generate a smart, brand-appropriate unbiased query suggestion"""
    if not openai_key:
        return "What are the best options in this category?"
    
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
                    "content": f"""Analyze the brand "{brand}" and generate ONE unbiased query that a consumer might ask when researching this category.

CRITICAL: The query must be GENERIC and NOT mention "{brand}" or any specific brand name.

Examples:
- UNIQLO → "What's the most sustainable fast fashion brand?"
- Tesla → "What's the best electric vehicle for families?"
- Nike → "Which athletic brands offer the best performance gear?"
- Starbucks → "Where should I get the best coffee?"

Generate a similar generic question for {brand}. Return ONLY the question, nothing else."""
                }],
                "max_tokens": 100,
                "temperature": 0.7
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            query = data['choices'][0]['message']['content'].strip()
            # Clean up any quotes
            query = query.strip('"\'')
            return query
        
    except Exception as e:
        logger.error(f"Error generating query suggestion: {e}")
    
    return f"What are the best options for {brand.lower()} customers?"

@app.route("/typeform-audit", methods=["GET", "POST"])
def typeform_audit():
    """Typeform-style audit flow with elegant UX"""
    if request.method == "GET":
        return render_template_string(TPL_TYPEFORM_AUDIT)
    
    # Handle AJAX API calls
    action = request.json.get('action') if request.is_json else None
    
    if action == 'suggest_query':
        brand = request.json.get('brand', '')
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        suggestion = generate_smart_query_suggestion(brand, openai_key)
        return {'suggestion': suggestion}
    
    elif action == 'detect_competitors':
        brand = request.json.get('brand', '')
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        from simple_raw_auditor import infer_competitors
        result = infer_competitors(brand, openai_key)
        return {'competitors': result.get('competitors', []), 'industry': result.get('industry', 'Unknown')}
    
    elif action == 'generate_queries':
        brand = request.json.get('brand', '')
        query = request.json.get('query', '')
        competitors = request.json.get('competitors', [])
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        from simple_raw_auditor import generate_queries
        prompts = generate_queries(brand, query, competitors, openai_key)
        return {'queries': prompts}
    
    elif action == 'run_audit':
        brand = request.json.get('brand', '')
        competitors = request.json.get('competitors', [])
        prompts = request.json.get('prompts', [])
        
        from simple_raw_auditor import SimpleRawAuditor
        auditor = SimpleRawAuditor(brand, competitors, prompts)
        results = auditor.run_audit()
        
        # Save CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_brand = "".join(c for c in brand if c.isalnum() or c in (' ', '-', '_')).strip()
        csv_filename = f"{safe_brand}_audit_{timestamp}.csv"
        csv_path = f"lead_audits/{csv_filename}"
        auditor.to_csv(csv_path)
        
        # Analyze results for dashboard
        analysis = analyze_audit_results(brand, competitors, results)
        analysis['csv_filename'] = csv_filename
        
        return analysis
    
    return {'error': 'Invalid action'}, 400

def analyze_audit_results(brand, competitors, results):
    """Analyze audit results to create dashboard data with PR scoring"""
    
    # Import PR analysis functions
    try:
        from pr_analysis_backend import (
            classify_outlet_tier,
            calculate_pr_opportunity_score,
            enhance_analysis_with_pr_scoring
        )
        pr_backend_available = True
    except ImportError:
        pr_backend_available = False
    
    def _normalize_domain(value: str) -> str:
        try:
            from urllib.parse import urlparse
            v = (value or "").strip().lower()
            if not v:
                return ""
            
            # First, try to extract domain from full URLs
            if '://' in v or v.startswith('www.'):
                netloc = urlparse(v).netloc or urlparse("https://" + v).netloc or v
            else:
                # For plain text citations like "McMenamins" or brand names
                # Check if it looks like a domain
                if '.' in v:
                    netloc = v
                else:
                    # It's likely a brand name without .com - add .com for consistency
                    # This helps combine "mcmenamins" with "mcmenamins.com"
                    netloc = v + '.com' if not any(ext in v for ext in ['.com', '.org', '.net', '.edu']) else v
            
            # Strip common prefixes and ports
            if netloc.startswith("www."):
                netloc = netloc[4:]
            if netloc.startswith("m."):
                netloc = netloc[2:]
            if netloc.startswith("mobile."):
                netloc = netloc[7:]
            netloc = netloc.split(":")[0]  # Remove port
            
            # Clean up the domain
            netloc = netloc.strip('/')
            
            return netloc or v
        except Exception:
            # For non-URL text, normalize and add .com if it looks like a brand
            v = (value or "").lower().strip()
            if v and not '.' in v and len(v) > 2:
                # Likely a brand name without extension
                return v + '.com'
            return v

    def _group_for_domain(domain: str, brand_name: str) -> str:
        try:
            d = (domain or "").lower()
            b = (brand_name or "").lower().replace(" ", "")
            if b and b in d:
                return "brand_official"
            if any(k in d for k in ["espn", "sport", "nba", "athletic", "bleacher", "foxsports", "cbssports", "si.com", "sportingnews"]):
                return "sports_entertainment"
            if any(k in d for k in ["cordcut", "cable", "stream", "streaming", "cord", "theverge", "techcrunch", "tomsguide", "cnet", "android", "appleinsider", "gsmarena", "xfinity", "directv"]):
                return "tech_streaming"
            try:
                from run_audit import classify_domain as _classify_domain
                cls = _classify_domain(d)
                if cls in ("industry_trade",):
                    return "industry_trade"
                if cls in ("pr",):
                    return "pr_wire"
                if cls in ("editorial_tier1", "food_tier1"):
                    return "tier1_editorial"
                if cls in ("food_tier2", "editorial"):
                    return "editorial"
            except Exception:
                pass
            return "other"
        except Exception:
            return "other"
    total_results = len(results)
    brand_mentions = sum(1 for r in results if r.get('brand_mentioned', False))
    
    # Platform breakdown
    platform_stats = {}
    for result in results:
        platform = result['platform']
        if platform not in platform_stats:
            platform_stats[platform] = {'total': 0, 'brand_mentions': 0, 'citations': 0}
        platform_stats[platform]['total'] += 1
        if result.get('brand_mentioned'):
            platform_stats[platform]['brand_mentions'] += 1
        platform_stats[platform]['citations'] += len(result.get('actual_citations', []))
    
    # Competitor analysis
    competitor_mentions = {}
    for comp in competitors:
        competitor_mentions[comp] = sum(1 for r in results if comp in r.get('competitors_mentioned', []))
    
    # Sort competitors by mentions
    sorted_competitors = sorted(competitor_mentions.items(), key=lambda x: x[1], reverse=True)
    
    # Calculate rankings
    all_brands = {brand: brand_mentions}
    all_brands.update(competitor_mentions)
    rankings = sorted(all_brands.items(), key=lambda x: x[1], reverse=True)
    brand_rank = next(i + 1 for i, (b, _) in enumerate(rankings) if b == brand)
    
    # Process all citation types: actual URLs, inferred citations, and recommended resources
    citation_sources = {}
    
    for result in results:
        # Process actual URL citations (from Perplexity)
        for citation in result.get('actual_citations', []):
            domain = _normalize_domain(citation)
            if domain:
                if domain not in citation_sources:
                    citation_sources[domain] = {
                        'total': 0, 
                        'brand_mentions': 0, 
                        'url_citations': 0,
                        'inferred_citations': 0,
                        'recommended': 0
                    }
                citation_sources[domain]['total'] += 1
                citation_sources[domain]['url_citations'] += 1
                if result.get('brand_mentioned'):
                    citation_sources[domain]['brand_mentions'] += 1
        
        # Process inferred citations ("According to X")
        for inferred in result.get('inferred_citations', []):
            # Clean and normalize the source name or URL
            domain = _normalize_domain(inferred)
            
            if domain:
                if domain not in citation_sources:
                    citation_sources[domain] = {
                        'total': 0, 
                        'brand_mentions': 0, 
                        'url_citations': 0,
                        'inferred_citations': 0,
                        'recommended': 0
                    }
                citation_sources[domain]['total'] += 1
                citation_sources[domain]['inferred_citations'] += 1
                if result.get('brand_mentioned'):
                    citation_sources[domain]['brand_mentions'] += 1
        
        # Process recommended resources ("Visit X", "Check Y")
        for recommended in result.get('recommended_resources', []):
            # Clean and normalize
            resource = _normalize_domain(recommended)
            
            if resource:
                if resource not in citation_sources:
                    citation_sources[resource] = {
                        'total': 0, 
                        'brand_mentions': 0, 
                        'url_citations': 0,
                        'inferred_citations': 0,
                        'recommended': 0
                    }
                citation_sources[resource]['total'] += 1
                citation_sources[resource]['recommended'] += 1
                if result.get('brand_mentioned'):
                    citation_sources[resource]['brand_mentions'] += 1
    
    # Sort by total citations and prepare for display
    top_sources = sorted(citation_sources.items(), key=lambda x: x[1]['total'], reverse=True)[:20]  # Increased to 20 for better PR analysis
    total_citations_count = sum(s['total'] for s in citation_sources.values())
    unique_outlets_count = len(citation_sources)
    
    # Prepare base analysis
    analysis = {
        'brand': brand,
        'total_queries': total_results // 4,  # Divide by 4 platforms
        'total_results': total_results,
        'brand_mentions': brand_mentions,
        'brand_mention_rate': round(brand_mentions / total_results * 100, 1) if total_results > 0 else 0,
        'brand_rank': brand_rank,
        'total_brands': len(rankings),
        'total_citations': total_citations_count,
        'total_unique_outlets': unique_outlets_count,
        'platform_stats': platform_stats,
        'competitor_mentions': dict(sorted_competitors),
        'rankings': rankings,
        'top_sources': [],
        'results': results
    }
    
    # Enhanced top sources with PR scoring if backend available
    for d, s in top_sources:
        source_data = {
            'domain': d, 
            'total': s['total'], 
            'brand_mentions': s['brand_mentions'], 
            'brand_share': round(s['brand_mentions'] / s['total'] * 100, 1) if s['total'] > 0 else 0,
            'url_citations': s.get('url_citations', 0),
            'inferred_citations': s.get('inferred_citations', 0),
            'recommended': s.get('recommended', 0),
            'group': _group_for_domain(d, brand)
        }
        
        # Add PR tier classification if backend available
        if pr_backend_available:
            source_data['tier'] = classify_outlet_tier(d)
            # Calculate PR opportunity score
            pr_score = calculate_pr_opportunity_score(s, brand)
            source_data['pr_score'] = pr_score['total']
            source_data['pr_priority'] = 'High' if pr_score['total'] >= 60 else 'Medium' if pr_score['total'] >= 30 else 'Low'
        
        analysis['top_sources'].append(source_data)
    
    # Enhance with full PR analysis if backend available
    if pr_backend_available:
        analysis = enhance_analysis_with_pr_scoring(analysis)
    
    return analysis

# Typeform-style audit template
TPL_TYPEFORM_AUDIT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Citation Audit | innate c3</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #000000;
            color: #E8E8E8;
            overflow-x: hidden;
        }
        
        .screen {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 2rem;
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.6s ease, transform 0.6s ease;
            position: absolute;
            width: 100%;
            left: 0;
            top: 0;
        }
        
        .screen.active {
            opacity: 1;
            transform: translateY(0);
            position: relative;
        }
        
        .screen.hidden {
            display: none;
        }
        
        .progress-bar {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: #1A1A1A;
            z-index: 1000;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #464A3F 0%, #5A5F53 100%);
            transition: width 0.3s ease;
        }
        
        .question-number {
            font-size: 0.9rem;
            color: #999999;
            margin-bottom: 1rem;
            font-weight: 300;
            letter-spacing: 1px;
        }
        
        .question-text {
            font-size: 2.5rem;
            font-weight: 300;
            color: #FFFFFF;
            margin-bottom: 2rem;
            max-width: 800px;
            text-align: center;
            line-height: 1.3;
        }
        
        .question-text .emoji {
            display: inline-block;
            margin-left: 0.5rem;
        }
        
        input[type="text"],
        textarea {
            width: 100%;
            max-width: 600px;
            padding: 1.25rem 1.5rem;
            font-size: 1.25rem;
            font-family: 'Roboto', sans-serif;
            background: #1A1A1A;
            border: 2px solid #2A2A2A;
            border-radius: 8px;
            color: #E8E8E8;
            transition: all 0.3s ease;
            font-weight: 300;
        }
        
        input[type="text"]:focus,
        textarea:focus {
            outline: none;
            border-color: #464A3F;
            background: #222222;
            box-shadow: 0 0 0 4px rgba(70, 74, 63, 0.1);
        }
        
        textarea {
            resize: vertical;
            min-height: 120px;
            line-height: 1.6;
        }
        
        .hint {
            font-size: 0.9rem;
            color: #666666;
            margin-top: 0.75rem;
            font-weight: 300;
        }
        
        .button {
            padding: 1rem 2.5rem;
            font-size: 1.1rem;
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            background: linear-gradient(135deg, #464A3F 0%, #5A5F53 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 2rem;
            letter-spacing: 0.5px;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(70, 74, 63, 0.3);
        }
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .button-secondary {
            background: transparent;
            border: 2px solid #464A3F;
            color: #464A3F;
            margin-right: 1rem;
        }
        
        .button-secondary:hover {
            background: rgba(70, 74, 63, 0.1);
        }
        
        .competitor-list {
            width: 100%;
            max-width: 600px;
            margin: 2rem 0;
        }
        
        .competitor-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: #1A1A1A;
            border-radius: 8px;
            border: 1px solid #2A2A2A;
        }
        
        .competitor-item input {
            flex: 1;
            margin: 0;
            padding: 0.75rem 1rem;
            font-size: 1rem;
        }
        
        .remove-btn {
            padding: 0.5rem 1rem;
            background: #4D1F1F;
            color: #EF5350;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .add-btn {
            padding: 0.75rem 1.5rem;
            background: transparent;
            border: 2px dashed #464A3F;
            color: #464A3F;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 1rem;
        }
        
        .query-item {
            margin-bottom: 1.5rem;
        }
        
        .query-item label {
            display: block;
            font-size: 0.9rem;
            color: #999999;
            margin-bottom: 0.5rem;
            font-weight: 400;
        }
        
        .processing-screen {
            text-align: center;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 3px solid #2A2A2A;
            border-top-color: #464A3F;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .processing-message {
            font-size: 1.5rem;
            color: #CCCCCC;
            margin: 1rem 0;
            min-height: 2rem;
            font-weight: 300;
        }
        
        .processing-emoji {
            font-size: 2rem;
            margin-right: 0.5rem;
        }
        
        .results-dashboard {
            max-width: 1400px;
            width: 100%;
            padding: 2rem;
            margin: 0 auto;
        }
        
        .results-header {
            background: linear-gradient(135deg, #464A3F 0%, #5A5F53 100%);
            padding: 3rem 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .results-header h1 {
            font-size: 2.5rem;
            font-weight: 300;
            margin-bottom: 0.5rem;
        }
        
        .results-header .subtitle {
            font-size: 1rem;
            opacity: 0.9;
            font-weight: 300;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: #1A1A1A;
            padding: 2rem;
            border-radius: 8px;
            border-top: 3px solid #464A3F;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #999999;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.75rem;
            font-weight: 500;
        }
        
        .metric-value {
            font-size: 3rem;
            font-weight: 300;
            color: #464A3F;
            margin-bottom: 0.5rem;
        }
        
        .metric-sublabel {
            font-size: 0.9rem;
            color: #666666;
            font-weight: 300;
        }
        
        .section {
            background: #1A1A1A;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 400;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #2A2A2A;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            padding: 1rem;
            background: #222222;
            font-weight: 500;
            font-size: 0.85rem;
            color: #999999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        td {
            padding: 1rem;
            border-bottom: 1px solid #2A2A2A;
            color: #CCCCCC;
        }
        
        tr:hover {
            background: #222222;
        }
        
        .rank-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-weight: 500;
            font-size: 0.85rem;
        }
        
        .rank-1 { background: #FFD700; color: #000; }
        .rank-2 { background: #C0C0C0; color: #000; }
        .rank-3 { background: #CD7F32; color: #FFF; }
        .rank-other { background: #464A3F; color: #E8E8E8; }
        
        .citation-count {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #464A3F;
            color: #FFF;
            border-radius: 4px;
            font-weight: 500;
        }
        
        .download-btn {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #B8C5CD;
            color: #000;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin-top: 1rem;
        }
        
        @media (max-width: 768px) {
            .question-text {
                font-size: 1.75rem;
            }
            
            input[type="text"],
            textarea {
                font-size: 1rem;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <div class="progress-bar">
        <div class="progress-fill" id="progressFill"></div>
    </div>
    
    <!-- Screen 1: Brand Name -->
    <div class="screen active" id="screen1">
        <div class="question-number">Question 1 of 4</div>
        <h1 class="question-text">Enter a brand name: <span class="emoji">💼</span></h1>
        <input type="text" id="brandInput" placeholder="e.g., Tesla, Patagonia, Apple" autofocus>
        <div class="hint">Press Enter ↵</div>
        <button class="button" onclick="nextScreen(2)">Continue</button>
    </div>
    
    <!-- Screen 2: Query -->
    <div class="screen" id="screen2">
        <div class="question-number">Question 2 of 4</div>
        <h1 class="question-text">What query should we test? <span class="emoji">🔍</span></h1>
        <textarea id="queryInput" placeholder="e.g., What are the best electric vehicles for families?"></textarea>
        <div class="hint">A question your customers might ask AI platforms</div>
        <div style="margin-top: 2rem;">
            <button class="button-secondary button" onclick="prevScreen(1)">Back</button>
            <button class="button" onclick="detectCompetitors()">Continue</button>
        </div>
    </div>
    
    <!-- Screen 3: Competitors -->
    <div class="screen" id="screen3">
        <div class="question-number">Question 3 of 4</div>
        <h1 class="question-text">Review your competitors <span class="emoji">🎯</span></h1>
        <div class="competitor-list" id="competitorList"></div>
        <button class="add-btn" onclick="addCompetitor()">+ Add competitor</button>
        <div style="margin-top: 2rem;">
            <button class="button-secondary button" onclick="prevScreen(2)">Back</button>
            <button class="button" onclick="generateQueries()">Continue</button>
        </div>
    </div>
    
    <!-- Screen 4: Queries -->
    <div class="screen" id="screen4">
        <div class="question-number">Question 4 of 4</div>
        <h1 class="question-text">Review test queries <span class="emoji">✏️</span></h1>
        <div style="max-width: 600px; width: 100%;" id="queryList"></div>
        <div style="margin-top: 2rem;">
            <button class="button-secondary button" onclick="prevScreen(3)">Back</button>
            <button class="button" onclick="runAudit()">Run Audit</button>
        </div>
    </div>
    
    <!-- Screen 5: Processing -->
    <div class="screen processing-screen" id="screen5">
        <div class="spinner"></div>
        <div class="processing-message" id="processingMessage">
            <span class="processing-emoji">🔄</span> Starting...
        </div>
        <div id="processingHint" class="hint">This will only take a moment...</div>
        <div id="progressInfo" style="display: none; margin-top: 2rem; max-width: 600px; width: 100%;">
            <div style="background: #2A2A2A; border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 1rem;">
                <div id="timeProgressBar" style="background: linear-gradient(90deg, #464A3F 0%, #5A5F53 100%); height: 100%; width: 0%; transition: width 0.5s ease;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; color: #999999; font-size: 0.9rem;">
                <span id="progressPercent">0%</span>
                <span id="timeRemaining">About 2 minutes remaining...</span>
            </div>
        </div>
    </div>
    
    <!-- Screen 6: Results -->
    <div class="screen" id="screen6">
        <div class="results-dashboard" id="resultsDashboard"></div>
    </div>
    
    <script>
        let currentScreen = 1;
        let appState = {
            brand: '',
            query: '',
            competitors: [],
            queries: [],
            results: null
        };
        
        const processingMessages = {
            detectCompetitors: [
                {emoji: '🔍', text: 'Researching competitors...'}
            ],
            generateQueries: [
                {emoji: '✏️', text: 'Generating test queries...'}
            ],
            runAudit: [
                {emoji: '🤖', text: 'Querying ChatGPT...'},
                {emoji: '💬', text: 'Querying Claude...'},
                {emoji: '🔮', text: 'Querying Gemini...'},
                {emoji: '🌐', text: 'Querying Perplexity...'},
                {emoji: '📊', text: 'Analyzing results...'},
                {emoji: '📝', text: 'Documenting citations...'},
                {emoji: '🔍', text: 'Identifying patterns...'},
                {emoji: '💡', text: 'Calculating metrics...'},
                {emoji: '✨', text: 'Generating dashboard...'}
            ]
        };
        
        let currentProcessStage = 'runAudit';
        let processStartTime = 0;
        let estimatedDuration = 150000; // 2.5 minutes in milliseconds
        
        // Enter key handlers
        document.getElementById('brandInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') nextScreen(2);
        });
        
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                detectCompetitors();
            }
        });
        
        function updateProgress() {
            const progress = (currentScreen / 6) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }
        
        function showScreen(screenNum) {
            document.querySelectorAll('.screen').forEach(s => {
                s.classList.remove('active');
                s.classList.add('hidden');
            });
            
            const screen = document.getElementById('screen' + screenNum);
            screen.classList.remove('hidden');
            
            setTimeout(() => {
                screen.classList.add('active');
            }, 50);
            
            currentScreen = screenNum;
            updateProgress();
        }
        
        function nextScreen(screenNum) {
            if (screenNum === 2) {
                appState.brand = document.getElementById('brandInput').value.trim();
                if (!appState.brand) {
                    alert('Please enter a brand name');
                    return;
                }
            }
            showScreen(screenNum);
        }
        
        function prevScreen(screenNum) {
            showScreen(screenNum);
        }
        
        async function detectCompetitors() {
            appState.query = document.getElementById('queryInput').value.trim();
            if (!appState.query) {
                alert('Please enter a query');
                return;
            }
            
            showScreen(5);
            currentProcessStage = 'detectCompetitors';
            
            // Hide progress bar for quick stages
            document.getElementById('progressInfo').style.display = 'none';
            document.getElementById('processingHint').textContent = 'This will only take a moment...';
            updateProcessingMessage('detectCompetitors', 0);
            
            try {
                const response = await fetch('/typeform-audit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: 'detect_competitors',
                        brand: appState.brand
                    })
                });
                
                const data = await response.json();
                appState.competitors = data.competitors || [];
                
                renderCompetitors();
                showScreen(3);
            } catch (error) {
                alert('Error detecting competitors: ' + error.message);
                showScreen(2);
            }
        }
        
        function renderCompetitors() {
            const list = document.getElementById('competitorList');
            list.innerHTML = '';
            
            appState.competitors.forEach((comp, i) => {
                const item = document.createElement('div');
                item.className = 'competitor-item';
                item.innerHTML = `
                    <input type="text" value="${comp}" onchange="updateCompetitor(${i}, this.value)">
                    <button class="remove-btn" onclick="removeCompetitor(${i})">Remove</button>
                `;
                list.appendChild(item);
            });
        }
        
        function updateCompetitor(index, value) {
            appState.competitors[index] = value;
        }
        
        function removeCompetitor(index) {
            appState.competitors.splice(index, 1);
            renderCompetitors();
        }
        
        function addCompetitor() {
            appState.competitors.push('');
            renderCompetitors();
            const inputs = document.querySelectorAll('.competitor-item input');
            inputs[inputs.length - 1].focus();
        }
        
        async function generateQueries() {
            showScreen(5);
            currentProcessStage = 'generateQueries';
            
            // Hide progress bar for quick stages
            document.getElementById('progressInfo').style.display = 'none';
            document.getElementById('processingHint').textContent = 'This will only take a moment...';
            updateProcessingMessage('generateQueries', 0);
            
            try {
                const response = await fetch('/typeform-audit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: 'generate_queries',
                        brand: appState.brand,
                        query: appState.query,
                        competitors: appState.competitors.filter(c => c.trim())
                    })
                });
                
                const data = await response.json();
                appState.queries = data.queries || [];
                
                renderQueries();
                showScreen(4);
            } catch (error) {
                alert('Error generating queries: ' + error.message);
                showScreen(3);
            }
        }
        
        function renderQueries() {
            const list = document.getElementById('queryList');
            list.innerHTML = '';
            
            appState.queries.forEach((query, i) => {
                const item = document.createElement('div');
                item.className = 'query-item';
                item.innerHTML = `
                    <label>Query ${i + 1}</label>
                    <textarea onchange="updateQuery(${i}, this.value)">${query}</textarea>
                `;
                list.appendChild(item);
            });
        }
        
        function updateQuery(index, value) {
            appState.queries[index] = value;
        }
        
        async function runAudit() {
            showScreen(5);
            startProcessingAnimation();
            
            try {
                const response = await fetch('/typeform-audit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: 'run_audit',
                        brand: appState.brand,
                        competitors: appState.competitors.filter(c => c.trim()),
                        prompts: appState.queries.filter(q => q.trim())
                    })
                });
                
                const data = await response.json();
                appState.results = data;
                
                renderResults(data);
                showScreen(6);
            } catch (error) {
                alert('Error running audit: ' + error.message);
                showScreen(4);
            }
        }
        
        let processingInterval;
        let progressInterval;
        
        function startProcessingAnimation() {
            currentProcessStage = 'runAudit';
            const messages = processingMessages.runAudit;
            let index = 0;
            
            // Show progress bar and update hint for longer audit process
            document.getElementById('progressInfo').style.display = 'block';
            document.getElementById('processingHint').textContent = 'This takes about 2-3 minutes';
            
            // Show first message immediately
            updateProcessingMessage(currentProcessStage, 0);
            
            // Start message rotation
            processingInterval = setInterval(() => {
                index = (index + 1) % messages.length;
                updateProcessingMessage(currentProcessStage, index);
            }, 15000); // 2.5 minutes / 9 messages ≈ 15 seconds per message
            
            // Start progress bar animation
            processStartTime = Date.now();
            estimatedDuration = 150000; // 2.5 minutes
            
            progressInterval = setInterval(() => {
                const elapsed = Date.now() - processStartTime;
                const progress = Math.min((elapsed / estimatedDuration) * 100, 99);
                const remaining = Math.max(0, Math.ceil((estimatedDuration - elapsed) / 1000));
                
                document.getElementById('timeProgressBar').style.width = progress + '%';
                document.getElementById('progressPercent').textContent = Math.round(progress) + '%';
                
                if (remaining > 60) {
                    const mins = Math.ceil(remaining / 60);
                    document.getElementById('timeRemaining').textContent = `About ${mins} minute${mins > 1 ? 's' : ''} remaining...`;
                } else if (remaining > 0) {
                    document.getElementById('timeRemaining').textContent = `Less than a minute remaining...`;
                } else {
                    document.getElementById('timeRemaining').textContent = 'Finishing up...';
                }
            }, 500);
        }
        
        function updateProcessingMessage(stage, index) {
            const messages = processingMessages[stage];
            if (!messages || index >= messages.length) return;
            
            const msg = messages[index];
            document.getElementById('processingMessage').innerHTML = 
                `<span class="processing-emoji">${msg.emoji}</span> ${msg.text}`;
        }
        
        function renderResults(data) {
            if (processingInterval) clearInterval(processingInterval);
            if (progressInterval) clearInterval(progressInterval);
            
            const dashboard = document.getElementById('resultsDashboard');
            
            // Header with Executive Summary
            let html = `
                <div class="results-header">
                    <div style="text-align: left; margin-bottom: 1.5rem; color: #B8C5CD; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">
                        ${data.brand} — AI Citation Analysis
                    </div>
                    <h1 style="margin-bottom: 0.5rem;">${data.brand} Citation Visibility Report</h1>
                    <div class="subtitle">${data.total_citations || data.total_results} Citations Analyzed | ${data.total_queries} Queries Tested | ${new Date().toLocaleDateString('en-US', {month: 'long', year: 'numeric'})}</div>
                </div>
                
                <div class="section">
                    <h3 style="font-size: 1.25rem; font-weight: 400; margin-bottom: 1rem;">Executive Summary</h3>
                    <p style="line-height: 1.8; color: #CCCCCC; margin-bottom: 1.5rem;">
                        ${data.brand} appears in <strong>${data.brand_mention_rate}%</strong> of queries tested, 
                        ranking <strong>#${data.brand_rank}</strong> among ${data.total_brands} brands analyzed. 
                        ${data.top_sources && data.top_sources.length > 0 ? 
                            `The analysis identified ${data.total_unique_outlets || data.top_sources.length} unique media outlets, 
                            with ${data.top_sources[0].domain} leading with ${data.top_sources[0].total} citations.` : 
                            'Analysis complete across all major AI platforms.'}
                    </p>
                </div>
            `;
            
            // Key Metrics Grid (6 boxes like NBA page)
            const gapToLeader = data.rankings && data.rankings.length > 0 ? 
                Math.round((data.rankings[0][1] / data.total_results * 100) - data.brand_mention_rate) : 0;
            
            html += `<div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">`;
            html += `
                <div class="metric-card">
                    <div class="metric-label">${data.brand} Mention Rate</div>
                    <div class="metric-value">${data.brand_mention_rate}%</div>
                    <div class="metric-sublabel">${data.brand_rank > 1 ? getRankSuffix(data.brand_rank) + ' among competitors' : 'Leading position'}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">First Position Rate</div>
                    <div class="metric-value">${data.first_position_rate || 0}%</div>
                    <div class="metric-sublabel">${data.first_position_rate > 0 ? 'Strong visibility' : 'Opportunity for growth'}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Queries Tested</div>
                    <div class="metric-value">${data.total_queries}</div>
                    <div class="metric-sublabel">${data.total_queries} queries × 4 AI platforms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Citations</div>
                    <div class="metric-value">${data.total_citations || data.total_results}</div>
                    <div class="metric-sublabel">${data.total_unique_outlets || (data.top_sources ? data.top_sources.length : 0)} unique media outlets</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Gap to Leader</div>
                    <div class="metric-value">${gapToLeader > 0 ? '-' : ''}${Math.abs(gapToLeader)}%</div>
                    <div class="metric-sublabel">vs ${data.rankings && data.rankings[0] ? data.rankings[0][0] : 'top competitor'}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Platforms Tested</div>
                    <div class="metric-value">4</div>
                    <div class="metric-sublabel">ChatGPT, Claude, Perplexity, Gemini</div>
                </div>
            `;
            html += `</div>`;
            
            // Brand Mention Share Visualization
            if (data.rankings && data.rankings.length > 0) {
                html += `
                <div class="section">
                    <h2 class="section-title">Brand Mention Share</h2>
                    <div style="margin: 2rem 0;">
                `;
                
                data.rankings.slice(0, 5).forEach(([brand, mentions]) => {
                    const pct = Math.round(mentions / data.total_results * 100);
                    const isOurBrand = brand === data.brand;
                    html += `
                        <div style="margin-bottom: 1.5rem;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="font-weight: ${isOurBrand ? 'bold' : '400'}; color: ${isOurBrand ? '#B8C5CD' : '#E8E8E8'};">${brand}</span>
                                <span style="font-weight: ${isOurBrand ? 'bold' : '400'}; color: ${isOurBrand ? '#B8C5CD' : '#E8E8E8'};">${pct}%</span>
                            </div>
                            <div style="background: #2A2A2A; height: 12px; border-radius: 6px; overflow: hidden;">
                                <div style="background: ${isOurBrand ? 'linear-gradient(90deg, #464A3F 0%, #5A5F53 100%)' : '#3A3A3A'}; width: ${pct}%; height: 100%; transition: width 0.5s ease;"></div>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                    </div>
                </div>
                `;
            }
            
            // Competitive Rankings Table
            html += `
            <div class="section">
                <h2 class="section-title">Brand Citation Rankings</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Brand</th>
                            <th>Mention Rate</th>
                            <th>First Position %</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.rankings.forEach((item, i) => {
                const [brand, mentions] = item;
                const pct = Math.round(mentions / data.total_results * 100);
                const rankClass = i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : 'rank-other';
                const isOurBrand = brand === data.brand;
                const status = i === 0 ? 'Dominant' : i <= 2 ? 'Strong' : pct >= 50 ? 'Competitive' : 'Growth Opportunity';
                
                html += `
                    <tr style="${isOurBrand ? 'background: rgba(70, 74, 63, 0.1);' : ''}">
                        <td><span class="rank-badge ${rankClass}">#${i + 1}</span></td>
                        <td><strong>${brand}</strong></td>
                        <td>${pct}%</td>
                        <td>${data.first_position_rate || 0}%</td>
                        <td>${status}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            </div>
            `;
            
            // Top Media Outlets with Citation Type Breakdown
            if (data.top_sources && data.top_sources.length > 0) {
                // Count recommended resources for key finding
                const recommendedCount = data.top_sources.filter(s => s.recommended > 0).length;
                const topRecommended = data.top_sources.filter(s => s.recommended > 0).sort((a, b) => b.recommended - a.recommended)[0];
                
                html += `
                <div class="section" id="topMediaSection">
                    <h2 class="section-title">Top Media Outlets by Citation Frequency</h2>
                    <div style="margin: 1.5rem 0;">
                        <h4 style="font-size: 1rem; font-weight: 500; color: #B8C5CD; margin-bottom: 1rem;">Key Finding</h4>
                        <p style="line-height: 1.8; color: #CCCCCC;">
                            ${data.top_sources[0].domain} leads with ${data.top_sources[0].total} citations${data.top_sources[0].brand_mentions === 0 ? ` but does not currently mention ${data.brand}` : ''}. 
                            ${recommendedCount > 0 ? `<strong>${recommendedCount} outlets</strong> are actively recommending resources to users, with ${topRecommended.domain} being recommended most frequently (${topRecommended.recommended}x). These represent the highest-value PR opportunities.` : 'Analysis identifies strategic opportunities for increased visibility.'}
                        </p>
                    </div>
                    
                    <div style="margin: 1rem 0 1.5rem 0; padding: 1rem; background: #1A1A1A; border-radius: 6px;">
                        <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="display: inline-block; width: 12px; height: 12px; background: #2196F3; border-radius: 2px;"></span>
                                <span style="font-size: 0.85rem; color: #999999;">URL Citations (Direct links)</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="display: inline-block; width: 12px; height: 12px; background: #9C27B0; border-radius: 2px;"></span>
                                <span style="font-size: 0.85rem; color: #999999;">Inferred Citations ("According to X")</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span style="display: inline-block; width: 12px; height: 12px; background: #FFD700; border-radius: 2px;"></span>
                                <span style="font-size: 0.85rem; color: #999999;"><strong>Recommended Resources</strong> ("Visit X") - Highest Value</span>
                            </div>
                        </div>
                    </div>

                    <div class="tabs" style="display:flex; gap:0; margin-bottom: 1rem; border-bottom: 2px solid #2A2A2A; flex-wrap: wrap;">
                        <button class="tab topmedia-tab active" onclick="switchTopMediaTab(event, 'all')" style="padding: 0.75rem 1.25rem; background:none; border:none; color:#B8C5CD; cursor:pointer; border-bottom: 3px solid #464A3F;">All Media (Top 20)</button>
                        <button class="tab topmedia-tab" onclick="switchTopMediaTab(event, 'sports_entertainment')" style="padding: 0.75rem 1.25rem; background:none; border:none; color:#888888; cursor:pointer; border-bottom: 3px solid transparent;">Sports & Entertainment</button>
                        <button class="tab topmedia-tab" onclick="switchTopMediaTab(event, 'tech_streaming')" style="padding: 0.75rem 1.25rem; background:none; border:none; color:#888888; cursor:pointer; border-bottom: 3px solid transparent;">Tech & Streaming</button>
                        <button class="tab topmedia-tab" onclick="switchTopMediaTab(event, 'brand_official')" style="padding: 0.75rem 1.25rem; background:none; border:none; color:#888888; cursor:pointer; border-bottom: 3px solid transparent;">Brand Official Sites</button>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 50px;">Rank</th>
                                <th>Outlet</th>
                                <th style="width: 100px;">Total</th>
                                <th style="width: 200px;">Citation Type Breakdown</th>
                                <th style="width: 100px;">${data.brand} Mentions</th>
                                <th style="width: 100px;">Priority</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.top_sources.forEach((source, i) => {
                    const priority = source.total >= 4 && source.brand_mentions === 0 ? 'High' : 
                                   source.total >= 2 ? 'Medium' : 'Low';
                    const priorityColor = priority === 'High' ? '#FFD700' : priority === 'Medium' ? '#B8C5CD' : '#666666';
                    
                    // Highlight rows with recommended resources
                    const hasRecommendations = source.recommended > 0;
                    const rowStyle = hasRecommendations ? 'background: rgba(255, 215, 0, 0.05); border-left: 3px solid #FFD700;' : '';
                    
                    // Build citation type badges
                    let citationBadges = '';
                    if (source.url_citations > 0) {
                        citationBadges += `<span style="display: inline-block; padding: 0.25rem 0.5rem; background: #2196F3; color: white; border-radius: 3px; font-size: 0.75rem; margin-right: 0.25rem;">🔗 ${source.url_citations}</span>`;
                    }
                    if (source.inferred_citations > 0) {
                        citationBadges += `<span style="display: inline-block; padding: 0.25rem 0.5rem; background: #9C27B0; color: white; border-radius: 3px; font-size: 0.75rem; margin-right: 0.25rem;">📰 ${source.inferred_citations}</span>`;
                    }
                    if (source.recommended > 0) {
                        citationBadges += `<span style="display: inline-block; padding: 0.25rem 0.5rem; background: #FFD700; color: #000; border-radius: 3px; font-size: 0.75rem; font-weight: 600; margin-right: 0.25rem;">⭐ ${source.recommended}</span>`;
                    }
                    
                    html += `
                        <tr style="${rowStyle}" data-group="${source.group}">
                            <td><strong>${i + 1}</strong></td>
                            <td>
                                <a href="https://${source.domain}" target="_blank" style="color: #B8C5CD; text-decoration: none;">${source.domain}</a>
                                ${hasRecommendations ? '<span style="margin-left: 0.5rem; color: #FFD700; font-size: 0.85rem;">★ Recommended</span>' : ''}
                            </td>
                            <td><span class="citation-count">${source.total}</span></td>
                            <td>${citationBadges || '<span style="color: #666;">-</span>'}</td>
                            <td>${source.brand_mentions}</td>
                            <td><span style="color: ${priorityColor}; font-weight: 500;">${priority}</span></td>
                        </tr>
                    `;
                });
                
                html += `
                        </tbody>
                    </table>
                    
                    <div style="margin-top: 1.5rem; padding: 1rem; background: #1A1A1A; border-radius: 6px; border-left: 3px solid #FFD700;">
                        <h4 style="font-size: 0.95rem; font-weight: 500; color: #FFD700; margin-bottom: 0.75rem;">💡 About Citation Types</h4>
                        <ul style="margin: 0; padding-left: 1.5rem; line-height: 1.8; color: #CCCCCC; font-size: 0.9rem;">
                            <li><strong>URL Citations (🔗):</strong> Direct hyperlinks provided by platforms (primarily Perplexity)</li>
                            <li><strong>Inferred Citations (📰):</strong> Source references like "According to X" or "ESPN reports"</li>
                            <li><strong>Recommended Resources (⭐):</strong> Platforms explicitly telling users "Visit X" or "Check Y" - These are the highest-value opportunities as AI is actively directing traffic to these outlets</li>
                        </ul>
                    </div>
                </div>
                `;
            }
            
            // Interactive chart: Citation Types by Outlet
            html += `
            <div class="section">
                <h2 class="section-title">Citation Types by Outlet (Interactive)</h2>
                <div style="height: 320px;">
                    <canvas id="citationsChart"></canvas>
                </div>
                <div style="margin-top: 0.5rem; color: #999999; font-size: 0.9rem;">
                    Stacked bars by citation type:
                    <span style="display:inline-block;width:10px;height:10px;background:#2196F3;margin:0 6px 0 12px;"></span>URL (🔗)
                    <span style="display:inline-block;width:10px;height:10px;background:#9C27B0;margin:0 6px 0 12px;"></span>Inferred (📰)
                    <span style="display:inline-block;width:10px;height:10px;background:#FFD700;margin:0 6px 0 12px;border:1px solid #333;"></span>Recommended (⭐)
                </div>
            </div>
            `;

            // Media Outlets Matrix (Interactive)
            html += `
            <div class="section">
                <h2 class="section-title">Media Outlets Matrix — Interactive</h2>
                <div class="filter-controls" style="display:flex; gap: 12px; align-items:center; margin-bottom: 0.75rem;">
                    <input id="mediaMatrixSearch" type="text" placeholder="Search outlets..." 
                           style="flex:1; padding: 8px 10px; background:#1A1A1A; border:1px solid #2A2A2A; border-radius:6px; color:#E8E8E8;">
                    <select id="mediaMatrixFilter" 
                            style="padding: 8px 10px; background:#1A1A1A; border:1px solid #2A2A2A; border-radius:6px; color:#E8E8E8;">
                        <option value="">All</option>
                        <option value="opportunities">Opportunities Only (no brand mentions)</option>
                    </select>
                </div>
                <table id="mediaMatrixTable" style="width:100%; border-collapse:collapse; font-size: 0.95rem;">
                    <thead>
                        <tr style="background:#222222;">
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('domain')">Outlet</th>
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('total')">Total</th>
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('brand_mentions')">${data.brand} Mentions</th>
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('brand_share')">${data.brand} Share</th>
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('url_citations')">URL (🔗)</th>
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('inferred_citations')">Inferred (📰)</th>
                            <th style="padding:10px; color:#999999; cursor:pointer;" onclick="sortMediaMatrix('recommended')">Recommended (⭐)</th>
                            <th style="padding:10px; color:#999999;">Priority</th>
                        </tr>
                    </thead>
                    <tbody id="mediaMatrixBody"></tbody>
                </table>
            </div>
            `;

            // Initialize Media Outlets Matrix
            try {
                const rawRows = (data.top_sources || []).map(s => {
                    const priority = (s.total >= 4 && (s.brand_mentions||0) === 0) ? 'High'
                                   : (s.total >= 2 && s.total < 4 && (s.brand_mentions||0) === 0) ? 'Medium'
                                   : '—';
                    return {
                        domain: s.domain,
                        total: s.total || 0,
                        brand_mentions: s.brand_mentions || 0,
                        brand_share: s.brand_share || 0,
                        url_citations: s.url_citations || 0,
                        inferred_citations: s.inferred_citations || 0,
                        recommended: s.recommended || 0,
                        priority
                    };
                });

                let matrixRows = rawRows.slice();
                let sortCol = 'total';
                let sortDir = 'desc';

                function applyFilters() {
                    const q = (document.getElementById('mediaMatrixSearch')?.value || '').toLowerCase();
                    const filter = document.getElementById('mediaMatrixFilter')?.value || '';
                    let rows = rawRows.filter(r => r.domain.toLowerCase().includes(q));
                    if (filter === 'opportunities') rows = rows.filter(r => r.brand_mentions === 0);
                    return rows;
                }

                function renderMediaMatrix() {
                    const tbody = document.getElementById('mediaMatrixBody');
                    if (!tbody) return;
                    tbody.innerHTML = '';
                    matrixRows.forEach(r => {
                        const priorityColor = r.priority === 'High' ? '#FFD700' : r.priority === 'Medium' ? '#B8C5CD' : '#666666';
                        const tr = document.createElement('tr');
                        tr.style.borderBottom = '1px solid #2A2A2A';
                        tr.innerHTML = `
                            <td style="padding:10px;"><a href="https://${r.domain}" target="_blank" style="color:#B8C5CD; text-decoration:none;">${r.domain}</a></td>
                            <td style="padding:10px;"><span class="citation-count">${r.total}</span></td>
                            <td style="padding:10px;">${r.brand_mentions}</td>
                            <td style="padding:10px;">${r.brand_share}%</td>
                            <td style="padding:10px;">${r.url_citations}</td>
                            <td style="padding:10px;">${r.inferred_citations}</td>
                            <td style="padding:10px;">${r.recommended}</td>
                            <td style="padding:10px; color:${priorityColor}; font-weight:500;">${r.priority}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }

                function sortRows(col) {
                    if (sortCol === col) {
                        sortDir = (sortDir === 'asc') ? 'desc' : 'asc';
                    } else {
                        sortCol = col;
                        sortDir = (col === 'domain') ? 'asc' : 'desc';
                    }
                    matrixRows.sort((a, b) => {
                        const va = a[col], vb = b[col];
                        if (typeof va === 'string' || typeof vb === 'string') {
                            return sortDir === 'asc' ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
                        }
                        return sortDir === 'asc' ? (va - vb) : (vb - va);
                    });
                }

                // Expose handlers
                window.sortMediaMatrix = (col) => { matrixRows = applyFilters(); sortRows(col); renderMediaMatrix(); };
                window.filterMediaMatrix = () => { matrixRows = applyFilters(); sortRows(sortCol); renderMediaMatrix(); };

                // Initial render
                matrixRows = applyFilters();
                sortRows(sortCol);
                renderMediaMatrix();

                // Wire up search/filter (in case user types without pressing enter)
                const searchEl = document.getElementById('mediaMatrixSearch');
                if (searchEl) {
                    searchEl.addEventListener('input', () => window.filterMediaMatrix());
                }
            } catch (e) {
                console.error('Media matrix init failed', e);
            }

            // PR Target List
            const highPriorityOutlets = data.top_sources ? data.top_sources.filter(s => s.total >= 4 && s.brand_mentions === 0) : [];
            const mediumPriorityOutlets = data.top_sources ? data.top_sources.filter(s => s.total >= 2 && s.total < 4 && s.brand_mentions === 0) : [];
            
            if (highPriorityOutlets.length > 0 || mediumPriorityOutlets.length > 0) {
                html += `
                <div class="section">
                    <h2 class="section-title">PR Target List — Priority Media Outlets</h2>
                    <div style="margin: 1.5rem 0 2rem 0;">
                        <h4 style="font-size: 1rem; font-weight: 500; color: #B8C5CD; margin-bottom: 1rem;">Strategic Targeting</h4>
                        <p style="line-height: 1.8; color: #CCCCCC;">
                            Publications with high citation frequency but limited ${data.brand} mentions represent opportunities for increased visibility. 
                            These outlets are already trusted by AI platforms and could help strengthen ${data.brand}'s presence through enhanced content partnerships.
                        </p>
                    </div>
                `;
                
                if (highPriorityOutlets.length > 0) {
                    html += `
                    <div style="margin-bottom: 2rem;">
                        <h3 style="font-size: 1.1rem; font-weight: 500; color: #FFD700; margin-bottom: 1rem;">Tier 1: High Priority</h3>
                        <p style="font-size: 0.9rem; color: #999999; margin-bottom: 1rem;">Criteria: 4+ citations, limited ${data.brand} mentions, high AI platform trust.</p>
                        <table>
                            <thead>
                                <tr>
                                    <th>Level</th>
                                    <th>Outlet</th>
                                    <th>Citations</th>
                                    <th>AI Platforms Citing</th>
                                    <th>Recommended Action</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    highPriorityOutlets.forEach(source => {
                        html += `
                            <tr>
                                <td><span style="color: #FFD700; font-weight: 500;">High</span></td>
                                <td><a href="https://${source.domain}" target="_blank" style="color: #B8C5CD; text-decoration: none;">${source.domain}</a></td>
                                <td><span class="citation-count">${source.total}</span></td>
                                <td>Multiple Platforms</td>
                                <td>Priority outreach for editorial partnerships</td>
                            </tr>
                        `;
                    });
                    
                    html += `
                            </tbody>
                        </table>
                    </div>
                    `;
                }
                
                if (mediumPriorityOutlets.length > 0) {
                    html += `
                    <div style="margin-bottom: 2rem;">
                        <h3 style="font-size: 1.1rem; font-weight: 500; color: #B8C5CD; margin-bottom: 1rem;">Tier 2: Medium Priority</h3>
                        <p style="font-size: 0.9rem; color: #999999; margin-bottom: 1rem;">Criteria: 2-3 citations, limited ${data.brand} mentions, good reach potential.</p>
                        <table>
                            <thead>
                                <tr>
                                    <th>Outlet</th>
                                    <th>Citations</th>
                                    <th>${data.brand} Share</th>
                                    <th>Target Action</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    mediumPriorityOutlets.forEach(source => {
                        html += `
                            <tr>
                                <td><a href="https://${source.domain}" target="_blank" style="color: #B8C5CD; text-decoration: none;">${source.domain}</a></td>
                                <td><span class="citation-count">${source.total}</span></td>
                                <td>${source.brand_share}%</td>
                                <td>Consider for content inclusion</td>
                            </tr>
                        `;
                    });
                    
                    html += `
                            </tbody>
                        </table>
                    </div>
                    `;
                }
                
                html += `</div>`;
            }
            
            // AI Platform Citation Patterns
            const platforms = Object.keys(data.platform_stats);
            html += `
            <div class="section">
                <h2 class="section-title">AI Platform Citation Patterns</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
            `;
            
            platforms.forEach(platform => {
                const stats = data.platform_stats[platform];
                const rate = stats.total > 0 ? Math.round(stats.brand_mentions / stats.total * 100) : 0;
                const citationLevel = stats.citations > 15 ? 'High' : stats.citations > 5 ? 'Medium' : stats.citations > 0 ? 'Low' : 'Minimal';
                const description = getPlatformDescription(platform, citationLevel);
                
                html += `
                    <div style="padding: 1.5rem; background: #222222; border-radius: 8px; border-left: 3px solid #464A3F;">
                        <h4 style="font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem;">${platform}</h4>
                        <div style="font-size: 2rem; font-weight: 300; color: #B8C5CD; margin: 0.75rem 0;">${rate}%</div>
                        <div style="font-size: 0.9rem; color: #999999; margin-bottom: 0.75rem;">
                            ${stats.brand_mentions}/${stats.total} mentions • ${stats.citations} citations
                        </div>
                        <div style="padding: 0.75rem; background: #1A1A1A; border-radius: 4px; margin-top: 0.75rem;">
                            <div style="font-size: 0.85rem; color: #B8C5CD; font-weight: 500; margin-bottom: 0.25rem;">${citationLevel}</div>
                            <div style="font-size: 0.85rem; color: #CCCCCC; line-height: 1.5;">${description}</div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                </div>
                <div style="margin-top: 2rem; padding: 1.5rem; background: #1A1A1A; border-radius: 8px; border-left: 3px solid #B8C5CD;">
                    <h4 style="font-size: 1rem; font-weight: 500; color: #B8C5CD; margin-bottom: 1rem;">Platform Strategy Insight</h4>
                    <p style="line-height: 1.8; color: #CCCCCC;">
                        ${getPlatformStrategyInsight(data.platform_stats, data.brand)}
                    </p>
                </div>
            </div>
            `;
            
            // Strategic Recommendations
            html += `
            <div class="section">
                <h2 class="section-title">Strategic Recommendations</h2>
                
                <div style="margin: 1.5rem 0;">
                    <h3 style="font-size: 1.1rem; font-weight: 500; color: #FFD700; margin-bottom: 1rem;">Near-Term Opportunities (Next 30-60 Days)</h3>
                    <ol style="padding-left: 1.5rem; line-height: 2; color: #CCCCCC;">
            `;
            
            // Generate recommendations based on data
            const recommendations = generateRecommendations(data);
            recommendations.nearTerm.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            
            html += `
                    </ol>
                </div>
                
                <div style="margin: 1.5rem 0;">
                    <h3 style="font-size: 1.1rem; font-weight: 500; color: #B8C5CD; margin-bottom: 1rem;">Medium-Term Strategy (Q1 2026)</h3>
                    <ol style="padding-left: 1.5rem; line-height: 2; color: #CCCCCC;">
            `;
            
            recommendations.mediumTerm.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            
            html += `
                    </ol>
                </div>
            </div>
            `;
            
            // Methodology
            html += `
            <div class="section">
                <h2 class="section-title">Methodology & Data Quality</h2>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0;">
                    <div style="padding: 1rem; background: #1A1A1A; border-radius: 6px;">
                        <div style="font-size: 1.5rem; font-weight: 300; color: #B8C5CD; margin-bottom: 0.5rem;">${data.total_results}</div>
                        <div style="font-size: 0.85rem; color: #999999;">queries executed</div>
                    </div>
                    <div style="padding: 1rem; background: #1A1A1A; border-radius: 6px;">
                        <div style="font-size: 1.5rem; font-weight: 300; color: #B8C5CD; margin-bottom: 0.5rem;">${data.total_citations || data.total_results}</div>
                        <div style="font-size: 0.85rem; color: #999999;">citations captured</div>
                    </div>
                    <div style="padding: 1rem; background: #1A1A1A; border-radius: 6px;">
                        <div style="font-size: 1.5rem; font-weight: 300; color: #B8C5CD; margin-bottom: 0.5rem;">${data.total_unique_outlets || (data.top_sources ? data.top_sources.length : 0)}</div>
                        <div style="font-size: 0.85rem; color: #999999;">unique media outlets</div>
                    </div>
                    <div style="padding: 1rem; background: #1A1A1A; border-radius: 6px;">
                        <div style="font-size: 1.5rem; font-weight: 300; color: #B8C5CD; margin-bottom: 0.5rem;">100%</div>
                        <div style="font-size: 0.85rem; color: #999999;">query success rate</div>
                    </div>
                </div>
                
                <div style="margin-top: 1.5rem;">
                    <h4 style="font-size: 1rem; font-weight: 500; color: #B8C5CD; margin-bottom: 1rem;">Analysis Scope</h4>
                    <p style="line-height: 1.8; color: #CCCCCC;">
                        ${data.total_queries} queries tested across ChatGPT, Claude, Perplexity, and Gemini. 
                        Mix included brand-specific discovery queries, competitive comparison queries, and unbiased market queries. 
                        Analysis conducted ${new Date().toLocaleDateString('en-US', {month: 'long', year: 'numeric'})} to inform visibility strategy.
                    </p>
                </div>
            </div>
            `;
            
            // Download CSV
            html += `
            <div class="section" style="text-align: center;">
                <h2 class="section-title">Download Full Data</h2>
                <a href="/download-sample/raw/${data.csv_filename}" class="download-btn">⬇ Download Complete CSV Report</a>
                <p style="margin-top: 1rem; color: #666666; font-size: 0.9rem;">
                    Includes full responses, citations, query matrix, and detailed competitive analysis
                </p>
            </div>
            `;
            
            dashboard.innerHTML = html;

            // Initialize Chart.js stacked bar for citation types, if canvas present
            try {
                if (data.top_sources && data.top_sources.length > 0) {
                    const labels = data.top_sources.map(s => s.domain);
                    const urlData = data.top_sources.map(s => s.url_citations || 0);
                    const infData = data.top_sources.map(s => s.inferred_citations || 0);
                    const recData = data.top_sources.map(s => s.recommended || 0);

                    const canvas = document.getElementById('citationsChart');
                    if (canvas) {
                        const ctx = canvas.getContext('2d');
                        // Tweak colors for dark theme
                        const gridColor = '#2A2A2A';
                        const axisColorX = '#CCCCCC';
                        const axisColorY = '#999999';

                        new Chart(ctx, {
                            type: 'bar',
                            data: {
                                labels,
                                datasets: [
                                    {
                                        label: 'URL Citations',
                                        data: urlData,
                                        backgroundColor: '#2196F3',
                                        borderWidth: 0
                                    },
                                    {
                                        label: 'Inferred Citations',
                                        data: infData,
                                        backgroundColor: '#9C27B0',
                                        borderWidth: 0
                                    },
                                    {
                                        label: 'Recommended',
                                        data: recData,
                                        backgroundColor: '#FFD700',
                                        borderColor: '#000000',
                                        borderWidth: 0
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                interaction: { mode: 'index', intersect: false },
                                plugins: {
                                    legend: {
                                        labels: { color: '#CCCCCC', boxWidth: 14 }
                                    },
                                    tooltip: {
                                        callbacks: {
                                            afterBody: (items) => {
                                                const i = items[0].dataIndex;
                                                const t = (urlData[i] || 0) + (infData[i] || 0) + (recData[i] || 0);
                                                const share = t ? Math.round((recData[i] / t) * 100) : 0;
                                                return [`Total: ${t}`, `Recommended share: ${share}%`];
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    x: {
                                        stacked: true,
                                        ticks: { color: axisColorX },
                                        grid: { color: gridColor }
                                    },
                                    y: {
                                        stacked: true,
                                        ticks: { color: axisColorY },
                                        grid: { color: gridColor }
                                    }
                                },
                                onClick: (evt, elements) => {
                                    if (elements && elements.length > 0) {
                                        const index = elements[0].index;
                                        const domain = labels[index];
                                        if (domain) {
                                            window.open(`https://${domain}`, '_blank');
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
            } catch (e) {
                console.error('Chart initialization failed', e);
            }

            // Filterable tabs for Top Media table
            try {
                window.switchTopMediaTab = function(evt, group) {
                    document.querySelectorAll('.topmedia-tab').forEach(b => b.classList.remove('active'));
                    if (evt && evt.target) {
                        evt.target.classList.add('active');
                    }
                    const rows = document.querySelectorAll('#topMediaSection table tbody tr');
                    rows.forEach(r => {
                        const g = r.getAttribute('data-group') || 'other';
                        r.style.display = (!group || group === 'all' || g === group) ? '' : 'none';
                    });
                };
                // Default view
                window.switchTopMediaTab(null, 'all');
            } catch (e) {
                console.error('Top media tabs init failed', e);
            }
        }
        
        function getRankSuffix(rank) {
            if (rank === 1) return '1st';
            if (rank === 2) return '2nd';
            if (rank === 3) return '3rd';
            return rank + 'th';
        }
        
        function getPlatformDescription(platform, level) {
            const descriptions = {
                'ChatGPT': {
                    'High': 'Strong citation behavior, diverse source usage',
                    'Medium': 'Moderate citations, relies on training data',
                    'Low': 'Limited citations, training data focused',
                    'Minimal': 'Rarely cites external sources, relies on training data'
                },
                'Claude': {
                    'High': 'Most detailed citations, includes multiple sources',
                    'Medium': 'Good citation behavior, selective sourcing',
                    'Low': 'Some citations, quality focused',
                    'Minimal': 'Very selective citation usage'
                },
                'Perplexity': {
                    'High': 'Web-first approach, cites media heavily',
                    'Medium': 'Strong web sourcing, good citation practices',
                    'Low': 'Some web citations, variable sourcing',
                    'Minimal': 'Limited web citation usage'
                },
                'Gemini': {
                    'High': 'Comprehensive citations, detailed sourcing',
                    'Medium': 'Moderate citations, selective usage',
                    'Low': 'Limited citations, minimal sourcing',
                    'Minimal': 'Very few citations, minimal streaming coverage'
                }
            };
            
            return descriptions[platform]?.[level] || 'Citation behavior varies';
        }
        
        function getPlatformStrategyInsight(platformStats, brand) {
            // Find which platforms have the most citations
            const sortedPlatforms = Object.entries(platformStats)
                .map(([name, stats]) => ({ name, citations: stats.citations }))
                .sort((a, b) => b.citations - a.citations);
            
            const topPlatforms = sortedPlatforms.slice(0, 2).map(p => p.name);
            
            if (topPlatforms.length >= 2) {
                return `${topPlatforms[0]} and ${topPlatforms[1]} drive the majority of citations and are most influenced by media content. Optimizing content for these platforms through strategic media partnerships will have the highest ROI for improving ${brand}'s visibility in AI recommendations.`;
            } else if (topPlatforms.length === 1) {
                return `${topPlatforms[0]} provides the most citations. Focus content optimization efforts on sources that this platform frequently cites to improve ${brand}'s visibility.`;
            } else {
                return `Citation patterns vary across platforms. A diversified content strategy targeting multiple media outlets will help improve overall visibility.`;
            }
        }
        
        function generateRecommendations(data) {
            const recommendations = {
                nearTerm: [],
                mediumTerm: []
            };
            
            // Near-term recommendations based on high-priority outlets
            const highPriorityOutlets = data.top_sources ? data.top_sources.filter(s => s.total >= 4 && s.brand_mentions === 0) : [];
            
            if (highPriorityOutlets.length > 0) {
                recommendations.nearTerm.push(
                    `<strong>${highPriorityOutlets[0].domain} engagement:</strong> ${highPriorityOutlets[0].total} citations, no current ${data.brand} mentions. Consider outreach for inclusion in relevant content, emphasizing ${data.brand}'s unique value proposition.`
                );
            }
            
            if (highPriorityOutlets.length > 1) {
                recommendations.nearTerm.push(
                    `<strong>${highPriorityOutlets[1].domain} partnership exploration:</strong> ${highPriorityOutlets[1].total} citations with high authority. Potential opportunity for inclusion in comparison guides or industry coverage.`
                );
            }
            
            // Gap to leader recommendation
            if (data.brand_rank > 1 && data.rankings && data.rankings.length > 0) {
                const leader = data.rankings[0][0];
                const gap = Math.round((data.rankings[0][1] / data.total_results * 100) - data.brand_mention_rate);
                recommendations.nearTerm.push(
                    `<strong>Competitive analysis:</strong> Review ${leader}'s content approach (${gap}% gap) to identify potential best practices and differentiation opportunities.`
                );
            }
            
            // Platform-specific recommendations
            const platformsWithLowCitations = Object.entries(data.platform_stats || {})
                .filter(([name, stats]) => stats.citations < 5)
                .map(([name]) => name);
            
            if (platformsWithLowCitations.length > 0) {
                recommendations.nearTerm.push(
                    `<strong>Platform optimization:</strong> ${platformsWithLowCitations.join(', ')} show low citation counts. Develop content optimized for discoverability on these platforms.`
                );
            }
            
            // Add generic recommendations if we don't have enough specific ones
            if (recommendations.nearTerm.length < 4) {
                recommendations.nearTerm.push(
                    `<strong>Content audit:</strong> Review and update existing content to include relevant keywords and structured data that AI platforms can easily parse and cite.`
                );
            }
            
            if (recommendations.nearTerm.length < 5) {
                recommendations.nearTerm.push(
                    `<strong>Regular monitoring:</strong> Consider quarterly ${data.brand} citation audits to track progress and identify emerging opportunities in the AI visibility landscape.`
                );
            }
            
            // Medium-term recommendations
            recommendations.mediumTerm.push(
                `<strong>Content optimization:</strong> Develop ${data.brand} guides optimized for AI platform discoverability with structured data and clear value propositions.`
            );
            
            recommendations.mediumTerm.push(
                `<strong>Media relationships:</strong> Build long-term partnerships with industry publications and create regular contribution opportunities.`
            );
            
            recommendations.mediumTerm.push(
                `<strong>Value proposition messaging:</strong> Emphasize ${data.brand}'s unique differentiators in all content to stand out in competitive comparisons.`
            );
            
            recommendations.mediumTerm.push(
                `<strong>Community engagement:</strong> Encourage customer feedback and reviews on platforms commonly cited by AI systems to build social proof.`
            );
            
            recommendations.mediumTerm.push(
                `<strong>Thought leadership:</strong> Position ${data.brand} leadership as subject matter experts through regular insights, webinars, and industry commentary.`
            );
            
            return recommendations;
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5010"))
    app.run(host="0.0.0.0", port=port, debug=True)
