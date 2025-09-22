import os
import re
import json
import time
import uuid
from collections import Counter, defaultdict
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from providers.llm_browsing_client import LlmBrowsingProvider
from providers.perplexity_client import PerplexityProvider
from providers.openai_client import OpenAIProvider
from providers.gemini_client import GeminiProvider


def normalize_url(url: str) -> str:
    """Normalize URL by stripping tracking params and fragments."""
    try:
        parsed = urlparse(url.strip())
        # Remove fragments
        fragmentless = parsed._replace(fragment="")
        # Strip common tracking params
        qs = dict(parse_qsl(fragmentless.query, keep_blank_values=False))
        tracking_keys = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "gclid",
            "fbclid",
            "igshid",
            "mc_cid",
            "mc_eid",
            "mkt_tok",
        }
        for k in list(qs.keys()):
            if k.lower() in tracking_keys or k.lower().startswith("utm_"):
                qs.pop(k, None)
        new_query = urlencode(qs, doseq=True)
        cleaned = fragmentless._replace(query=new_query)
        return urlunparse(cleaned)
    except Exception:
        return url


def extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def load_domain_categories():
    """Load publisher domain categories from news-analyzer/config if available."""
    categories = {}
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg_dir = os.path.join(root, "news-analyzer", "config")

    def load_list(fname, label):
        path = os.path.join(cfg_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Files may be arrays or wrapped
            domains = []
            if isinstance(data, dict):
                # pick first key's list
                for v in data.values():
                    if isinstance(v, list):
                        domains = v
                        break
            elif isinstance(data, list):
                domains = data
            for d in domains:
                categories[d.lower()] = label
        except Exception:
            # It's okay if files aren't present
            pass

    load_list("domains_tier1.json", "Tier1")
    load_list("domains_pr.json", "PR")
    load_list("domains_community.json", "Community")
    load_list("domains_aggregators.json", "Aggregator")
    return categories


class EarnedAnalyzer:
    """Orchestrates prompts, provider calls, and aggregation for Earned Media Audit."""

    def __init__(self, anthropic_api_key: str | None, providers: list[str] | None = None):
        self.anthropic_api_key = anthropic_api_key
        self.provider_names = providers or ["llm_browsing"]
        self.domain_categories = load_domain_categories()
        self.providers = self._init_providers()

    def _init_providers(self):
        providers = []
        for name in self.provider_names:
            if name == "llm_browsing":
                providers.append(LlmBrowsingProvider(api_key=self.anthropic_api_key))
            elif name == "perplexity":
                providers.append(PerplexityProvider(api_key=os.environ.get("PERPLEXITY_API_KEY")))
            elif name == "openai":
                providers.append(OpenAIProvider(api_key=os.environ.get("OPENAI_API_KEY")))
            elif name == "gemini":
                providers.append(GeminiProvider(api_key=os.environ.get("GEMINI_API_KEY")))
            # Future: add brave_client UI automation behind config flags
        return providers

    def _infer_core_category_hints(self, brand_name: str) -> list[str]:
        """Very lightweight hints to slightly steer intent generation."""
        name = brand_name.lower()
        hints = []
        if any(k in name for k in ["card", "amex", "visa", "mastercard", "chase", "capital one", "citi"]):
            hints = ["credit cards", "rewards", "signup bonuses"]
        elif any(k in name for k in ["run", "shoe", "nike", "hoka", "brooks", "asics", "sneaker"]):
            hints = ["running shoes", "stability shoes", "marathon gear"]
        elif any(k in name for k in ["ev", "tesla", "rivian", "polestar", "lucid", "electric"]):
            hints = ["electric vehicles", "range", "charging", "cargo capacity"]
        return hints

    def _generate_intents(self, brand: dict, competitors: list[dict], query_budget: int) -> list[dict]:
        """80/20 split: general-intent vs media-centric prompts across brand and competitors."""
        entities = [brand] + competitors
        n_entities = max(1, len(entities))
        # Reserve some comparison prompts separately
        compare_slots = min(len(competitors), max(1, query_budget // 6))
        remaining = max(1, query_budget - compare_slots)

        general_count = max(1, int(remaining * 0.8))
        media_count = max(0, remaining - general_count)

        # Distribute per entity
        per_entity_general = max(1, general_count // n_entities)
        per_entity_media = max(1, media_count // n_entities) if media_count else 0

        prompts: list[dict] = []
        # General-intent patterns
        general_templates = [
            "best {hint}",
            "top {hint} for {use_case}",
            "{brand} vs top alternatives in {hint}",
            "is {brand} worth it for {hint}",
            "{brand} review in the context of {hint}",
        ]
        use_cases = ["value", "beginners", "experts", "families", "performance", "2025"]

        # Media-centric patterns
        media_templates = [
            "who covers {brand} in {hint}, cite sources",
            "best articles about {brand} for {hint}, cite sources",
            "background and FAQ resources for {brand} in {hint}, cite sources",
        ]

        # Build entity-specific prompts
        for ent in entities:
            name = ent.get("name") or ent.get("url") or "brand"
            hints = self._infer_core_category_hints(name) or ["the category"]
            # general
            g_added = 0
            for t in general_templates:
                if g_added >= per_entity_general:
                    break
                for h in hints:
                    if g_added >= per_entity_general:
                        break
                    uc = use_cases[g_added % len(use_cases)]
                    text = t.format(brand=name, hint=h, use_case=uc)
                    prompts.append({
                        "id": str(uuid.uuid4())[:8],
                        "entity": name,
                        "entity_type": "brand" if ent is entities[0] else "competitor",
                        "kind": "general",
                        "text": text
                    })
                    g_added += 1
            # media
            m_added = 0
            for t in media_templates:
                if m_added >= per_entity_media:
                    break
                for h in hints:
                    if m_added >= per_entity_media:
                        break
                    text = t.format(brand=name, hint=h)
                    prompts.append({
                        "id": str(uuid.uuid4())[:8],
                        "entity": name,
                        "entity_type": "brand" if ent is entities[0] else "competitor",
                        "kind": "media",
                        "text": text
                    })
                    m_added += 1

        # Comparison prompts brand vs each competitor
        brand_name = brand.get("name") or "brand"
        for comp in competitors[:compare_slots]:
            comp_name = comp.get("name") or "competitor"
            comp_prompts = [
                f"{brand_name} vs {comp_name} — pros and cons; cite sources",
                f"alternatives to {brand_name} and {comp_name}; cite sources",
            ]
            for text in comp_prompts:
                prompts.append({
                    "id": str(uuid.uuid4())[:8],
                    "entity": f"{brand_name} vs {comp_name}",
                    "entity_type": "comparison",
                    "kind": "general",
                    "text": text
                })

        # Cap to budget
        if len(prompts) > query_budget:
            prompts = prompts[:query_budget]
        return prompts

    def _categorize(self, domain: str, brand_domain_whitelist: set[str], competitor_domain_whitelist: set[str]) -> str:
        if domain in brand_domain_whitelist:
            return "Owned"
        if domain in competitor_domain_whitelist:
            return "Competitor Owned"
        return self.domain_categories.get(domain, "Unknown")

    def run_audit(self, job_id: str, brand: dict, competitors: list[dict], query_budget: int = 25) -> dict:
        started = time.time()
        prompts = self._generate_intents(brand, competitors, query_budget)

        # Provider execution
        runs = []
        for provider in self.providers:
            run = provider.run(prompts=prompts, context={
                "brand": brand,
                "competitors": competitors,
            })
            runs.extend(run or [])

        # Aggregate citations
        domain_counts = Counter()
        page_counts = Counter()
        domain_provider_coverage = defaultdict(set)  # domain -> set(providers)
        page_provider_coverage = defaultdict(set)

        # Per-entity
        entity_domain_counts = defaultdict(Counter)
        entity_page_counts = defaultdict(Counter)

        # Owned domains to tag categories
        def get_domain_from_url(u: str) -> str:
            return extract_domain(u)

        brand_domains = {extract_domain(brand.get("url", ""))} if brand.get("url") else set()
        competitor_domains = {extract_domain(c.get("url", "")) for c in competitors if c.get("url")}

        total_citations = 0
        citations_detailed = []  # store a sample to inspect later

        for run in runs:
            tool = run.get("tool", "unknown")
            prompt_id = run.get("prompt_id")
            prompt_text = run.get("prompt_text", "")
            entity = run.get("entity", "")
            citations = run.get("citations", []) or []
            clean_citations = []
            for c in citations:
                url = normalize_url(c.get("url", ""))
                if not url:
                    continue
                domain = get_domain_from_url(url)
                if not domain:
                    continue
                clean_citations.append({"url": url, "title": c.get("title"), "domain": domain})
                # Global
                domain_counts[domain] += 1
                page_counts[url] += 1
                domain_provider_coverage[domain].add(tool)
                page_provider_coverage[url].add(tool)
                # Per-entity
                entity_domain_counts[entity][domain] += 1
                entity_page_counts[entity][url] += 1
                total_citations += 1

            if clean_citations:
                citations_detailed.append({
                    "tool": tool,
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text,
                    "entity": entity,
                    "citations": clean_citations
                })

        # Build Top Domains / Pages
        top_domains = []
        for domain, cnt in domain_counts.most_common():
            category = self._categorize(domain, brand_domains, competitor_domains)
            top_domains.append({
                "domain": domain,
                "count": cnt,
                "share": round(cnt / total_citations, 4) if total_citations else 0.0,
                "providers": sorted(list(domain_provider_coverage[domain])),
                "category": category
            })

        top_pages = []
        for url, cnt in page_counts.most_common():
            domain = extract_domain(url)
            category = self._categorize(domain, brand_domains, competitor_domains)
            top_pages.append({
                "url": url,
                "domain": domain,
                "count": cnt,
                "share": round(cnt / total_citations, 4) if total_citations else 0.0,
                "providers": sorted(list(page_provider_coverage[url])),
                "category": category
            })

        # By-entity summaries (only include top N to keep payload + UI light)
        def top_n(counter: Counter, n=25):
            return [{"key": k, "count": v} for k, v in counter.most_common(n)]

        by_entity = {}
        for ent, dc in entity_domain_counts.items():
            by_entity[ent] = {
                "top_domains": top_n(dc, 25),
                "top_pages": top_n(entity_page_counts[ent], 25),
                "total_citations": int(sum(dc.values()))
            }

        # Gap analysis: competitor-only vs brand
        brand_label = brand.get("name") or brand.get("url") or "brand"
        brand_dom_set = set(entity_domain_counts.get(brand_label, {}))
        gaps_domains = []
        comp_aggregate = Counter()
        comp_presence = defaultdict(set)  # domain -> set(comp_name)

        for comp in competitors:
            comp_name = comp.get("name") or comp.get("url") or "competitor"
            comp_dc = entity_domain_counts.get(comp_name, Counter())
            for d, v in comp_dc.items():
                comp_aggregate[d] += v
                comp_presence[d].add(comp_name)

        for d, v in comp_aggregate.most_common():
            if d not in brand_dom_set:
                gaps_domains.append({
                    "domain": d,
                    "competitors": sorted(list(comp_presence[d])),
                    "competitor_citations": int(v),
                    "brand_citations": int(entity_domain_counts.get(brand_label, Counter()).get(d, 0)),
                    "delta": int(v - entity_domain_counts.get(brand_label, Counter()).get(d, 0)),
                    "category": self._categorize(d, brand_domains, competitor_domains)
                })

        finished = time.time()
        result = {
            "job_id": job_id,
            "input": {
                "brand": brand,
                "competitors": competitors,
                "query_budget": query_budget,
                "providers": [p.name for p in self.providers],
            },
            "meta": {
                "started_at": started,
                "finished_at": finished,
                "duration_sec": round(finished - started, 2),
                "total_prompts": len(prompts),
                "total_citations": total_citations
            },
            "prompts": prompts,
            "providers_used": [p.name for p in self.providers],
            "runs_sample": citations_detailed[:25],  # not all to keep payload reasonable
            "top_domains": top_domains,
            "top_pages": top_pages,
            "by_entity": by_entity,
            "gaps": {
                "domains": gaps_domains[:50]
            }
        }
        return result
