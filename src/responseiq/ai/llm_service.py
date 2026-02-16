import json
from typing import Any, Dict, Optional

import httpx

from responseiq.config.settings import settings
from responseiq.utils.logger import logger


async def analyze_with_llm(log_text: str, code_context: str = "") -> Optional[Dict[str, Any]]:
    """
    Analyzes log using OpenAI API if available, or local mock LLM as fallback.
    Returns structured data if successful, None if disabled or fails.
    Asynchronous version for high-throughput processing.
    """
    # Try OpenAI first if API key is available
    if settings.openai_api_key:
        result = await _analyze_with_openai(log_text, code_context)
        if result is not None:
            return result
        logger.warning("OpenAI analysis failed, falling back to local mock LLM")

    # Fall back to local mock LLM
    use_local_fallback = getattr(settings, "use_local_llm_fallback", True)
    if use_local_fallback:
        logger.info("🤖 Using local mock LLM for incident analysis")
        from responseiq.ai.local_llm_service import analyze_with_local_llm

        return await analyze_with_local_llm(log_text, code_context)

    logger.debug("AI analysis disabled - no OpenAI key and local fallback disabled")
    return None


async def _analyze_with_openai(log_text: str, code_context: str = "") -> Optional[Dict[str, Any]]:
    """
    Internal function to analyze using OpenAI API specifically.
    Returns structured data if successful, None if fails.
    """
    if not settings.openai_api_key:
        return None

    api_key = settings.openai_api_key.get_secret_value()

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Enrich the prompt with source code if available
    final_user_content = f"Log content: {log_text}"
    if code_context:
        final_user_content += f"\n\n{code_context}"
        logger.info("Enriched AI Prompt with Source Code Context")

    # Prompt asking for specific JSON format to ensure compatibility
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a DevOps Incident Analyzer. Analyze the log AND the provided source code context. "
                    "Pinpoint the exact line of code causing the issue if visible. "
                    "Return a JSON object with keys: 'title' (string), "
                    "'severity' (low/medium/high), 'description' (string), "
                    "'remediation' (string). The remediation should be a precise code change if possible. "
                    "Do not add markdown formatting."
                ),
            },
            {"role": "user", "content": final_user_content},
        ],
        "temperature": 0.0,
        "max_tokens": 300,  # Increased tokens for detailed code fixes
    }

    try:
        # Use Async Client with context manager
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
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
        logger.warning(f"LLM Connection Error: {str(e)}. Falling back to local parsers.")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in LLM analysis: {str(e)}")
        return None


async def generate_reproduction_code(incident_summary: str, relevant_code: str) -> Optional[str]:
    """
    Asks the LLM to generate a standalone pytest script that reproduces the incident.
    Returns the raw Python code (string) or None if it fails.
    """
    if not settings.openai_api_key:
        logger.warning("OpenAI API Key missing. Cannot generate reproduction code.")
        return None

    api_key = settings.openai_api_key.get_secret_value()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = (
        "You are an expert QA Automation Engineer. "
        "Your goal is to write a standalone Python script using `pytest` that REPRODUCES the bug described below. "
        "The test MUST FAIL when run against the current code (representing the bug), "
        "and PASS only after the bug is fixed.\n\n"
        f"INCIDENT SUMMARY:\n{incident_summary}\n\n"
        f"RELEVANT SOURCE CODE:\n{relevant_code}\n\n"
        "INSTRUCTIONS:\n"
        "1. Return ONLY the python code. No markdown, no explanations.\n"
        "2. Use standard `pytest` syntax.\n"
        "3. Assert the specific error condition found in the incident summary.\n"
        "4. Mock external dependencies (network, db, filesystem) where appropriate, using `unittest.mock`.\n"
        "5. The test should be self-contained and ready to run."
    )

    payload = {
        "model": "gpt-4-turbo-preview",  # Use a better model for code generation
        "messages": [
            {"role": "system", "content": "You are a Python focused QA Automation Expert."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                # Clean up markdown if the LLM ignores instructions
                if content.startswith("```python"):
                    content = content.replace("```python", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                return content
            else:
                logger.error(f"Failed to generate reproduction code: {response.text}")
                return None

    except Exception as e:
        logger.exception(f"Error generating reproduction code: {e}")
        return None
