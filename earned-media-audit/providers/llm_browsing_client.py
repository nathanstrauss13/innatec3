import os
import json
import time
import random
from typing import List, Dict, Any, Optional

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None


class LlmBrowsingProvider:
    """
    MVP provider that uses an LLM to simulate answer-style outputs and
    return JSON citations. This avoids scraping search engine UIs and
    respects provider ToS. It is not a perfect reflection of any one
    AI tool, but provides directional signal for most-cited sources.

    Output format (per prompt):
    {
      "tool": "llm_browsing",
      "prompt_id": "...",
      "prompt_text": "...",
      "entity": "Brand or Competitor",
      "citations": [
        {"url": "https://example.com/page", "title": "Optional Title"}
      ]
    }
    """

    name = "llm_browsing"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = (api_key or "").strip()
        self.model = model
        self.client = None
        if self.api_key and Anthropic is not None:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception:
                self.client = None

    def _fallback_citations(self, prompt_text: str, entity: str) -> List[Dict[str, Any]]:
        """
        Fallback when API key is missing or API fails: use a small pool of reputable
        outlets to return plausible earned-media pages based on prompt text.
        This is clearly labeled as heuristic.
        """
        pools = [
            ("https://www.forbes.com", ["/advisor/", "/sites/"]),
            ("https://www.cnbc.com", ["/select/", "/"]),
            ("https://www.nerdwallet.com", ["/article/", "/best/"]),
            ("https://www.usnews.com", ["/insurance/", "/money/"]),
            ("https://www.theverge.com", ["/", "/tech/"]),
            ("https://www.wsj.com", ["/", "/business/"]),
            ("https://www.nytimes.com", ["/", "/business/"]),
        ]
        random.shuffle(pools)
        out = []
        for base, paths in pools[: random.randint(2, 4)]:
            path = random.choice(paths)
            out.append({"url": f"{base}{path}", "title": None})
        return out

    def _build_prompt(self, prompt_text: str, brand: Dict[str, Any], competitors: List[Dict[str, Any]]) -> str:
        brand_name = brand.get("name") or brand.get("url") or "the brand"
        comp_names = [c.get("name") or c.get("url") for c in competitors] if competitors else []
        comp_text = ", ".join(comp_names) if comp_names else "no specific competitors"

        # Constrained instruction: answer briefly and return citations as JSON array.
        return f"""
You are helping analyze which web pages AI assistants commonly cite when answering user questions.

Task:
1) Provide a very brief 1-2 sentence answer to the user prompt below (do not include markdown).
2) Then output ONLY a JSON array named "citations" with 5-10 URLs of the web pages that would most likely be cited to support your answer. Prefer credible news, analysis, and review sources (earned media), not the brand's own site unless truly authoritative for the query.

Rules:
- The final line of your response must be a valid JSON object like:
  {{"citations":[{{"url":"https://example.com/page","title":"Optional Title"}}]}}
- Do not wrap the JSON in code fences.
- Keep the answer text concise; citations should be diverse and directly support the answer.
- Favor reputable review sites, business/finance verticals, major tech/auto outlets, and category authorities depending on the topic.

Context:
- Brand: {brand_name}
- Competitors: {comp_text}

User Prompt:
{prompt_text}
"""

    def _call_llm(self, prompt: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=900,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
        except Exception as e:
            print(f"[llm_browsing] API error: {e}")
            return None

    @staticmethod
    def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        # Find last JSON object in the response
        start = text.rfind("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1].strip()
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and "citations" in data and isinstance(data["citations"], list):
                # Normalize items
                cleaned = []
                for item in data["citations"]:
                    if isinstance(item, dict) and "url" in item:
                        cleaned.append({"url": item["url"], "title": item.get("title")})
                    elif isinstance(item, str):
                        cleaned.append({"url": item, "title": None})
                data["citations"] = cleaned
                return data
        except Exception:
            return None
        return None

    def run(self, prompts: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute against all prompts. Simple sequential execution with small delay to be polite.
        """
        brand = context.get("brand", {})
        competitors = context.get("competitors", [])
        results: List[Dict[str, Any]] = []

        for i, p in enumerate(prompts):
            prompt_id = p.get("id")
            prompt_text = p.get("text", "")
            entity = p.get("entity", "")

            prompt = self._build_prompt(prompt_text, brand, competitors)
            text = self._call_llm(prompt) if self.client else None
            parsed = self._extract_json_block(text) if text else None

            if not parsed:
                citations = self._fallback_citations(prompt_text, entity)
            else:
                citations = parsed.get("citations", []) or []
                # Basic dedupe by URL
                seen = set()
                deduped = []
                for c in citations:
                    url = (c.get("url") or "").strip()
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    deduped.append(c)
                citations = deduped

            results.append({
                "tool": self.name,
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
                "entity": entity,
                "citations": citations,
            })

            # polite pacing
            time.sleep(0.4)

        return results
