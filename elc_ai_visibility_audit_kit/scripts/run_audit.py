import os
import json
import time
import hashlib
import argparse
import logging
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

"""
ELC AI Visibility Audit - Data Collection Pipeline

Enhancements:
- Argparse CLI flags (paths, providers, delay, retries, cache dir/ttl, limit, verbosity)
- Structured logging
- Retry with exponential backoff
- Simple on-disk caching per (provider, query)
- Optional Anthropic provider (simulated outlets)
- Optional Gemini provider (simulated outlets)
- Outlet normalization improvements
- Backward-compatible default behavior/output

Usage (default):
  python3 scripts/run_audit.py
"""

# Defaults resolved relative to project root
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = ROOT / "config"
DEFAULT_DATA_QUERIES = ROOT / "data" / "queries.csv"
DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_CACHE_DIR = DEFAULT_OUTPUT_DIR / ".cache"

# --------------- Env & Config ---------------

def env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)

def load_env(config_dir: Path):
    """
    Load KEY=VALUE pairs from config/.env into environment.
    """
    dotenv_path = config_dir / ".env"
    if dotenv_path.exists():
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()

def load_json(path: Path, default=None):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

# --------------- Helpers ---------------

def domain_to_outlet(domain: str, mapping: Dict[str, str]) -> str:
    d = (domain or "").lower().replace("www.", "")
    return mapping.get(d, d or "")

def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""

def normalize_outlet_name(name: str) -> str:
    if not name:
        return ""
    # Trim, collapse whitespace, standardize basic casing without harming acronyms
    s = " ".join(str(name).strip().split())
    # If it's all caps/acronyms like CNN/WSJ keep it; else title-case common words
    if len(s) <= 5 and s.isupper():
        return s
    try:
        return s.title()
    except Exception:
        return s

def hash_key(*parts: str) -> str:
    m = hashlib.sha256()
    m.update("|".join(parts).encode("utf-8"))
    return m.hexdigest()

# --------------- Caching ---------------

def cache_get(cache_dir: Path, key: str, ttl_seconds: int) -> Optional[dict]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_dir / f"{key}.json"
    if not p.exists():
        return None
    # TTL check
    age = time.time() - p.stat().st_mtime
    if ttl_seconds >= 0 and age > ttl_seconds:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def cache_set(cache_dir: Path, key: str, data: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_dir / f"{key}.json"
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logging.debug(f"Cache write failed for {p}: {e}")

# --------------- Networking ---------------

def post_with_retries(url: str, headers: dict, payload: dict, retries: int, initial_backoff: float, timeout: int = 60, params: Optional[dict] = None) -> requests.Response:
    attempt = 0
    backoff = initial_backoff
    last_exc = None
    while attempt <= retries:
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout, params=params)
            # Retry on 5xx
            if 500 <= r.status_code < 600:
                raise requests.HTTPError(f"Server error {r.status_code}: {r.text}")
            r.raise_for_status()
            return r
        except Exception as e:
            last_exc = e
            if attempt == retries:
                break
            sleep_for = backoff * (2 ** attempt)
            logging.warning(f"POST {url} failed (attempt {attempt+1}/{retries+1}): {e}. Retrying in {sleep_for:.2f}s")
            time.sleep(sleep_for)
            attempt += 1
    raise RuntimeError(f"Failed POST {url} after {retries+1} attempts: {last_exc}")

# --------------- Providers ---------------

def call_perplexity(query: str, api_key: str, retries: int, backoff: float, cache_dir: Path, cache_ttl: int) -> List[str]:
    """
    Returns list of citation URLs (strings)
    """
    provider = "perplexity"
    ck = hash_key(provider, query)
    cached = cache_get(cache_dir, ck, cache_ttl)
    if cached is not None:
        return cached.get("citations", [])

    if not api_key:
        return []

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "sonar-pro", "messages": [{"role": "user", "content": query}]}
    try:
        r = post_with_retries("https://api.perplexity.ai/chat/completions", headers, payload, retries, backoff)
        data = r.json()
        citations: List[str] = []
        urls = []

        # Try multiple shapes
        if isinstance(data, dict):
            if "citations" in data:
                urls = data["citations"]
            # choices[0].message.metadata.citations or web_search_sources
            if data.get("choices"):
                meta = data["choices"][0].get("message", {}).get("metadata", {})
                urls = meta.get("citations", []) or meta.get("web_search_sources", urls)

        for u in urls or []:
            if isinstance(u, dict):
                url = u.get("url") or u.get("source") or ""
            else:
                url = str(u)
            if url:
                citations.append(url)

        cache_set(cache_dir, ck, {"citations": citations})
        return citations
    except Exception as e:
        logging.warning(f"Perplexity call failed: {e}")
        return []

def _extract_json_array(text: str) -> List[str]:
    """
    Heuristically extract first JSON array from a text blob and parse it.
    """
    if not text:
        return []
    m = re.search(r"\[.*?\]", text, re.S)
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
        return [str(x).strip() for x in arr if isinstance(x, (str,))]
    except Exception:
        return []

def call_openai_list_outlets(query: str, api_key: str, prompts: dict, retries: int, backoff: float, cache_dir: Path, cache_ttl: int) -> List[str]:
    """
    Returns list of outlet names
    """
    provider = "openai_simulated"
    ck = hash_key(provider, query)
    cached = cache_get(cache_dir, ck, cache_ttl)
    if cached is not None:
        return cached.get("outlets", [])

    if not api_key:
        return []

    system = prompts.get("openai", {}).get("system", "")
    template = prompts.get("openai", {}).get("user_template", "Query: {q}")
    user = template.format(q=query)

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        r = post_with_retries("https://api.openai.com/v1/chat/completions", headers, payload, retries, backoff)
        txt = r.json()["choices"][0]["message"]["content"]
        outlets = _extract_json_array(txt)
        cache_set(cache_dir, ck, {"outlets": outlets})
        return outlets
    except Exception as e:
        logging.warning(f"OpenAI call failed: {e}")
        return []

def call_anthropic_list_outlets(query: str, api_key: str, prompts: dict, retries: int, backoff: float, cache_dir: Path, cache_ttl: int) -> List[str]:
    """
    Returns list of outlet names
    """
    provider = "anthropic_simulated"
    ck = hash_key(provider, query)
    cached = cache_get(cache_dir, ck, cache_ttl)
    if cached is not None:
        return cached.get("outlets", [])

    if not api_key:
        return []

    system = prompts.get("anthropic", {}).get("system", "")
    template = prompts.get("anthropic", {}).get("user_template", "Query: {q}")
    user = template.format(q=query)

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-3-haiku-20240307",  # lightweight, adjust if needed
        "max_tokens": 600,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    try:
        r = post_with_retries("https://api.anthropic.com/v1/messages", headers, payload, retries, backoff)
        data = r.json()
        # Concatenate all text blocks
        txt = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                txt += block.get("text", "")
        outlets = _extract_json_array(txt)
        cache_set(cache_dir, ck, {"outlets": outlets})
        return outlets
    except Exception as e:
        logging.warning(f"Anthropic call failed: {e}")
        return []

def call_gemini_list_outlets(query: str, api_key: str, prompts: dict, retries: int, backoff: float, cache_dir: Path, cache_ttl: int) -> List[str]:
    """
    Returns list of outlet names via Google Generative Language API (Gemini)
    """
    provider = "gemini_simulated"
    ck = hash_key(provider, query)
    cached = cache_get(cache_dir, ck, cache_ttl)
    if cached is not None:
        return cached.get("outlets", [])

    if not api_key:
        return []

    system = prompts.get("anthropic", {}).get("system", "") or prompts.get("openai", {}).get("system", "")
    template = prompts.get("anthropic", {}).get("user_template", "Query: {q}") or prompts.get("openai", {}).get("user_template", "Query: {q}")
    user = template.format(q=query)

    # Keep prompt simple: place system + user into one user turn for compatibility
    prompt_text = (system + "\n\n" + user).strip()

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_text}],
            }
        ],
    }
    try:
        r = post_with_retries(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
            headers,
            payload,
            retries,
            backoff,
            params={"key": api_key},
        )
        data = r.json()
        txt = ""
        for cand in data.get("candidates", []) or []:
            content = cand.get("content", {})
            for part in content.get("parts", []) or []:
                if isinstance(part, dict) and "text" in part:
                    txt += part["text"]
        outlets = _extract_json_array(txt)
        cache_set(cache_dir, ck, {"outlets": outlets})
        return outlets
    except Exception as e:
        logging.warning(f"Gemini call failed: {e}")
        return []

# --------------- Core ---------------

def determine_providers(providers_arg: str) -> List[str]:
    """
    providers_arg:
      - 'auto' (default): enable providers if key present
      - comma-separated list: e.g., 'perplexity,openai,anthropic,gemini'
    """
    available = []
    if providers_arg.strip().lower() != "auto":
        for p in [x.strip().lower() for x in providers_arg.split(",") if x.strip()]:
            if p in {"perplexity", "openai", "anthropic", "gemini"}:
                available.append(p)
        return available

    # auto
    if env("PPLX_API_KEY") or env("PERPLEXITY_API_KEY"):
        available.append("perplexity")
    if env("OPENAI_API_KEY"):
        available.append("openai")
    if env("ANTHROPIC_API_KEY"):
        available.append("anthropic")
    if env("GEMINI_API_KEY"):
        available.append("gemini")
    return available

def run(
    queries_path: Path,
    output_dir: Path,
    config_dir: Path,
    providers_arg: str,
    delay: float,
    retries: int,
    backoff: float,
    cache_dir: Path,
    cache_ttl: int,
    limit: Optional[int],
):
    load_env(config_dir)
    prompts = load_json(config_dir / "prompts.json", default={}) or {}
    mapping = load_json(config_dir / "outlet_domain_map.json", default={}) or {}

    # Determine providers
    providers = determine_providers(providers_arg)
    logging.info(f"Providers enabled: {providers or 'none'}")

    # Resolve keys with fallbacks
    perplexity_key = env("PPLX_API_KEY") or env("PERPLEXITY_API_KEY") or ""
    openai_key = env("OPENAI_API_KEY", "") or ""
    anthropic_key = env("ANTHROPIC_API_KEY", "") or ""
    gemini_key = env("GEMINI_API_KEY", "") or ""

    # Load queries
    if not queries_path.exists():
        raise FileNotFoundError(f"Queries file not found: {queries_path}")
    qdf = pd.read_csv(queries_path)
    if "query" not in qdf.columns:
        raise ValueError(f"Expected column 'query' in {queries_path}")
    queries = [str(x) for x in qdf["query"].dropna().tolist()]
    if limit is not None:
        queries = queries[: int(limit)]
    if not queries:
        logging.warning("No queries to process.")
        queries = []

    rows: List[Dict[str, str]] = []

    for idx, q in enumerate(queries, 1):
        logging.info(f"[{idx}/{len(queries)}] Query: {q}")

        if "perplexity" in providers:
            urls = call_perplexity(q, perplexity_key, retries, backoff, cache_dir, cache_ttl)
            for u in urls:
                rows.append({"provider": "perplexity", "query": q, "url": u})

        if "openai" in providers:
            outlets = call_openai_list_outlets(q, openai_key, prompts, retries, backoff, cache_dir, cache_ttl)
            for name in outlets:
                rows.append({"provider": "openai_simulated", "query": q, "outlet": normalize_outlet_name(name)})

        if "anthropic" in providers:
            outlets = call_anthropic_list_outlets(q, anthropic_key, prompts, retries, backoff, cache_dir, cache_ttl)
            for name in outlets:
                rows.append({"provider": "anthropic_simulated", "query": q, "outlet": normalize_outlet_name(name)})

        if "gemini" in providers:
            outlets = call_gemini_list_outlets(q, gemini_key, prompts, retries, backoff, cache_dir, cache_ttl)
            for name in outlets:
                rows.append({"provider": "gemini_simulated", "query": q, "outlet": normalize_outlet_name(name)})

        if delay > 0:
            time.sleep(delay)

    df = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not df.empty:
        if "url" in df.columns:
            df["domain"] = df["url"].fillna("").apply(lambda x: extract_domain(x) if isinstance(x, str) else "")
            # fill outlet by mapping domains when outlet missing
            df["outlet"] = df.apply(
                lambda r: r.get("outlet") or domain_to_outlet(r.get("domain", ""), mapping),
                axis=1,
            )
        # Normalize outlet text a bit more
        df["outlet"] = df["outlet"].fillna("").apply(normalize_outlet_name)
        df = df.drop_duplicates()

    # Write raw rows
    raw_path = output_dir / "citations_raw.csv"
    df.to_csv(raw_path, index=False)

    # Aggregate
    if df.empty:
        agg = pd.DataFrame(columns=["outlet", "count"])
    else:
        agg = (
            df.groupby("outlet")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
    counts_path = output_dir / "outlet_counts.csv"
    agg.to_csv(counts_path, index=False)

    logging.info(f"Wrote: {raw_path}  {counts_path}")

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ELC AI Visibility Audit - Data Collection")
    p.add_argument("--queries-file", type=Path, default=DEFAULT_DATA_QUERIES, help="CSV with a 'query' column")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to write outputs")
    p.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR, help="Directory with .env and config JSONs")
    p.add_argument("--providers", type=str, default="auto", help="Providers to use: 'auto' or comma list: perplexity,openai,anthropic,gemini")
    p.add_argument("--delay", type=float, default=0.25, help="Delay (seconds) between queries")
    p.add_argument("--retries", type=int, default=2, help="HTTP retry attempts per call")
    p.add_argument("--backoff", type=float, default=0.5, help="Initial backoff (seconds) for retries (exponential)")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="On-disk cache directory")
    p.add_argument("--cache-ttl", type=int, default=86400, help="Cache TTL in seconds (set -1 to disable TTL expiration)")
    p.add_argument("--limit", type=int, default=None, help="Limit number of queries processed")
    p.add_argument("--verbose", action="store_true", help="Verbose logging")
    return p

def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    run(
        queries_path=args.queries_file,
        output_dir=args.output_dir,
        config_dir=args.config_dir,
        providers_arg=args.providers,
        delay=args.delay,
        retries=args.retries,
        backoff=args.backoff,
        cache_dir=args.cache_dir,
        cache_ttl=args.cache_ttl,
        limit=args.limit,
    )

if __name__ == "__main__":
    main()
