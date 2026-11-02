"""Multi-provider LLM enhancement (Google Gemini, OpenAI, Anthropic, or Local rule-based)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests


def get_active_provider() -> str:
    """Return the currently configured LLM provider name or 'none'."""
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "none"


def llm_available() -> bool:
    """Return True if any supported LLM provider API key is configured."""
    return get_active_provider() != "none"


def _extract_json_block(text: str) -> dict[str, Any] | None:
    """Safely extract JSON object from markdown code fence or raw string."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # Try finding first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def _call_gemini(api_key: str, prompt_json: dict[str, Any], model: str = "gemini-1.5-flash") -> list[dict[str, Any]] | None:
    """Call Google Gemini generateContent REST endpoint."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    system_instruction = (
        "You are an elite pitch deck and presentation coach. "
        "Improve slide titles, bullet copy, and spoken narration for maximum clarity, punch, and executive impact. "
        "Strictly preserve verified facts without hallucinating unverified claims. "
        "Output ONLY valid JSON with structure: {\"slides\": [{\"number\": 1, \"title\": \"...\", \"bullets\": [\"...\"], \"speaker_notes\": \"...\"}]}"
    )
    user_prompt = f"{system_instruction}\n\nProject: {prompt_json['project_name']}\nArchetype: {prompt_json.get('archetype', 'investor')}\n\nOriginal slides:\n{json.dumps(prompt_json['slides'], indent=2)}"

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3,
        },
    }
    response = requests.post(url, json=payload, timeout=45)
    if response.status_code >= 400:
        return None
    data = response.json()
    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    parsed = _extract_json_block(text)
    if parsed and isinstance(parsed.get("slides"), list):
        return parsed["slides"]
    return None


def _call_openai(api_key: str, prompt_json: dict[str, Any], model: str = "gpt-4o-mini") -> list[dict[str, Any]] | None:
    """Call OpenAI or OpenAI-compatible endpoint."""
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "You improve pitch slide copy for executive presentations. "
        "Keep the exact number of slides and meaning, sharpening bullet impact and speaker notes pacing. "
        "Do not invent facts that aren't evidenced in the input. "
        "Return JSON only: {\"slides\": [{\"number\":1, \"title\":\"...\", \"bullets\":[...], \"speaker_notes\":\"...\"}]}"
    )
    payload = {
        "model": model,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(prompt_json)},
        ],
    }
    response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=45)
    if response.status_code >= 400:
        return None
    content = response.json()["choices"][0]["message"]["content"]
    parsed = _extract_json_block(content)
    if parsed and isinstance(parsed.get("slides"), list):
        return parsed["slides"]
    return None


def _call_anthropic(api_key: str, prompt_json: dict[str, Any], model: str = "claude-3-5-sonnet-20241022") -> list[dict[str, Any]] | None:
    """Call Anthropic Messages REST endpoint."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    user_prompt = (
        f"You are an expert pitch deck advisor. Polish this presentation for high clarity and flow.\n"
        f"Project: {prompt_json['project_name']}\n"
        f"Input slides:\n{json.dumps(prompt_json['slides'], indent=2)}\n\n"
        f"Output MUST be raw JSON: {{\"slides\": [ {{\"number\": 1, \"title\": \"...\", \"bullets\": [...], \"speaker_notes\": \"...\"}} ]}}"
    )
    payload = {
        "model": model,
        "max_tokens": 3000,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    response = requests.post(url, headers=headers, json=payload, timeout=45)
    if response.status_code >= 400:
        return None
    content = response.json().get("content", [{}])[0].get("text", "")
    parsed = _extract_json_block(content)
    if parsed and isinstance(parsed.get("slides"), list):
        return parsed["slides"]
    return None


def enhance_slide_copy(
    slides: list[dict[str, Any]],
    project_name: str,
    archetype: str = "investor",
) -> list[dict[str, Any]] | None:
    """
    Polishes slide titles, bullets, and speaker notes via the active LLM provider.
    Gracefully returns None on failure or unavailability so the caller retains rule-based slides.
    """
    provider = get_active_provider()
    if provider == "none":
        return None

    prompt_data = {
        "project_name": project_name,
        "archetype": archetype,
        "slides": slides,
    }

    enhanced: list[dict[str, Any]] | None = None
    try:
        if provider == "gemini":
            gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            enhanced = _call_gemini(gemini_key, prompt_data, model=gemini_model)
        elif provider == "openai":
            openai_key = os.getenv("OPENAI_API_KEY", "")
            openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            enhanced = _call_openai(openai_key, prompt_data, model=openai_model)
        elif provider == "anthropic":
            anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
            anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            enhanced = _call_anthropic(anthropic_key, prompt_data, model=anthropic_model)

        if not enhanced or len(enhanced) != len(slides):
            return None

        # Merge enhancements onto original slide structures to guarantee duration and metadata integrity
        merged: list[dict[str, Any]] = []
        for original, update in zip(slides, enhanced):
            item = dict(original)
            if isinstance(update.get("title"), str) and update["title"].strip():
                item["title"] = update["title"].strip()
            if isinstance(update.get("bullets"), list) and update["bullets"]:
                item["bullets"] = [str(b).strip() for b in update["bullets"] if str(b).strip()]
            if isinstance(update.get("speaker_notes"), str) and update["speaker_notes"].strip():
                item["speaker_notes"] = update["speaker_notes"].strip()
            merged.append(item)
        return merged
    except Exception:
        return None
