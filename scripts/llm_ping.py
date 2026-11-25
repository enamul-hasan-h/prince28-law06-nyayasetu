"""Send one direct HTTP request to each configured LLM provider."""

import time

import httpx

from nyayasetu.config import get_settings


def ping(name: str, base_url: str, api_key: str, model: str) -> bool:
    if not api_key:
        print(f"{name:<8} SKIPPED  API key is not configured")
        return False

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly one word: pong"}],
        "max_tokens": 256,
        "stream": False,
    }

    started = time.perf_counter()

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        response.raise_for_status()
        data = response.json()

        answer = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)

        print(
            f"{name:<8} OK       {model} said {answer!r} "
            f"in {elapsed_ms} ms, tokens in={tokens_in} out={tokens_out}"
        )
        return True

    except httpx.HTTPStatusError as exc:
        print(f"{name:<8} FAILED   HTTP {exc.response.status_code}: {exc.response.text[:400]}")
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        print(f"{name:<8} FAILED   {type(exc).__name__}: {exc}")

    return False


def main() -> None:
    settings = get_settings()

    print("Testing LLM providers directly (without the gateway)...")
    print()

    gemini_ok = ping(
        "gemini",
        settings.llm_primary_base_url,
        settings.gemini_api_key,
        settings.llm_primary_model,
    )

    groq_ok = ping(
        "groq",
        settings.llm_fallback_base_url,
        settings.groq_api_key,
        settings.llm_fallback_model,
    )

    print()
    print(f"Gemini: {'PASS' if gemini_ok else 'FAIL'}")
    print(f"Groq:   {'PASS' if groq_ok else 'FAIL'}")


if __name__ == "__main__":
    main()
