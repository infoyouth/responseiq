import json
from typing import Any, Dict, Optional

import httpx

from src.config.settings import settings
from src.utils.logger import logger


def analyze_with_llm(log_text: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes log using OpenAI API if available.
    Returns structured data if successful, None if configured to skip or fails.
    Synchronous version for compatibility with current background worker threads.
    """
    if not settings.openai_api_key:
        logger.debug("OpenAI API key not set. Skipping AI analysis.")
        return None

    api_key = settings.openai_api_key.get_secret_value()

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Prompt asking for specific JSON format to ensure compatibility
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a DevOps Incident Analyzer. Analyze the log. "
                    "Return a JSON object with keys: 'title' (string), "
                    "'severity' (low/medium/high), 'description' (string), "
                    "'remediation' (string). Do not add markdown formatting."
                ),
            },
            {"role": "user", "content": f"Log content: {log_text}"},
        ],
        "temperature": 0.0,
        "max_tokens": 150,
    }

    try:
        # Use sync Client
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("LLM returned non-JSON response", response=content)
                    return {
                        "title": "AI Insight (Unstructured)",
                        "severity": "medium",
                        "description": content,
                        "remediation": "Check logs for details",
                    }

            elif response.status_code == 401:
                logger.error("OpenAI API Key Invalid. Please check configuration.")
                return None
            else:
                logger.warning(f"OpenAI API Error: {response.status_code}")
                return None

    except httpx.RequestError as e:
        logger.warning(
            f"LLM Connection Error: {str(e)}. Falling back to local parsers."
        )
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in LLM analysis: {str(e)}")
        return None
