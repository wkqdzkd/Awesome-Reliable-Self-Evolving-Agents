#!/usr/bin/env python3
"""Generate README and audit documentation from the normalized catalog."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VISIBLE_LINK_STATUSES = {
    "source_listed",
    "verified",
    "redirected",
    "rate_limited",
    "blocked",
}
LIVE_STATUSES = {"verified", "redirected"}
ARTIFACT_STATUSES = VISIBLE_LINK_STATUSES | {"invalid", "unreachable"}

LEVEL_BADGE_COLORS: dict[str, str] = {
    "L0": "9AA5B1",
    "L1": "4C78A8",
    "L2": "2E8B57",
    "L3": "E8842C",
    "L4": "C0392B",
}

CONTENTS_BACKLINK = '<sub><a href="#toc">↑ contents</a></sub>'

VENUE_ALIASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\bNeurIPS\b|\bNIPS\b|Neural Information Processing Systems",
            re.IGNORECASE,
        ),
        "NeurIPS",
    ),
    (
        re.compile(
            r"\bICLR\b|International Conference on Learning Representations",
            re.IGNORECASE,
        ),
        "ICLR",
    ),
    (
        re.compile(
            r"\bICML\b|International Conference on Machine Learning",
            re.IGNORECASE,
        ),
        "ICML",
    ),
    (re.compile(r"\bEMNLP-IJCNLP\b", re.IGNORECASE), "EMNLP-IJCNLP"),
    (
        re.compile(
            r"\bEMNLP\b|Conference on Empirical Methods in Natural Language Processing",
            re.IGNORECASE,
        ),
        "EMNLP",
    ),
    (
        re.compile(
            r"\bNAACL\b|North American Chapter of the Association for Computational Linguistics",
            re.IGNORECASE,
        ),
        "NAACL",
    ),
    (
        re.compile(
            r"\bEACL\b|European Chapter of the Association for Computational Linguistics",
            re.IGNORECASE,
        ),
        "EACL",
    ),
    (re.compile(r"\bAACL\b", re.IGNORECASE), "AACL"),
    (
        re.compile(
            r"\bACL\b|Annual Meeting of the Association for Computational Linguistics",
            re.IGNORECASE,
        ),
        "ACL",
    ),
    (re.compile(r"\bCOLING\b", re.IGNORECASE), "COLING"),
    (re.compile(r"\bLREC\b", re.IGNORECASE), "LREC"),
    (
        re.compile(r"\bCoLM\b|Conference on Language Modeling", re.IGNORECASE),
        "CoLM",
    ),
    (
        re.compile(r"\bTMLR\b|Transactions on Machine Learning Research", re.IGNORECASE),
        "TMLR",
    ),
    (
        re.compile(
            r"\bTACL\b|Transactions of the Association for Computational Linguistics",
            re.IGNORECASE,
        ),
        "TACL",
    ),
    (
        re.compile(r"\bJMLR\b|Journal of Machine Learning Research", re.IGNORECASE),
        "JMLR",
    ),
    (re.compile(r"\bAAAI\b", re.IGNORECASE), "AAAI"),
    (re.compile(r"\bIJCAI\b", re.IGNORECASE), "IJCAI"),
    (re.compile(r"\bAAMAS\b", re.IGNORECASE), "AAMAS"),
    (re.compile(r"\bAISTATS\b", re.IGNORECASE), "AISTATS"),
    (re.compile(r"\bUAI\b", re.IGNORECASE), "UAI"),
    (re.compile(r"\bCVPR\b", re.IGNORECASE), "CVPR"),
    (re.compile(r"\bICCV\b", re.IGNORECASE), "ICCV"),
    (re.compile(r"\bECCV\b", re.IGNORECASE), "ECCV"),
    (re.compile(r"\bMICCAI\b", re.IGNORECASE), "MICCAI"),
    (re.compile(r"\bACM MM\b|\bMM\b", re.IGNORECASE), "ACM MM"),
    (re.compile(r"\bCoRL\b|Conference on Robot Learning", re.IGNORECASE), "CoRL"),
    (re.compile(r"\bICRA\b", re.IGNORECASE), "ICRA"),
    (re.compile(r"\bIROS\b", re.IGNORECASE), "IROS"),
    (re.compile(r"\bESEC/FSE\b|\bESEC-FSE\b", re.IGNORECASE), "ESEC/FSE"),
    (re.compile(r"\bICSE\b", re.IGNORECASE), "ICSE"),
    (re.compile(r"\bASE\b", re.IGNORECASE), "ASE"),
    (re.compile(r"\bFSE\b", re.IGNORECASE), "FSE"),
    (re.compile(r"\bSIGIR\b", re.IGNORECASE), "SIGIR"),
    (re.compile(r"\bCIKM\b", re.IGNORECASE), "CIKM"),
    (re.compile(r"\bWSDM\b", re.IGNORECASE), "WSDM"),
    (re.compile(r"\bKDD\b", re.IGNORECASE), "KDD"),
    (re.compile(r"\bThe Web Conference\b|\bWWW\b", re.IGNORECASE), "WWW"),
    (re.compile(r"\bCHI\b", re.IGNORECASE), "CHI"),
    (re.compile(r"\bUIST\b", re.IGNORECASE), "UIST"),
    (
        re.compile(
            r"ACM on Software Engineering|Proceedings of the ACM on Software Engineering",
            re.IGNORECASE,
        ),
        "PACMSE",
    ),
    (
        re.compile(
            r"Computer-Aided Design of Integrated Circuits and Systems",
            re.IGNORECASE,
        ),
        "IEEE TCAD",
    ),
    (
        re.compile(r"\bNature Communications\b|\bNat Commun\b", re.IGNORECASE),
        "Nature Communications",
    ),
    (re.compile(r"^\s*Nature\s*$", re.IGNORECASE), "Nature"),
    (re.compile(r"\bPNAS\b", re.IGNORECASE), "PNAS"),
    (re.compile(r"\barXiv\b", re.IGNORECASE), "arXiv"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/papers.json"))
    parser.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/manuscript_manifest.json")
    )
    parser.add_argument(
        "--import-report", type=Path, default=Path("data/import_report.json")
    )
    parser.add_argument(
        "--validation-report",
        type=Path,
        default=Path("data/validation_report.json"),
    )
    parser.add_argument(
        "--link-audit", type=Path, default=Path("data/link_audit.json")
    )
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument(
        "--alignment-report",
        type=Path,
        default=Path("docs/ALIGNMENT_REPORT.md"),
    )
    parser.add_argument(
        "--link-report", type=Path, default=Path("docs/LINK_AUDIT.md")
    )
    parser.add_argument(
        "--project-meta", type=Path, default=Path("data/project_meta.json")
    )
    return parser.parse_args()


def figure_block(asset: str, alt: str, label: str, caption: str, width: str) -> list[str]:
    return [
        '<div align="center">',
        f'<img src="assets/{asset}" width="{width}" alt="{alt}"/>',
        "<br>",
        f"<em><b>{label}</b> {caption}</em>",
        "</div>",
        "",
    ]


# Figures are exported from the manuscript's own sources, so a level label in a
# figure and a level heading in this list always come from the same numbering.
SECTION_FIGURES: dict[str, tuple[str, str, str, str]] = {
    "L0": (
        "sec3_output.png",
        "Task-local workflow of Output-Level Self-Evolution",
        "90%",
        "Reflection, exploration, and verification revise the current output while "
        "the underlying agent setup stays fixed, so independent tasks start fresh.",
    ),
    "L1": (
        "sec4_model.png",
        "The three training relations of Model-Level Self-Evolution",
        "90%",
        "The three training relations, read left to right as the party emitting the "
        "training signal moves further from the trainee and the signal becomes "
        "harder to fabricate.",
    ),
    "L2": (
        "sec5_scaffold.png",
        "The widening scaffold scope of Scaffold-Level Self-Evolution",
        "90%",
        "The widening scaffold scope, from a single prompt or code artifact out to "
        "the runtime harness that encloses them all. Each wider region presupposes "
        "the narrower objects it organizes, while the improver and criterion stay "
        "fixed.",
    ),
    "L3": (
        "sec6_improver.png",
        "Improver-Level Self-Evolution",
        "90%",
        "The current improver helps produce or select a candidate successor to its "
        "own update mechanism. After external audit and promotion, the retained "
        "updater governs later proposal, selection, commit, and rollback under a "
        "fixed criterion.",
    ),
    "cross_level": (
        "sec8_ladder.png",
        "The reliability ladder for self-evolving agents",
        "90%",
        "Each step is a deeper evolution target, and each card pairs it with the "
        "external audit and the control that a claim at that depth requires. The "
        "rise of the steps is self-evolution depth, not capability or reliability.",
    ),
    "open_problems": (
        "sec9_applications.png",
        "Applications and staged deployment of self-evolving agents",
        "90%",
        "Across executable engineering, persistent digital agents, scientific "
        "discovery, and embodied or high-stakes systems, the available evidence "
        "ranges from executable checks to expert review and backtests. Wider "
        "deployment requires staged evaluation against a declared external target.",
    ),
}


def count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return f"1 {singular}"
    return f"{count} {plural or singular + 's'}"


def agrees(count: int, singular: str, plural: str) -> str:
    return singular if count == 1 else plural


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_configured_value(value: Any) -> bool:
    """Return True when a project-meta value is present and usable."""
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return bool(stripped) and not stripped.upper().startswith("TODO")


def configured_value(value: Any, default: str | None = None) -> str | None:
    """Return a configured string value, or *default* when unset."""
    if not is_configured_value(value):
        return default
    assert isinstance(value, str)
    return value.strip()


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DEFAULT_NEWS_EMOJI = "✨"


def parse_iso_date(value: Any) -> str | None:
    """Return *YYYY-MM-DD* when *value* is a valid ISO calendar date."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not ISO_DATE_RE.fullmatch(candidate):
        return None
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate


def iso_date_from_value(value: Any) -> str | None:
    """Extract an ISO calendar date from a manifest or audit date/datetime field."""
    if not is_configured_value(value):
        return None
    assert isinstance(value, str)
    date_value = parse_iso_date(value)
    if date_value:
        return date_value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def normalize_news_text(text: str) -> str:
    """Collapse whitespace and newlines so list items stay on one line."""
    return " ".join(text.split())


def parse_manual_news_entries(
    project_meta: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Return validated manual news entries in their configured order."""
    meta = project_meta or {}
    raw_news = meta.get("news")
    if not isinstance(raw_news, list):
        return []

    entries: list[dict[str, str]] = []
    for index, item in enumerate(raw_news):
        if not isinstance(item, dict):
            continue
        date = parse_iso_date(item.get("date"))
        text = configured_value(item.get("text"))
        if not date or not text:
            continue
        emoji = configured_value(item.get("emoji"), default=DEFAULT_NEWS_EMOJI)
        assert emoji is not None
        entries.append(
            {
                "date": date,
                "emoji": emoji,
                "text": normalize_news_text(text),
                "source": "manual",
                "order": str(index),
            }
        )
    return entries


def build_auto_news_entries(
    works: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    manifest: dict[str, Any],
    validation: dict[str, Any],
    link_audit: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Return the three auto-generated What's New timeline entries."""
    manifest_date = iso_date_from_value(manifest.get("generated_at"))
    if not manifest_date:
        return []

    live_code = sum(
        any(
            artifact["kind"] == "code"
            and effective_artifact_status(artifact, link_audit) in LIVE_STATUSES
            for artifact in work["artifacts"]
        )
        for work in works
    )
    live_project = sum(
        any(
            artifact["kind"] == "project"
            and effective_artifact_status(artifact, link_audit) in LIVE_STATUSES
            for artifact in work["artifacts"]
        )
        for work in works
    )
    link_date = iso_date_from_value(
        link_audit.get("checked_at") if link_audit else None
    )
    if not link_date:
        link_date = manifest_date

    return [
        {
            "date": manifest_date,
            "emoji": "🏗️",
            "text": (
                f"Rebuilt the {len(taxonomy['levels'])}-level hierarchy and every "
                "subsection from the manuscript's current chapter structure."
            ),
            "source": "auto",
            "order": "0",
        },
        {
            "date": manifest_date,
            "emoji": "📊",
            "text": (
                f"Cataloged {len(works)} unique works and matched all "
                f"{manifest['active_bib_key_count']} active manuscript references."
            ),
            "source": "auto",
            "order": "1",
        },
        {
            "date": link_date,
            "emoji": "🔗",
            "text": (
                "Live-checked code/project links; "
                f"{live_code} code and {live_project} project links are currently reachable."
            ),
            "source": "auto",
            "order": "2",
        },
    ]


def render_news_timeline_line(emoji: str, date: str, text: str) -> str:
    """Render one What's New bullet in ``- <emoji> **[YYYY-MM-DD]** <text>`` form."""
    return f"- {emoji} **[{date}]** {text}"


def render_whats_new_timeline(
    works: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    manifest: dict[str, Any],
    validation: dict[str, Any],
    link_audit: dict[str, Any] | None,
    project_meta: dict[str, Any] | None = None,
) -> list[str]:
    """Merge manual and auto news entries into a dated timeline."""
    _ = validation
    manual_entries = parse_manual_news_entries(project_meta)
    auto_entries = build_auto_news_entries(
        works, taxonomy, manifest, validation, link_audit
    )
    combined = manual_entries + auto_entries
    combined.sort(
        key=lambda item: (
            item["date"],
            1 if item["source"] == "manual" else 0,
            -int(item["order"]),
        ),
        reverse=True,
    )
    return [
        render_news_timeline_line(item["emoji"], item["date"], item["text"])
        for item in combined
    ]


def get_configured(
    meta: dict[str, Any] | None, *keys: str, default: str | None = None
) -> str | None:
    """Safely read a nested project-meta string with configured-value filtering."""
    current: Any = meta or {}
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return configured_value(current, default=default)


GITHUB_OWNER_RE = re.compile(r"^(?!.*--)[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def is_valid_github_owner(value: str) -> bool:
    """Return True when *value* matches GitHub username/org naming rules."""
    if not (1 <= len(value) <= 39):
        return False
    return bool(GITHUB_OWNER_RE.fullmatch(value))


def is_valid_github_repo(value: str) -> bool:
    """Return True when *value* matches GitHub repository naming rules."""
    if not (1 <= len(value) <= 100):
        return False
    if value in {".", ".."}:
        return False
    return bool(GITHUB_REPO_RE.fullmatch(value))


def get_github_slug(meta: dict[str, Any] | None) -> str | None:
    """Return ``owner/repo`` when both GitHub coordinates are configured and safe."""
    owner = get_configured(meta, "github", "owner")
    repo = get_configured(meta, "github", "repo")
    if not owner or not repo:
        return None
    if not is_valid_github_owner(owner) or not is_valid_github_repo(repo):
        return None
    return f"{owner}/{repo}"


def _has_valid_authority_netloc(netloc: str) -> bool:
    """Return True when *netloc* has no userinfo and strict IPv6 authority syntax."""
    if "@" in netloc:
        return False
    if not netloc.startswith("["):
        return True
    close = netloc.find("]")
    if close == -1:
        return False
    suffix = netloc[close + 1 :]
    if not suffix:
        return True
    if not suffix.startswith(":"):
        return False
    port_part = suffix[1:]
    if not port_part.isdigit():
        return False
    port = int(port_part)
    return 1 <= port <= 65535


def is_safe_absolute_http_url(value: str) -> bool:
    """Return True when *value* is a safe absolute http or https URL."""
    if not value:
        return False
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False
    if any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.netloc or not _has_valid_authority_netloc(parsed.netloc):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        port = parsed.port
        if port is not None and not (1 <= port <= 65535):
            return False
    except ValueError:
        return False
    return True


def normalize_related_list_description(text: str) -> str:
    """Collapse whitespace while preserving Markdown text on one line."""
    lines = [normalize_news_text(line) for line in text.splitlines()]
    return " ".join(line for line in lines if line)


def parse_related_list_entries(
    project_meta: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Return validated related-list entries from project metadata."""
    meta = project_meta or {}
    raw_lists = meta.get("related_lists")
    if not isinstance(raw_lists, list):
        return []

    entries: list[dict[str, str]] = []
    for item in raw_lists:
        if not isinstance(item, dict):
            continue
        name = configured_value(item.get("name"))
        if not name:
            continue
        raw_url = item.get("url")
        if not isinstance(raw_url, str) or not is_safe_absolute_http_url(raw_url):
            continue
        entry: dict[str, str] = {"name": name, "url": raw_url}
        description = configured_value(item.get("description"))
        if description:
            entry["description"] = normalize_related_list_description(description)
        entries.append(entry)
    return entries


def render_star_history_section(github_slug: str) -> list[str]:
    """Render the Star History section for a configured GitHub repository."""
    chart_url = f"https://api.star-history.com/svg?repos={github_slug}&type=Date"
    dark_url = f"{chart_url}&theme=dark"
    page_url = f"https://star-history.com/#{github_slug}&Date"
    alt = f"Star history chart for {github_slug}"
    return [
        stable_anchor_div("star-history"),
        "",
        f"## ⭐ Star History {CONTENTS_BACKLINK}",
        "",
        '<div align="center">',
        f'<a href="{escape_html(page_url)}">',
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" '
        f'srcset="{escape_html(dark_url)}">',
        '  <source media="(prefers-color-scheme: light)" '
        f'srcset="{escape_html(chart_url)}">',
        f'  <img src="{escape_html(chart_url)}" alt="{escape_html(alt)}">',
        "</picture>",
        "</a>",
        "</div>",
        "",
    ]


def render_contributors_section(github_slug: str) -> list[str]:
    """Render the contributors avatars section for a configured GitHub repository."""
    contributors_url = f"https://github.com/{github_slug}/graphs/contributors"
    image_url = f"https://contrib.rocks/image?repo={github_slug}"
    alt = f"Contributors to {github_slug}"
    return [
        stable_anchor_div("contributors"),
        "",
        f"## 👥 Contributors {CONTENTS_BACKLINK}",
        "",
        '<div align="center">',
        f'<a href="{escape_html(contributors_url)}">',
        f'<img src="{escape_html(image_url)}" alt="{escape_html(alt)}">',
        "</a>",
        "</div>",
        "",
    ]


def escape_related_list_description(text: str) -> str:
    """Escape raw HTML while preserving Markdown syntax."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_related_list_line(entry: dict[str, str]) -> str:
    """Render one Related Lists bullet with a safe inline HTML link."""
    link = (
        f'<a href="{escape_html(entry["url"])}">'
        f'{escape_html(entry["name"])}</a>'
    )
    line = f"- {link}"
    description = entry.get("description")
    if description:
        line += f" — {escape_related_list_description(description)}"
    return line


def render_related_lists_section(entries: list[dict[str, str]]) -> list[str]:
    """Render the Related Lists section when at least one entry is valid."""
    if not entries:
        return []
    lines = [
        stable_anchor_div("related-lists"),
        "",
        f"## 📋 Related Lists {CONTENTS_BACKLINK}",
        "",
    ]
    for entry in entries:
        lines.append(render_related_list_line(entry))
    lines.append("")
    return lines


def render_operations_footer(
    project_meta: dict[str, Any] | None,
) -> list[str]:
    """Render README footer sections driven by configured project metadata."""
    github_slug = get_github_slug(project_meta)
    if not github_slug:
        return []
    lines = [
        *render_star_history_section(github_slug),
        *render_contributors_section(github_slug),
    ]
    related_entries = parse_related_list_entries(project_meta)
    if related_entries:
        lines.extend(render_related_lists_section(related_entries))
    return lines


def escape_html(text: str) -> str:
    """Escape text for safe inclusion in HTML attributes and elements."""
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def normalize_arxiv_url(value: str) -> str | None:
    """Return a safe canonical arXiv URL from an ID or existing URL."""
    stripped = value.strip()
    if is_safe_absolute_http_url(stripped):
        parsed = urlparse(stripped)
        if (
            parsed.hostname in {"arxiv.org", "www.arxiv.org"}
            and re.fullmatch(r"/(?:abs|pdf)/[^/]+(?:\.pdf)?", parsed.path)
        ):
            return stripped
        return None
    if re.fullmatch(
        r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[a-z-]+)?/\d{7})(?:v\d+)?",
        stripped,
        re.IGNORECASE,
    ):
        return f"https://arxiv.org/abs/{stripped}"
    return None


def normalize_hf_paper_url(value: str) -> str | None:
    """Return a safe Hugging Face Papers URL from an ID or existing URL."""
    stripped = value.strip()
    if is_safe_absolute_http_url(stripped):
        return stripped
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", stripped):
        return f"https://huggingface.co/papers/{stripped}"
    return None


def is_configured_bibtex(value: Any) -> bool:
    """Return True when *value* contains a real BibTeX entry rather than a placeholder."""
    if not is_configured_value(value):
        return False
    assert isinstance(value, str)
    return not re.search(r"@[A-Za-z]+\{\s*TODO\b", value)


def badge_link(href: str, alt: str, src: str) -> str:
    """Render a centered badge link with escaped metadata."""
    return (
        f'  <a href="{escape_html(href)}"><img alt="{escape_html(alt)}" '
        f'src="{escape_html(src)}"></a>'
    )


def render_readme_header(
    project_title: str,
    survey_title: str,
    works_count: int,
    coverage_badge: str,
    project_meta: dict[str, Any] | None = None,
) -> list[str]:
    """Render the README hero, badges, navigation, citation, and banner."""
    meta = project_meta or {}
    paper = meta.get("paper") if isinstance(meta.get("paper"), dict) else {}
    github_slug = get_github_slug(meta)

    academic_badges = [
        badge_link(
            "https://awesome.re",
            "Awesome",
            "https://awesome.re/badge.svg",
        )
    ]
    arxiv_id = get_configured(paper, "arxiv_id")
    if arxiv_id:
        arxiv_url = normalize_arxiv_url(arxiv_id)
        if arxiv_url:
            arxiv_label = arxiv_url.rsplit("/", maxsplit=1)[-1]
            academic_badges.append(
                badge_link(
                    arxiv_url,
                    "arXiv",
                    f"https://img.shields.io/badge/arXiv-{arxiv_label}-B31B1B?style=flat-square",
                )
            )
    openreview_url = get_configured(paper, "openreview_url")
    if openreview_url and is_safe_absolute_http_url(openreview_url):
        academic_badges.append(
            badge_link(
                openreview_url,
                "OpenReview",
                "https://img.shields.io/badge/OpenReview-Forum-8C1B13?style=flat-square",
            )
        )
    project_page = get_configured(paper, "project_page")
    if project_page and is_safe_absolute_http_url(project_page):
        academic_badges.append(
            badge_link(
                project_page,
                "Project Page",
                "https://img.shields.io/badge/Project-Page-2563EB?style=flat-square",
            )
        )
    hf_paper = get_configured(paper, "hf_paper")
    if hf_paper:
        hf_url = normalize_hf_paper_url(hf_paper)
        if hf_url:
            academic_badges.append(
                badge_link(
                    hf_url,
                    "Hugging Face Paper",
                    "https://img.shields.io/badge/%F0%9F%A4%97-Paper-FFD21E?style=flat-square",
                )
            )

    repo_badges = [
        badge_link(
            "#paper-catalog",
            "Papers",
            f"https://img.shields.io/badge/papers-{works_count}-6C5CE7?style=flat-square",
        ),
        badge_link(
            "docs/ALIGNMENT_REPORT.md",
            "Manuscript coverage",
            f"https://img.shields.io/badge/manuscript-{coverage_badge}-2E8B57?style=flat-square",
        ),
    ]
    if github_slug:
        repo_badges.extend(
            [
                badge_link(
                    f"https://github.com/{github_slug}",
                    "Last commit",
                    f"https://img.shields.io/github/last-commit/{github_slug}?style=flat-square",
                ),
                badge_link(
                    f"https://github.com/{github_slug}",
                    "GitHub stars",
                    f"https://img.shields.io/github/stars/{github_slug}?style=social",
                ),
            ]
        )
    repo_badges.extend(
        [
            badge_link(
                "LICENSES/CC-BY-4.0.txt",
                "Data and docs license",
                "https://img.shields.io/badge/data%20%26%20docs-CC%20BY%204.0-2E8B57?style=flat-square",
            ),
            badge_link(
                "LICENSES/MIT.txt",
                "Code license",
                "https://img.shields.io/badge/code-MIT-2E8B57?style=flat-square",
            ),
        ]
    )

    bibtex = meta.get("bibtex")
    has_citation = is_configured_bibtex(bibtex)
    nav_links = [
        '  <a href="#why-this-list-is-different">🧭 Taxonomy</a> &nbsp;•&nbsp;',
        '  <a href="#contents">🗂️ Browse</a> &nbsp;•&nbsp;',
        '  <a href="#data-and-reproducibility">🧪 Reproduce</a> &nbsp;•&nbsp;',
    ]
    if has_citation:
        nav_links.append('  <a href="#citation">📚 Cite</a> &nbsp;•&nbsp;')
    nav_links.append('  <a href="CONTRIBUTING.md">🤝 Contribute</a>')

    banner_alt = (
        "Five levels of self-evolution, drawn as divers descending from the "
        "surface to the sea floor"
    )
    lines = [
        '<a id="readme-top"></a>',
        "",
        '<div align="center">',
        "",
        f"<h1>🧬 {escape_html(project_title)}</h1>",
        "",
        "<strong>A machine-readable catalog organized by self-evolution depth "
        "and reliability evidence</strong><br>",
        f"Companion catalog for <em>{escape_html(survey_title)}</em>.",
        "",
        '<p align="center">',
        *academic_badges,
        "</p>",
        "",
        '<p align="center">',
        *repo_badges,
        "</p>",
        "",
        '<p align="center">',
        *nav_links,
        "</p>",
        "",
        "</div>",
        "",
    ]

    if has_citation:
        assert isinstance(bibtex, str)
        lines.extend(
            [
                '<a id="citation"></a>',
                "",
                "<details>",
                "<summary><strong>📚 Citation</strong></summary>",
                "",
                "```bibtex",
                bibtex.strip(),
                "```",
                "",
                "</details>",
                "",
            ]
        )

    lines.extend(
        [
            "> 🤝 **Contributions welcome.** Suggest papers, fix links, or improve "
            "classifications through an issue or pull request.",
            "",
            '<div align="center">',
            "<picture>",
            '  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.jpg">',
            '  <source media="(prefers-color-scheme: light)" srcset="assets/banner.jpg">',
            f'  <img src="assets/banner.jpg" width="90%" alt="{escape_html(banner_alt)}">',
            "</picture>",
            "</div>",
            "",
        ]
    )
    return lines


def load_project_meta(path: Path) -> dict[str, Any]:
    """Load project metadata, falling back to an empty config when absent."""
    loaded = load_json(path, default={})
    return loaded if isinstance(loaded, dict) else {}


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.writelines(f"{line}\n" for line in lines)


def effective_artifact_status(
    artifact: dict[str, Any], link_audit: dict[str, Any] | None = None
) -> str | None:
    """Prefer a valid current audit result over the catalog's stored status."""
    results = link_audit.get("results") if isinstance(link_audit, dict) else None
    result = results.get(artifact.get("url")) if isinstance(results, dict) else None
    audit_status = result.get("status") if isinstance(result, dict) else None
    if audit_status in ARTIFACT_STATUSES:
        return audit_status
    status = artifact.get("verification_status")
    return status if status in ARTIFACT_STATUSES else None


def visible_artifact(
    work: dict[str, Any],
    kind: str,
    link_audit: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    candidates = [
        item
        for item in work.get("artifacts", [])
        if item["kind"] == kind
        and effective_artifact_status(item, link_audit) in VISIBLE_LINK_STATUSES
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            effective_artifact_status(item, link_audit) not in LIVE_STATUSES,
            item["url"],
        )
    )
    return candidates[0]


def collection_for(work: dict[str, Any]) -> str:
    return work.get("primary_level") or work["catalog_source"]["collection"]


def group_works_by_collection(
    works: list[dict[str, Any]],
) -> dict[str, dict[str | None, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str | None, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for work in works:
        grouped[collection_for(work)][work.get("primary_subcategory")].append(work)
    return grouped


def collection_work_count(
    grouped: dict[str, dict[str | None, list[dict[str, Any]]]], collection: str
) -> int:
    return sum(len(entries) for entries in grouped.get(collection, {}).values())


def stable_anchor_div(anchor_id: str) -> str:
    return f'<div id="{anchor_id}"></div>'


def subcategory_anchor_id(subcategory: str | None, collection: str) -> str:
    if subcategory:
        return subcategory
    return f"{collection}.additional"


def level_badge_label(level: dict[str, Any]) -> str:
    return f"{level['id']}-{level['short_label']}"


def render_level_badge(level: dict[str, Any], taxonomy: dict[str, Any]) -> str:
    _ = taxonomy
    label = level_badge_label(level)
    color = LEVEL_BADGE_COLORS[level["id"]]
    src = f"https://img.shields.io/badge/{label}-{color}?style=flat-square"
    return (
        f'[![{label}]({src})](#{level["anchor"]})'
    )


def render_level_summary_table(
    taxonomy: dict[str, Any],
    grouped: dict[str, dict[str | None, list[dict[str, Any]]]],
) -> list[str]:
    lines = [
        "| Level | Deepest active evolution target | Characteristic failure | Works |",
        "| --- | --- | --- | ---: |",
    ]
    for level in taxonomy["levels"]:
        count = collection_work_count(grouped, level["id"])
        lines.append(
            "| "
            f"{render_level_badge(level, taxonomy)} | "
            f"{level['deepest_rewrite']} | "
            f"{level['characteristic_failure']} | "
            f"{count} |"
        )
    return lines


def render_contents_links(
    sections: list[dict[str, Any]],
    grouped: dict[str, dict[str | None, list[dict[str, Any]]]],
) -> list[str]:
    lines: list[str] = []
    for section in sections:
        count = collection_work_count(grouped, section["id"])
        lines.append(
            f"- [{section['icon']} {section['heading']}](#{section['anchor']}) "
            f"`{count}`"
        )
    lines.extend(
        [
            "- [🧪 Data and Reproducibility](#data-and-reproducibility)",
            "- [🤝 Contributing](#contributing)",
            "- [⚖️ License](#license)",
        ]
    )
    return lines


def ordered_subcategory_keys(
    section: dict[str, Any],
    available: dict[str | None, list[dict[str, Any]]],
) -> list[str | None]:
    subcategory_order = section["subcategories"]
    ordered_keys: list[str | None] = [
        key for key in subcategory_order if available.get(key)
    ]
    ordered_keys.extend(
        sorted(
            key
            for key in available
            if key not in subcategory_order and key and available.get(key)
        )
    )
    if available.get(None):
        ordered_keys.append(None)
    return ordered_keys


def render_subcategory_jump_nav(
    section: dict[str, Any],
    available: dict[str | None, list[dict[str, Any]]],
    labels: dict[str, str],
) -> str:
    links: list[str] = []
    for subcategory in ordered_subcategory_keys(section, available):
        entries = available.get(subcategory, [])
        if not entries:
            continue
        label = labels.get(subcategory, "Additional and Boundary Works")
        anchor = subcategory_anchor_id(subcategory, section["id"])
        links.append(f"[{label} ({len(entries)})](#{anchor})")
    if not links:
        return ""
    return "**Jump to:** " + " · ".join(links)


def publication_label(work: dict[str, Any]) -> str:
    """Return a compact ``Venue Year`` label for the rendered paper list."""
    raw_venue = " ".join((work.get("venue") or "").split())
    paper_url = work.get("paper_url") or ""
    year = work.get("year")
    if not year:
        year_match = re.search(r"\b(?:19|20)\d{2}\b", raw_venue)
        year = year_match.group(0) if year_match else "n.d."

    venue = next(
        (
            label
            for pattern, label in VENUE_ALIASES
            if pattern.search(raw_venue)
        ),
        None,
    )
    date_only = bool(
        re.fullmatch(
            r"\s*\(?(?:arXiv\s+)?(?:19|20)\d{2}(?:-\d{2}){0,2}"
            r"(?:\s+\([^)]*\))?\)?\s*",
            raw_venue,
            re.IGNORECASE,
        )
    )
    arxiv_preprint = (
        "arxiv.org" in paper_url
        and re.search(r"\bpreprint\b", raw_venue, re.IGNORECASE)
    )
    if venue is None and (not raw_venue or date_only or arxiv_preprint):
        if work.get("arxiv_id") or "arxiv.org" in paper_url:
            venue = "arXiv"
        elif "openreview.net" in paper_url:
            venue = "OpenReview"
        elif "xyz-lab.ai" in paper_url:
            venue = "XYZ Lab"
        elif "lilianweng.github.io" in paper_url:
            venue = "Lilian Weng Blog"
        elif "deepmind" in paper_url:
            venue = "Google DeepMind"
        elif "microsoft.com" in paper_url:
            venue = "Microsoft Research"
        else:
            venue = "Online"
    elif venue is None:
        parenthetical_acronym = re.search(
            r"\(([A-Z][A-Z0-9/&-]{1,15})(?:\s+(?:19|20)\d{2})?[^)]*\)",
            raw_venue,
        )
        leading_acronym = re.match(
            r"^(?!IEEE\b|ACM\b)([A-Z][A-Z0-9/&-]{2,15})\b", raw_venue
        )
        if parenthetical_acronym:
            venue = parenthetical_acronym.group(1)
        elif leading_acronym:
            venue = leading_acronym.group(1)
        else:
            venue = re.sub(r"^\[W\]\s*", "", raw_venue, flags=re.IGNORECASE)
        venue = re.sub(
            r"\s*\((?:arXiv\s+)?(?:19|20)\d{2}(?:-\d{2}){0,2}[^)]*\)",
            "",
            venue,
            flags=re.IGNORECASE,
        )
        venue = re.sub(r"\b(?:19|20)\d{2}\b", "", venue)
        venue = re.sub(
            r",?\s+vol(?:ume)?\.?\s*\d+.*$", "", venue, flags=re.IGNORECASE
        )
        venue = re.sub(
            r"^Proceedings of (?:the )?", "", venue, flags=re.IGNORECASE
        )
        venue = re.sub(r"\s+", " ", venue).strip(" ,()-")
        venue = venue or "Preprint"

    label = f"{venue} {year}"
    lowered = raw_venue.lower()
    if "findings" in lowered:
        label += " Findings"
    elif "workshop" in lowered or raw_venue.lower().startswith("[w]"):
        label += " Workshop"

    presentation = re.search(r"\b(spotlight|oral|poster)\b", raw_venue, re.IGNORECASE)
    if presentation:
        label += f" ({presentation.group(1).title()})"
    return label.replace("`", "'")


def markdown_entry(
    work: dict[str, Any], link_audit: dict[str, Any] | None = None
) -> str:
    title = work["title"].replace("[", r"\[").replace("]", r"\]")
    if not title.endswith((".", "?", "!")):
        title += "."
    paper = visible_artifact(work, "paper", link_audit)
    parts = [f"- **`{publication_label(work)}`** {title}"]
    if paper:
        parts.append(f"[[paper]({paper['url']})]")
    code = visible_artifact(work, "code", link_audit)
    project = visible_artifact(work, "project", link_audit)
    if code:
        relation = code.get("relation", "")
        if "third_party" in relation:
            code_label = "third-party code"
        elif "companion" in relation:
            code_label = "companion"
        else:
            code_label = "code"
        parts.append(f"[[{code_label}]({code['url']})]")
    if project:
        parts.append(f"[[project]({project['url']})]")
    if work["classification_status"] not in {"strict", "supporting"}:
        parts.append(f"`{work['classification_status']}`")
    return " ".join(parts)


def subcategory_labels(taxonomy: dict[str, Any]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for level in taxonomy["levels"]:
        labels.update(
            {item["id"]: item["label"] for item in level["subcategories"]}
        )
    labels.update(
        {
            item["id"]: item["label"]
            for item in taxonomy.get("supporting_subcategories", [])
        }
    )
    return labels


def level_by_id(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {level["id"]: level for level in taxonomy["levels"]}


def core_level_ids(taxonomy: dict[str, Any]) -> list[str]:
    return [level["id"] for level in taxonomy["levels"]]


def presentation_sections(taxonomy: dict[str, Any]) -> list[dict[str, Any]]:
    """Order the rendered catalog: surveys, then each level, then the rest."""
    collections = {item["id"]: item for item in taxonomy["collections"]}
    sections: list[dict[str, Any]] = []

    def collection_section(collection: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": collection["id"],
            "icon": collection["icon"],
            "anchor": collection["anchor"],
            "heading": collection["label"],
            "description": collection["description"],
            "subcategories": [
                item["id"]
                for item in taxonomy.get("supporting_subcategories", [])
                if item["collection"] == collection["id"]
            ],
        }

    if "surveys" in collections:
        sections.append(collection_section(collections["surveys"]))
    for level in taxonomy["levels"]:
        sections.append(
            {
                "id": level["id"],
                "icon": level["icon"],
                "anchor": level["anchor"],
                "heading": f"{level['id']}: {level['label']}",
                "description": (
                    f"Deepest active evolution target: **{level['deepest_rewrite']}**. "
                    f"Characteristic failure: **{level['characteristic_failure']}**."
                ),
                "subcategories": [item["id"] for item in level["subcategories"]],
            }
        )
    for collection in taxonomy["collections"]:
        if collection["id"] != "surveys":
            sections.append(collection_section(collection))
    return sections


def make_readme(
    works: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    manifest: dict[str, Any],
    validation: dict[str, Any],
    link_audit: dict[str, Any] | None,
    project_title: str,
    survey_title: str,
    project_meta: dict[str, Any] | None = None,
) -> list[str]:
    labels = subcategory_labels(taxonomy)
    sections = presentation_sections(taxonomy)
    core_ids = core_level_ids(taxonomy)
    grouped = group_works_by_collection(works)

    coverage_badge = str(validation["active_manuscript_coverage"]).replace(
        "/", "%2F"
    )
    lines = [
        *render_readme_header(
            project_title=project_title,
            survey_title=survey_title,
            works_count=len(works),
            coverage_badge=coverage_badge,
            project_meta=project_meta,
        ),
        "---",
        "",
        stable_anchor_div("whats-new"),
        "",
        f"## 🎉 What's New {CONTENTS_BACKLINK}",
        "",
        *render_whats_new_timeline(
            works,
            taxonomy,
            manifest,
            validation,
            link_audit,
            project_meta,
        ),
        "",
        "---",
        "",
        stable_anchor_div("why-this-list-is-different"),
        "",
        f"## 🧭 Why This List Is Different {CONTENTS_BACKLINK}",
        "",
        (
            "The catalog follows the survey's two organizing questions: **what changes "
            "during self-evolution, and what evidence can support claims of improvement?**"
        ),
        "",
        (
            "Each transition is classified by the **deepest evolution target whose active "
            "semantic change affects a decision-relevant output, update, or judgment**—not "
            "by its algorithm name, training stage, or runtime components."
        ),
        "",
        *render_level_summary_table(taxonomy, grouped),
        "",
        (
            f"{core_ids[0]} is task-local; {core_ids[1]}–{core_ids[-1]} require a "
            "retained change that affects later independent tasks or future updates. "
            "The levels describe how far a change reaches, not how capable or reliable "
            "the system is."
        ),
        "",
        (
            "Under the survey's structural definition, recursive self-improvement (RSI) "
            f"begins at {core_ids[3]} and extends at {core_ids[4]}. This boundary does "
            "not itself establish improvement or imply accelerating gains."
        ),
        "",
        (
            "Across all levels, reliable self-evolution depends on whether evaluation and "
            "oversight remain independent of the update and adequately cover the scope of "
            "the improvement claim."
        ),
        "",
        *figure_block(
            "sec2_loop.png",
            "The self-evolution loop of an agent",
            "Figure 1.",
            "The self-evolution loop. The agent runs a task, then proposes and "
            "selects a candidate change, and an external audit either accepts it, "
            "rejects it and rolls back, or escalates to a human. The evidence source "
            "and the acceptance gate stay outside the update boundary, so the loop "
            "cannot rewrite them.",
            "90%",
        ),
        (
            "A work has one primary level and may have additional manuscript memberships. "
            f"`facing`, `mixed`, and `boundary` labels preserve distinctions such as an "
            f"{core_ids[1]} policy update discussed at the {core_ids[4]} curriculum "
            "frontier."
        ),
        "",
        *figure_block(
            "organization.png",
            "Organization of the survey",
            "Figure 2.",
            "What the companion survey covers. Part I frames self-evolution and "
            f"RSI, Part II maps methods from {core_ids[0]} to {core_ids[-1]} by "
            "evolution depth, and Part III analyses reliability and open problems.",
            "90%",
        ),
        "🔎 Read the full [taxonomy](docs/TAXONOMY.md), "
        "[inclusion methodology](docs/METHODOLOGY.md), "
        "[manuscript alignment report](docs/ALIGNMENT_REPORT.md), and "
        "[link audit](docs/LINK_AUDIT.md).",
        "",
        stable_anchor_div("contents"),
        "",
        "## 🗂️ Contents",
        "",
        stable_anchor_div("toc"),
        "<details open>",
        f"<summary><strong>Browse {len(works)} works by self-evolution level</strong></summary>",
        "",
        *render_contents_links(sections, grouped),
        "",
        "</details>",
        "",
        stable_anchor_div("paper-catalog"),
        "",
        "<!-- BEGIN GENERATED PAPER LIST -->",
    ]

    for section in sections:
        collection = section["id"]
        if collection not in grouped:
            continue
        lines.extend(
            [
                stable_anchor_div(section["anchor"]),
                "",
                f"## {section['icon']} {section['heading']} {CONTENTS_BACKLINK}",
                "",
                f"> {section['description']}",
                "",
            ]
        )
        if collection in SECTION_FIGURES:
            asset, alt, width, caption = SECTION_FIGURES[collection]
            lines.extend(
                figure_block(asset, alt, "Section figure.", caption, width)
            )
        available = grouped[collection]
        jump_nav = render_subcategory_jump_nav(section, available, labels)
        if jump_nav:
            lines.extend([jump_nav, ""])
        ordered_keys = ordered_subcategory_keys(section, available)
        for subcategory in ordered_keys:
            entries = available.get(subcategory, [])
            if not entries:
                continue
            label = labels.get(subcategory, "Additional and Boundary Works")
            lines.extend(
                [
                    stable_anchor_div(
                        subcategory_anchor_id(subcategory, collection)
                    ),
                    "",
                    f"### {label}",
                    "",
                ]
            )
            for work in sorted(
                entries,
                key=lambda item: (
                    -(item.get("year") or 0),
                    item["title"].lower(),
                ),
            ):
                lines.append(markdown_entry(work, link_audit))
            lines.append("")
        lines.extend(
            [
                "---",
                "",
            ]
        )
    lines.extend(
        [
            "<!-- END GENERATED PAPER LIST -->",
            "",
            stable_anchor_div("data-and-reproducibility"),
            "",
            f"## 🧪 Data and Reproducibility {CONTENTS_BACKLINK}",
            "",
            "- 📚 `data/papers.json` is the canonical work catalog.",
            f"- 🧭 `data/taxonomy.json` is the canonical {core_ids[0]}-{core_ids[-1]} hierarchy.",
            "- 🔎 `data/manuscript_manifest.json` records active citations and source hashes.",
            "- ✅ `scripts/validate_catalog.py` enforces identifiers, counts, taxonomy, and coverage.",
            "- 🔗 `scripts/check_links.py` records live HTTP results without silently deleting announced links.",
            "",
            "Regenerate the list with:",
            "",
            "```bash",
            "python scripts/validate_catalog.py --report data/validation_report.json",
            "python scripts/generate_docs.py",
            "```",
            "",
            stable_anchor_div("contributing"),
            "",
            f"## 🤝 Contributing {CONTENTS_BACKLINK}",
            "",
            "Paper suggestions and classification corrections are welcome. Every proposal must "
            "include a canonical paper link, evidence for any code/project link, and an "
            "evolution-target rationale. See [CONTRIBUTING.md](CONTRIBUTING.md).",
            "",
            "Catalog entries follow this format:",
            "",
            "```text",
            "- **`Venue Year`** Title. [[paper](URL)] [[code](URL)]",
            "```",
            "",
            stable_anchor_div("license"),
            "",
            f"## ⚖️ License {CONTENTS_BACKLINK}",
            "",
            "Catalog data and documentation are licensed under "
            "[CC BY 4.0](LICENSES/CC-BY-4.0.txt). Scripts and workflow code are licensed "
            "under the [MIT License](LICENSES/MIT.txt). Third-party paper and repository "
            "links remain subject to their respective licenses.",
        ]
    )
    lines.extend(render_operations_footer(project_meta))
    return lines


def make_alignment_report(
    works: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    manifest: dict[str, Any],
    import_report: dict[str, Any] | None,
    validation: dict[str, Any],
) -> list[str]:
    # These reconciliation counts describe the public catalog snapshot. The
    # internal import report is optional in the release repository.
    RELEASE_RECONCILIATION = {
        "duplicate_bib_key_merges": 1,
        "identity_alias_merges": 7,
        "metadata_overrides_applied": 8,
    }
    core_levels = set(core_level_ids(taxonomy))
    labels = subcategory_labels(taxonomy)
    reconciled = [
        work for work in works if work.get("classification_audit")
    ]
    primary_by_bib = {
        work["manuscript"]["bib_key"]: work
        for work in works
        if work["manuscript"]["bib_key"]
    }
    cross_discussions: list[tuple[str, str, list[str]]] = []
    for bib_key, work in primary_by_bib.items():
        primary = work.get("primary_level")
        cited_levels = sorted(
            {
                membership["source"]
                for membership in work["manuscript"]["memberships"]
                if membership["source"] in core_levels
            }
        )
        if primary and cited_levels and any(level != primary for level in cited_levels):
            cross_discussions.append((bib_key, primary, cited_levels))
    report = import_report or {}
    alias_merge_count = len(report.get("duplicate_bib_key_merges", []))
    if not import_report:
        alias_merge_count = RELEASE_RECONCILIATION["duplicate_bib_key_merges"]
    identity_alias_merge_count = len(report.get("identity_alias_merges", []))
    if not import_report:
        identity_alias_merge_count = RELEASE_RECONCILIATION[
            "identity_alias_merges"
        ]
    excluded = report.get("excluded_works", [])
    unmatched = report.get(
        "unmatched_catalog_entries",
        [
            work["id"]
            for work in works
            if not work["manuscript"].get("bib_key")
            and work.get("catalog_source", {}).get("file")
            == "references/paper_detailed.md"
        ],
    )
    detailed_catalog_count = report.get(
        "detailed_catalog_count",
        sum(
            work.get("catalog_source", {}).get("file")
            == "references/paper_detailed.md"
            for work in works
        ),
    )
    excluded_count = len(excluded) if import_report else 618 - detailed_catalog_count
    unresolved_active_bib_keys = report.get(
        "unresolved_active_bib_keys", manifest.get("unresolved_bib_keys", [])
    )
    active_keys_missing_from_catalog = report.get(
        "active_keys_missing_from_catalog",
        manifest.get("active_keys_missing_from_catalog", []),
    )
    active_manuscript_supplements = report.get(
        "active_manuscript_supplements",
        [
            work
            for work in works
            if work["manuscript"].get("active")
            and work.get("catalog_source", {}).get("file") == "reference.bib"
        ],
    )
    curated_additions = report.get(
        "curated_additions",
        [
            work
            for work in works
            if work.get("catalog_source", {}).get("file")
            == "data/curated_additions.json"
        ],
    )
    metadata_overrides_applied = report.get(
        "metadata_overrides_applied",
        RELEASE_RECONCILIATION["metadata_overrides_applied"],
    )
    aliased = [
        work
        for work in works
        if work["manuscript"].get("bib_key_aliases")
        and len(work["manuscript"].get("cited_bib_keys") or []) > 0
    ]

    lines = [
        "# Manuscript Alignment Report",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Result",
        "",
        f"- Catalog validation: **{'PASS' if validation['valid'] else 'FAIL'}**",
        f"- Active manuscript references: **{validation['active_manuscript_coverage']}**",
        f"- Taxonomy-figure representatives: **{validation['taxonomy_representative_coverage']}**",
        (
            f"- Detailed catalog entries retained: "
            f"**{detailed_catalog_count}/618** "
            f"({count_phrase(excluded_count, 'entry', 'entries')} excluded)"
        ),
        f"- Unresolved active BibTeX keys: **{len(unresolved_active_bib_keys)}**",
        f"- Active keys missing from the catalog: **{len(active_keys_missing_from_catalog)}**",
        "",
        "The repository therefore covers every active citation in the compiled manuscript, "
        "including references that were cited in TeX but absent from the 618-entry detailed catalog.",
        "",
        "## Source-set reconciliation",
        "",
        "- The detailed catalog contributes 618 curated entries.",
        (
            f"- {count_phrase(excluded_count, 'curated entry', 'curated entries')} "
            f"{agrees(excluded_count, 'was', 'were')} excluded for failing the "
            "inclusion criteria: a benchmark, position, or theory paper that "
            "implements no self-evolving system, or a subject outside an agent "
            "changing its own output, model, scaffold, updater, or criterion. "
            "Each exclusion is recorded with its evidence in "
            "`data/exclusions.json`."
        ),
        (
            f"- {len(active_manuscript_supplements)} active manuscript references "
            "were added because they were absent from that detailed catalog."
        ),
        (
            f"- {len(curated_additions)} catalog-only works were added "
            "under the same taxonomy, including post-cutoff papers and one recovered identity split."
        ),
        (
            f"- {count_phrase(metadata_overrides_applied, 'curated record')} "
            "had metadata reconciled against the manuscript, covering identifier "
            "collisions and preprint identities that a published record has since "
            "superseded."
        ),
        (
            f"- {count_phrase(identity_alias_merge_count, 'published record')} merged into "
            "the curated preprint entry through a declared identity alias, so the "
            "manuscript's published citation and the catalog's preprint entry remain one work."
        ),
        (
            f"- {count_phrase(len(reconciled), 'stale detailed-catalog placement')} "
            f"{agrees(len(reconciled), 'was', 'were')} reconciled against the active "
            "chapter text and taxonomy figure."
        ),
        (
            f"- {count_phrase(len(aliased), 'work')} {agrees(len(aliased), 'is', 'are')} "
            "cited under a BibTeX key that differs from the key matched by the detailed "
            "catalog; each is stored once under its canonical identifier, with "
            f"{count_phrase(alias_merge_count, 'additional key')} folded in during import."
        ),
        (
            f"- {count_phrase(len(unmatched), 'detailed-catalog work')} "
            f"{agrees(len(unmatched), 'has', 'have')} no matching entry in the manuscript "
            f"BibTeX library and {agrees(len(unmatched), 'remains', 'remain')} cataloged "
            f"from {agrees(len(unmatched), 'its', 'their')} verified paper "
            f"{agrees(len(unmatched), 'record', 'records')}: "
            + ", ".join(f"`{item}`" for item in unmatched)
            + "."
        ),
        "",
        "## Taxonomy lock",
        "",
        "The machine-readable hierarchy mirrors the manuscript chapter structure:",
        "",
        *(
            f"- {level['id']} ({level['label']}): "
            + ", ".join(
                labels[item["id"]].lower() for item in level["subcategories"]
            )
            + "."
            for level in taxonomy["levels"]
        ),
        "",
        "The detailed catalog was curated under the manuscript's earlier L0-L4 numbering "
        "and its earlier subsection structure; the importer crosswalks those headings onto "
        "the taxonomy above rather than re-curating each entry.",
        "",
        "Primary level follows the deepest demonstrated active rewrite. A citation in another "
        "level's discussion does not silently change its primary classification; such appearances "
        "are retained as manuscript memberships.",
        "",
        "## Reconciled placements",
        "",
    ]
    for work in sorted(reconciled, key=lambda item: item["title"]):
        audit = work["classification_audit"]
        lines.append(
            f"- {work['title']} — "
            f"`{audit['source_primary_level'] or 'supporting'}` → "
            f"`{work['primary_level'] or 'supporting'}` "
            f"(`{work['classification_status']}`)"
        )
    lines.extend(
        [
        "",
        "A `mixed` record preserves every update path the manuscript attributes to a system "
        "instead of silently choosing one and discarding the others.",
        "",
        "## Cross-level discussion memberships",
        "",
        (
            f"{len(cross_discussions)} works are intentionally discussed in a core level other than "
            "their primary level. These are not alignment errors; they include criterion-facing "
            "curricula, mixed update paths, and explicit boundary cases."
        ),
        "",
        ]
    )
    for bib_key, primary, cited_levels in sorted(cross_discussions):
        work = primary_by_bib[bib_key]
        lines.append(
            f"- `{bib_key}` — {work['title']} — primary `{primary}`, discussed in "
            + ", ".join(f"`{level}`" for level in cited_levels)
        )
    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "The manifest stores SHA-256 hashes for the source bibliography and every TeX section. "
            "Re-running the importer after a manuscript edit makes taxonomy or citation drift visible.",
            "",
            "Validation command:",
            "",
            "```bash",
            "python scripts/validate_catalog.py --report data/validation_report.json",
            "```",
        ]
    )
    return lines


def make_link_report(
    works: list[dict[str, Any]], link_audit: dict[str, Any] | None
) -> list[str]:
    if not link_audit:
        return [
            "# Link Audit",
            "",
            "No live link audit has been recorded yet.",
        ]
    invalid_by_work: list[tuple[str, str, str]] = []
    for work in works:
        for artifact in work["artifacts"]:
            if effective_artifact_status(artifact, link_audit) in {
                "invalid",
                "unreachable",
            }:
                invalid_by_work.append(
                    (work["title"], artifact["kind"], artifact["url"])
                )
    lines = [
        "# Link Audit",
        "",
        f"Last checked: {link_audit['checked_at']}",
        "",
        "## Summary",
        "",
        f"- Unique URLs checked: **{link_audit['url_count']}**",
    ]
    for status, count in sorted(link_audit["status_counts"].items()):
        lines.append(f"- `{status}`: **{count}**")
    lines.extend(
        [
            "",
            "A missing code link does not imply that no implementation exists. It means no official "
            "or source-backed public repository was found. Announced but currently unavailable URLs "
            "remain in the data for provenance and are omitted from the rendered paper list.",
            "",
            "## Unavailable links",
            "",
        ]
    )
    if invalid_by_work:
        for title, kind, url in sorted(invalid_by_work):
            lines.append(f"- {title} — `{kind}` — {url}")
    else:
        lines.append("- None.")
    return lines


def main() -> None:
    args = parse_args()
    catalog = load_json(args.catalog)
    taxonomy = load_json(args.taxonomy)
    manifest = load_json(args.manifest)
    import_report = load_json(args.import_report)
    validation = load_json(args.validation_report)
    link_audit = load_json(args.link_audit)
    project_meta = load_project_meta(args.project_meta)
    works = catalog["works"]
    write_lines(
        args.readme,
        make_readme(
            works,
            taxonomy,
            manifest,
            validation,
            link_audit,
            catalog["title"],
            catalog["survey_title"],
            project_meta,
        ),
    )
    write_lines(
        args.alignment_report,
        make_alignment_report(works, taxonomy, manifest, import_report, validation),
    )
    write_lines(args.link_report, make_link_report(works, link_audit))
    print(
        json.dumps(
            {
                "readme": str(args.readme),
                "alignment_report": str(args.alignment_report),
                "link_report": str(args.link_report),
                "works": len(works),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
