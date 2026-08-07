#!/usr/bin/env python3
"""Validate catalog structure, deduplication, taxonomy, and manuscript coverage."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/papers.json"))
    parser.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/manuscript_manifest.json")
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return a non-zero status when warnings are present.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalized_title(title: str) -> str:
    value = unicodedata.normalize("NFKD", title)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def taxonomy_ids(taxonomy: dict[str, Any]) -> tuple[set[str], set[str]]:
    levels: set[str] = set()
    subcategories: set[str] = set()
    for level in taxonomy["levels"]:
        levels.add(level["id"])
        subcategories.update(item["id"] for item in level["subcategories"])
    subcategories.update(
        item["id"] for item in taxonomy.get("supporting_subcategories", [])
    )
    return levels, subcategories


def validate_url(url: str, field: str, work_id: str, errors: list[str]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{work_id}: {field} must be an absolute HTTPS URL: {url}")
    if parsed.netloc.lower() in {"git.woa.com", "localhost"}:
        errors.append(f"{work_id}: private URL is not publishable: {url}")


def main() -> None:
    args = parse_args()
    catalog = load_json(args.catalog)
    taxonomy = load_json(args.taxonomy)
    manifest = load_json(args.manifest)
    works: list[dict[str, Any]] = catalog["works"]
    valid_levels, valid_subcategories = taxonomy_ids(taxonomy)
    errors: list[str] = []
    warnings: list[str] = []

    ids: Counter[str] = Counter()
    arxiv_ids: Counter[str] = Counter()
    dois: Counter[str] = Counter()
    title_index: dict[str, list[str]] = defaultdict(list)
    bib_index: dict[str, dict[str, Any]] = {}
    # A work can be cited under several BibTeX keys when the bibliography holds
    # duplicate entries for it, so coverage is checked per cited key.
    cited_index: dict[str, dict[str, Any]] = {}

    for work in works:
        work_id = work.get("id")
        title = work.get("title")
        if not work_id or not title:
            errors.append("A work is missing id or title")
            continue
        ids[work_id] += 1
        title_index[normalized_title(title)].append(work_id)
        if work.get("arxiv_id"):
            arxiv_ids[work["arxiv_id"]] += 1
            expected_id = f"arxiv:{work['arxiv_id']}"
            if work_id != expected_id:
                errors.append(f"{work_id}: arXiv work ID must be {expected_id}")
        if work.get("doi"):
            dois[work["doi"].lower()] += 1
        level = work.get("primary_level")
        subcategory = work.get("primary_subcategory")
        if level is not None and level not in valid_levels:
            errors.append(f"{work_id}: invalid primary level {level}")
        if subcategory is not None and subcategory not in valid_subcategories:
            errors.append(f"{work_id}: invalid subcategory {subcategory}")
        if level and subcategory and not subcategory.startswith(f"{level}."):
            errors.append(
                f"{work_id}: subcategory {subcategory} does not belong to {level}"
            )
        if work.get("classification_status") not in {
            "strict",
            "facing",
            "mixed",
            "boundary",
            "supporting",
        }:
            errors.append(f"{work_id}: invalid classification status")
        urls: set[tuple[str, str]] = set()
        for artifact in work.get("artifacts", []):
            kind = artifact.get("kind")
            url = artifact.get("url")
            if not kind or not url:
                errors.append(f"{work_id}: artifact is missing kind or URL")
                continue
            validate_url(url, kind, work_id, errors)
            pair = (kind, url)
            if pair in urls:
                errors.append(f"{work_id}: duplicate artifact {kind} {url}")
            urls.add(pair)
        for field in ("paper_url", "code_url", "project_url"):
            value = work.get(field)
            if value:
                validate_url(value, field, work_id, errors)
        if work.get("paper_url") and (
            "paper",
            work["paper_url"],
        ) not in urls:
            errors.append(f"{work_id}: paper_url is absent from artifacts")
        if work.get("code_url") and ("code", work["code_url"]) not in urls:
            errors.append(f"{work_id}: code_url is absent from artifacts")
        if work.get("project_url") and (
            "project",
            work["project_url"],
        ) not in urls:
            errors.append(f"{work_id}: project_url is absent from artifacts")

        manuscript = work.get("manuscript", {})
        bib_key = manuscript.get("bib_key")
        cited_keys = manuscript.get("cited_bib_keys") or []
        if bib_key:
            if bib_key in bib_index:
                errors.append(
                    f"BibTeX key {bib_key} maps to both {bib_index[bib_key]['id']} and {work_id}"
                )
            bib_index[bib_key] = work
        for key in cited_keys:
            if cited_index.get(key, work) is not work:
                errors.append(
                    f"BibTeX key {key} maps to both {cited_index[key]['id']} and {work_id}"
                )
            cited_index[key] = work
        if manuscript.get("active") and not bib_key:
            errors.append(f"{work_id}: active work lacks a BibTeX key")
        if manuscript.get("active") and cited_keys != [bib_key]:
            errors.append(
                f"{work_id}: active work must map one-to-one to its primary "
                f"BibTeX key ({bib_key!r}), found {cited_keys!r}"
            )
        if not manuscript.get("active"):
            errors.append(
                f"{work_id}: catalog contains a work not used by the active manuscript"
            )
        if manuscript.get("representative") and not manuscript.get("active"):
            errors.append(f"{work_id}: representative work is not active")

        serialized = json.dumps(work, ensure_ascii=False)
        if re.search(r"/Users/|Zotero/storage|git\.woa\.com|@tencent\.com", serialized):
            errors.append(f"{work_id}: private or identity-bearing content detected")

    for label, counter in (
        ("work ID", ids),
        ("arXiv ID", arxiv_ids),
        ("DOI", dois),
    ):
        for value, count in counter.items():
            if count > 1:
                errors.append(f"Duplicate {label}: {value} ({count})")
    for title_key, work_ids in title_index.items():
        if title_key and len(work_ids) > 1:
            warnings.append(
                f"Possible duplicate normalized title: {', '.join(work_ids)}"
            )

    active_keys = set(manifest["active_bib_keys"])
    representative_keys = set(manifest["representative_bib_keys"])
    catalog_active = {
        key for key, work in cited_index.items() if work["manuscript"]["active"]
    }
    catalog_representatives = {
        key
        for key, work in cited_index.items()
        if work["manuscript"]["representative"]
    }
    missing_active = sorted(active_keys - catalog_active)
    unexpected_active = sorted(catalog_active - active_keys)
    missing_representatives = sorted(representative_keys - catalog_representatives)
    # A work is flagged as representative as a whole, so its other cited keys
    # are not themselves taxonomy-figure entries.
    unexpected_representatives = sorted(
        key
        for key in catalog_representatives - representative_keys
        if not (
            set(cited_index[key]["manuscript"].get("cited_bib_keys") or [])
            & representative_keys
        )
    )
    if missing_active:
        errors.append(f"Missing active manuscript keys: {missing_active}")
    if unexpected_active:
        errors.append(f"Unexpected active manuscript keys: {unexpected_active}")
    if missing_representatives:
        errors.append(
            f"Missing taxonomy representatives: {missing_representatives}"
        )
    if unexpected_representatives:
        errors.append(
            f"Unexpected taxonomy representatives: {unexpected_representatives}"
        )
    if len(works) != len(active_keys):
        errors.append(
            f"Catalog work count must equal active manuscript key count: "
            f"{len(works)} != {len(active_keys)}"
        )

    status_counts = Counter(work["classification_status"] for work in works)
    level_counts = Counter(
        work.get("primary_level") or work["catalog_source"]["collection"]
        for work in works
    )
    report = {
        "valid": not errors,
        "work_count": len(works),
        "active_manuscript_coverage": (
            f"{len(active_keys) - len(missing_active)}/{len(active_keys)}"
        ),
        "taxonomy_representative_coverage": (
            f"{len(representative_keys) - len(missing_representatives)}"
            f"/{len(representative_keys)}"
        ),
        "paper_links": sum(bool(work.get("paper_url")) for work in works),
        "code_links": sum(bool(work.get("code_url")) for work in works),
        "project_links": sum(bool(work.get("project_url")) for work in works),
        "counts_by_collection": dict(level_counts),
        "counts_by_status": dict(status_counts),
        "errors": errors,
        "warnings": warnings,
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8") as handle:
            handle.writelines((output, "\n"))
    print(output)
    if errors or (warnings and args.warnings_as_errors):
        sys.exit(1)


if __name__ == "__main__":
    main()
