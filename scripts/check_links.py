#!/usr/bin/env python3
"""Check paper, code, and project URLs and optionally persist audit results."""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = (
    "Awesome-Agent-RSI-LinkAudit/0.1 "
    "(curated academic metadata; one-time validation)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/papers.json"))
    parser.add_argument("--audit", type=Path, default=Path("data/link_audit.json"))
    parser.add_argument(
        "--kinds",
        default="paper,code,project",
        help="Comma-separated artifact kinds to check.",
    )
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write statuses back to papers.json as well as link_audit.json.",
    )
    parser.add_argument(
        "--fail-on-dead",
        action="store_true",
        help="Fail for HTTP 404/410 or repeated connection failures.",
    )
    return parser.parse_args()


def request_once(url: str, timeout: float) -> tuple[int | None, str, str | None]:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"}
    request = Request(url, headers=headers, method="HEAD")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl(), None
    except HTTPError as error:
        if error.code not in {400, 403, 405}:
            return error.code, error.geturl() or url, str(error)
    except (URLError, TimeoutError, socket.timeout, ssl.SSLError) as error:
        return None, url, f"{type(error).__name__}: {error}"
    request = Request(
        url,
        headers={**headers, "Range": "bytes=0-0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read(1)
            return response.status, response.geturl(), None
    except HTTPError as error:
        return error.code, error.geturl() or url, str(error)
    except (URLError, TimeoutError, socket.timeout, ssl.SSLError) as error:
        return None, url, f"{type(error).__name__}: {error}"


def classify(status: int | None, error: str | None, redirected: bool) -> str:
    if status is not None and 200 <= status < 400:
        return "redirected" if redirected else "verified"
    if status == 429:
        return "rate_limited"
    if status in {401, 403, 451}:
        return "blocked"
    if status in {404, 410}:
        return "invalid"
    if status is not None:
        return "unreachable"
    if error:
        return "unreachable"
    return "invalid"


def check_url(
    url: str, timeout: float, retries: int
) -> tuple[str, dict[str, Any]]:
    status: int | None = None
    final_url = url
    error: str | None = None
    for attempt in range(retries + 1):
        status, final_url, error = request_once(url, timeout)
        if status is not None and (status < 500 or status in {501, 505}):
            break
        if attempt < retries:
            time.sleep(0.5 * (attempt + 1))
    redirected = final_url.rstrip("/") != url.rstrip("/")
    return (
        url,
        {
            "status": classify(status, error, redirected),
            "http_status": status,
            "final_url": final_url,
            "checked_at": date.today().isoformat(),
            "error": error,
        },
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.writelines((serialized, "\n"))
    temporary.replace(path)


def main() -> None:
    args = parse_args()
    kinds = {item.strip() for item in args.kinds.split(",") if item.strip()}
    with args.catalog.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    works = catalog["works"]
    urls = sorted(
        {
            artifact["url"]
            for work in works
            for artifact in work.get("artifacts", [])
            if artifact["kind"] in kinds
        }
    )
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {
            executor.submit(
                check_url, url, args.timeout, max(0, args.retries)
            ): url
            for url in urls
        }
        for future in as_completed(futures):
            url, result = future.result()
            results[url] = result

    counts = Counter(result["status"] for result in results.values())
    dead = sorted(
        url
        for url, result in results.items()
        if result["status"] in {"invalid", "unreachable"}
    )
    audit = {
        "checked_at": date.today().isoformat(),
        "artifact_kinds": sorted(kinds),
        "url_count": len(urls),
        "status_counts": dict(counts),
        "dead_urls": dead,
        "results": dict(sorted(results.items())),
    }
    write_json(args.audit, audit)

    if args.write:
        for work in works:
            statuses: list[str] = []
            for artifact in work.get("artifacts", []):
                result = results.get(artifact["url"])
                if not result:
                    continue
                artifact["verification_status"] = result["status"]
                artifact["verified_at"] = result["checked_at"]
                artifact["http_status"] = result["http_status"]
                statuses.append(result["status"])
            if not statuses:
                continue
            work["curation"]["last_verified_at"] = date.today().isoformat()
            if all(status in {"verified", "redirected"} for status in statuses):
                work["curation"]["link_status"] = "verified"
            elif any(status in {"invalid", "unreachable"} for status in statuses):
                work["curation"]["link_status"] = "issues_detected"
            else:
                work["curation"]["link_status"] = "partially_verified"
        write_json(args.catalog, catalog)

    print(
        json.dumps(
            {
                "url_count": len(urls),
                "status_counts": dict(counts),
                "dead_url_count": len(dead),
                "audit": str(args.audit),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.fail_on_dead and dead:
        sys.exit(1)


if __name__ == "__main__":
    main()
