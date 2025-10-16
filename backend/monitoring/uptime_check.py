"""
Simple uptime check script for Phase 6.

Usage:
    python -m backend.monitoring.uptime_check http://localhost:8000/health
"""

import sys
import time
import json
from urllib import request, error


def check(url: str, timeout: float = 2.0) -> dict:
    start = time.perf_counter()
    try:
        with request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            elapsed = (time.perf_counter() - start) * 1000
            return {
                "ok": resp.status == 200,
                "status": resp.status,
                "elapsed_ms": round(elapsed, 2),
                "body": body,
            }
    except error.URLError as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {"ok": False, "error": str(e), "elapsed_ms": round(elapsed, 2)}


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/health"
    result = check(url)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
