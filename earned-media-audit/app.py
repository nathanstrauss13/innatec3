import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Local imports
from earned_analyzer import EarnedAnalyzer

# Load .env if present (root and app-local)
load_dotenv()  # root .env (repo-level)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)  # earned-media-audit/.env

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "earned_media_secret")

# Storage for job JSON (persisted to disk)
JOBS_DIR = os.path.join(os.path.dirname(__file__), "instance", "earned_jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

def infer_brand_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        if not host:
            return url
        parts = host.split(".")
        # crude but sufficient for MVP; future: use tldextract
        if len(parts) >= 2:
            # handle common ccTLD second-level like co.uk (simple heuristic)
            sld_tlds = {"co.uk", "com.au", "co.jp", "com.br", "com.mx", "co.in"}
            last2 = ".".join(parts[-2:])
            if last2 in sld_tlds and len(parts) >= 3:
                core = parts[-3]
            else:
                core = parts[-2]
            return core.replace("-", " ").title()
        return host
    except Exception:
        return url

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "time": datetime.utcnow().isoformat() + "Z"
    })

@app.route("/earned/run", methods=["POST"])
def run_earned_audit():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON payload"}), 400

    brand_url = (payload or {}).get("brand_url", "").strip()
    brand_name = (payload or {}).get("brand_name", "").strip()
    competitor_urls = (payload or {}).get("competitor_urls", []) or []
    query_budget = int((payload or {}).get("query_budget", 25))
    providers = (payload or {}).get("providers", ["llm_browsing"])

    if not brand_url:
        return jsonify({"error": "brand_url is required"}), 400

    if not brand_url.startswith(("http://", "https://")):
        brand_url = "https://" + brand_url

    if not brand_name:
        brand_name = infer_brand_from_url(brand_url)

    # Infer competitor names from URLs if names not given
    competitor_entities = []
    for cu in competitor_urls:
        if not cu:
            continue
        cu_norm = cu.strip()
        if not cu_norm.startswith(("http://", "https://")):
            cu_norm = "https://" + cu_norm
        competitor_entities.append({
            "url": cu_norm,
            "name": infer_brand_from_url(cu_norm)
        })

    analyzer = EarnedAnalyzer(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        providers=providers
    )

    job_id = str(uuid.uuid4())[:10]
    try:
        result = analyzer.run_audit(
            job_id=job_id,
            brand={"url": brand_url, "name": brand_name},
            competitors=competitor_entities,
            query_budget=query_budget
        )
    except Exception as e:
        return jsonify({"error": f"Audit failed: {e}"}), 500

    # Persist job JSON
    job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
    try:
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        # Non-fatal
        print(f"Warning: failed to persist job {job_id}: {e}")

    return jsonify(result)

@app.route("/earned/result/<job_id>", methods=["GET"])
def get_earned_result(job_id: str):
    job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if not os.path.exists(job_path):
        return jsonify({"error": "Result not found"}), 404
    with open(job_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5100))
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
    print(f"[earned-media-audit] Starting on port {port} (debug={debug_mode})")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
