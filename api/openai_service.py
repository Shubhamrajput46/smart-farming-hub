"""Minimal secure OpenAI integration. Keep OPENAI_API_KEY on the server only."""
import json
import urllib.error
import urllib.request
from django.conf import settings

def ask_openai(prompt: str) -> str:
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    model = getattr(settings, "OPENAI_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": "You are AgroSmart, an agricultural information assistant. Give practical, cautious guidance and recommend local agricultural experts for high-risk crop decisions."},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    timeout = getattr(settings, "OPENAI_TIMEOUT", 30)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not leak the API key or raw provider response to clients.
        if exc.code in (401, 403):
            raise RuntimeError("OpenAI authentication/configuration failed.") from exc
        if exc.code == 429:
            raise RuntimeError("OpenAI rate limit or quota exceeded.") from exc
        raise RuntimeError("OpenAI service request failed.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Could not reach OpenAI. Please try again later.") from exc

    output = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text" and part.get("text"):
                    output.append(part["text"])
    answer = "\n".join(output).strip()
    if not answer:
        raise RuntimeError("OpenAI returned no text output.")
    return answer
