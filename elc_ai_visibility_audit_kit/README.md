# Estée Lauder Companies — AI Visibility Audit (Report Factory Kit)

This kit lets you run a pay‑per‑report style AI Visibility Audit for Estée Lauder Companies (ELC) as a white‑label deliverable.  
It is designed for fast execution with auto-detected providers, caching, retries, and a branded PDF output.

What you'll get
- Aggregated AI citation data across multiple models (where supported), normalized to publisher names.
- CSVs suitable for analysis and charting.
- A branded PDF report (white‑label friendly).

Quick start
1) Put API keys into config/.env (do not commit)
   - Supported providers (any subset is fine):
     - Perplexity: PPLX_API_KEY or PERPLEXITY_API_KEY
     - OpenAI: OPENAI_API_KEY
     - Anthropic: ANTHROPIC_API_KEY
     - Google Gemini: GEMINI_API_KEY
   - Providers are auto-detected by key presence (or pass --providers to choose manually).

2) (Optional) Edit config/brands.json and data/queries.csv
   - data/queries.csv must contain a column named query (see the included sample).
   - config/outlet_domain_map.json maps domains → outlet names for better normalization.

3) Set up a virtual environment and install dependencies
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4) Run the audit (network calls = potential cost)
   ```bash
   python3 scripts/run_audit.py --providers auto --verbose
   ```
   - Output CSVs will be written to output/:
     - output/citations_raw.csv
     - output/outlet_counts.csv

5) Generate the PDF report
   ```bash
   python3 scripts/generate_pdf.py --title "ELC AI Visibility Audit — Estée Lauder Companies" --top-n 15 --verbose
   ```
   - Your report will appear at: output/ELC_AI_Visibility_Audit.pdf

Providers and behavior
- Perplexity (preferred for explicit citations)
  - Returns source URLs; we extract domains and map to normalized outlet names via config/outlet_domain_map.json.
- OpenAI / Anthropic / Gemini (simulated outlets)
  - These do not reliably expose citations. We prompt them to enumerate likely outlets (signal‑only); results are treated as outlet names.
- Auto detection and manual selection
  - Default is --providers auto (enable any provider with a configured key).
  - You can force a set with --providers perplexity,openai,anthropic,gemini (comma separated).
- Caching, retries, and delays
  - Simple on‑disk cache at output/.cache (TTL default 86400s).
  - Retries use exponential backoff; delay between queries is configurable.
  - All of these are tunable via CLI flags (see below).

CLI reference

Data collection: scripts/run_audit.py
```text
--queries-file PATH      CSV with a 'query' column (default: data/queries.csv)
--output-dir PATH        Directory to write outputs (default: output/)
--config-dir PATH        Directory with .env and config JSONs (default: config/)
--providers STR          'auto' or comma list: perplexity,openai,anthropic,gemini (default: auto)
--delay FLOAT            Delay in seconds between queries (default: 0.25)
--retries INT            HTTP retry attempts per call (default: 2)
--backoff FLOAT          Initial backoff seconds (exponential) (default: 0.5)
--cache-dir PATH         On-disk cache directory (default: output/.cache)
--cache-ttl INT          Cache TTL in seconds (-1 to disable TTL expiration) (default: 86400)
--limit INT              Limit number of queries processed (default: None)
--verbose                Verbose logging
```

Report generation: scripts/generate_pdf.py
```text
--counts-file PATH       Path to outlet counts CSV (default: output/outlet_counts.csv)
--output-file PATH       Output PDF path (default: output/ELC_AI_Visibility_Audit.pdf)
--title STR              Report title (default: "AI Visibility Audit — Estée Lauder Companies")
--top-n INT              Number of top outlets to include (default: 15)
--verbose                Verbose logging
```

Data and configuration
- data/queries.csv
  - List of questions to query. You can narrow with --limit while testing.
- config/prompts.json
  - Prompt templates for OpenAI/Anthropic. Gemini reuses these templates.
- config/outlet_domain_map.json
  - Maps domains to display outlet names (e.g., wsj.com → Wall Street Journal). Extend this for better normalization.
- config/brands.json
  - Brand, aliases, competitors (informational; not directly used in the current pipeline, but useful for future extensions).

Notes and costs
- Network calls may incur API costs. Use --limit during testing and leverage caching (default TTL = 24 hours).
- If a key is missing, that provider is skipped and the pipeline still produces an aggregate from available data.

Troubleshooting
- No data / empty CSV:
  - Ensure at least one provider key is set in config/.env and that queries.csv has a query column.
- Rate limiting or network errors:
  - Increase --delay, reduce --limit, or raise --retries slightly.
- Unexpected outlet names:
  - Extend config/outlet_domain_map.json to normalize more domains, and simulated outlet names are normalized to title case (short acronyms preserved).
- Clear cache:
  - Remove output/.cache or use a different --cache-dir. Set --cache-ttl -1 to disable TTL expiry checks.
- Virtual environment issues (macOS):
  - Ensure you used python3 -m venv .venv and source .venv/bin/activate before installing.
