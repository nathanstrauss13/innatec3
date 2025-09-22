import os
import json
import time
import random
from typing import List, Dict, Any, Optional

import requests


class OpenAIProvider:
    """
    Provider using OpenAI Chat Completions API to produce concise answers and a JSON
    citations object.

    Env:
      OPENAI_API_KEY

    Output format (per prompt):
      {
        "tool": "openai",
        "prompt_id": "...",
        "prompt_text": "...",
        "entity": "Brand or Competitor",
        "citations": [{"url": "...", "title": None}]
      }
    """

    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = (api_key or os.environ.get("OPENAI_API_KEY") or "").strip()
        self.model = model
        self.enabled = bool(self.api_key)
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    @staticmethod
    def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        start = text.rfind("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1].strip()
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and "citations" in data and isinstance(data["citations"], list):
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

    def _build_prompt(self, prompt_text: str, brand: Dict[str, Any], competitors: List[Dict[str, Any]]) -> str:
        brand_name = brand.get("name") or brand.get("url") or "the brand"
        comp_names = [c.get("name") or c.get("url") for c in competitors] if competitors else []
        comp_text = ", ".join(comp_names) if comp_names else "no specific competitors"

        return f"""
You are helping analyze which web pages AI assistants commonly cite when answering user questions.

Task:
1) Provide a very brief 1-2 sentence answer to the user prompt below (no markdown).
2) Then output ONLY a JSON object with a key "citations" containing 5-10 URLs and optional titles, like:
   {{"citations":[{{"url":"https://example.com/page","title":"Optional Title"}}]}}

Rules:
- Final line must be valid JSON as shown above; do not wrap in code fences.
- Prefer reputable earned-media sources: reviews, business/finance verticals, news outlets, category authorities.
- Include the most directly supportive sources for the prompt.

Context:
- Brand: {brand_name}
- Competitors: {comp_text}

User Prompt:
{prompt_text}
"""

    def _call_api(self, prompt: str) -> Optional[dict]:
        if not self.enabled:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[openai] API error: {e}")
            return None

    def _parse_response(self, data: dict) -> Optional[List[Dict[str, Any]]]:
        if not data:
            return None
        try:
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            parsed = self._extract_json_block(content)
            if parsed and isinstance(parsed.get("citations"), list):
                return parsed["citations"]
        except Exception:
            return None
        return None

    def run(self, prompts: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        brand = context.get("brand", {})
        competitors = context.get("competitors", [])
        results: List[Dict[str, Any]] = []

        for p in prompts:
            prompt_id = p.get("id")
            prompt_text = p.get("text", "")
            entity = p.get("entity", "")

            citations: List[Dict[str, Any]] = []
            if self.enabled:
                api_prompt = self._build_prompt(prompt_text, brand, competitors)
                data = self._call_api(api_prompt)
                parsed = self._parse_response(data)
                if parsed:
                    # dedupe
                    seen = set()
                    for c in parsed:
                        url = (c.get("url") or "").strip()
                        if url and url not in seen:
                            seen.add(url)
                            citations.append({"url": url, "title": c.get("title")})

            results.append({
                "tool": self.name,
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
                "entity": entity,
                "citations": citations,
            })

            time.sleep(0.35 + random.random() * 0.2)

        return results
