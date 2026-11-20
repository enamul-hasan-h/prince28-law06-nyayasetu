"""Smoke-test the deployed NyayaSetu API."""

import argparse
import json
import time
import urllib.error
import urllib.request


def request_json(url: str) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def smoke_test(base_url: str, expected_version: str | None) -> bool:
    base_url = base_url.rstrip("/")
    checks = {
        "health": f"{base_url}/health",
        "ready": f"{base_url}/ready",
        "documents": f"{base_url}/v1/documents?limit=1",
    }

    for attempt in range(1, 31):
        try:
            health_status, health = request_json(checks["health"])
            ready_status, ready = request_json(checks["ready"])
            documents_status, _ = request_json(checks["documents"])

            if health_status != 200:
                raise RuntimeError(f"/health returned HTTP {health_status}")
            if ready_status != 200 or ready.get("status") != "ready":
                raise RuntimeError(f"/ready check failed: {ready}")
            if ready.get("checks", {}).get("database") is not True:
                raise RuntimeError("Database readiness check failed")
            if documents_status != 200:
                raise RuntimeError(f"/v1/documents returned HTTP {documents_status}")

            actual_version = health.get("git_sha")
            if expected_version and actual_version != expected_version:
                raise RuntimeError(
                    f"Version mismatch: expected {expected_version}, received {actual_version}"
                )

            print(f"PASS /health: HTTP {health_status}")
            print(f"PASS /ready: HTTP {ready_status}, database connected")
            print(f"PASS /v1/documents: HTTP {documents_status}")
            print(f"PASS deployed git SHA: {actual_version}")
            print("Smoke test passed.")
            return True

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            RuntimeError,
        ) as error:
            print(f"Attempt {attempt}/30: {error}")
            if attempt < 30:
                time.sleep(10)

    print("Smoke test failed after 30 attempts.")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Base URL of the deployed API")
    parser.add_argument("--expect-version", help="Expected deployed Git SHA")
    args = parser.parse_args()

    if not smoke_test(args.base_url, args.expect_version):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
