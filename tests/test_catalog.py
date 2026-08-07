from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATE_SPEC = importlib.util.spec_from_file_location(
    "generate_docs", ROOT / "scripts" / "generate_docs.py"
)
assert GENERATE_SPEC and GENERATE_SPEC.loader
GENERATE_DOCS = importlib.util.module_from_spec(GENERATE_SPEC)
GENERATE_SPEC.loader.exec_module(GENERATE_DOCS)


class ProjectMetaTests(unittest.TestCase):
    def test_configured_value_keeps_valid_string(self) -> None:
        self.assertEqual(
            GENERATE_DOCS.configured_value("alanqwang"), "alanqwang"
        )

    def test_configured_value_filters_blank_and_todo(self) -> None:
        self.assertIsNone(GENERATE_DOCS.configured_value(""))
        self.assertIsNone(GENERATE_DOCS.configured_value("   "))
        self.assertIsNone(GENERATE_DOCS.configured_value("TODO"))
        self.assertIsNone(GENERATE_DOCS.configured_value("TODO: fill later"))
        self.assertIsNone(GENERATE_DOCS.configured_value("  TODO owner"))

    def test_get_configured_reads_nested_fields(self) -> None:
        meta = {
            "github": {"owner": "alanqwang", "repo": "TODO"},
            "paper": {"arxiv_id": "  "},
        }
        self.assertEqual(
            GENERATE_DOCS.get_configured(meta, "github", "owner"),
            "alanqwang",
        )
        self.assertIsNone(GENERATE_DOCS.get_configured(meta, "github", "repo"))
        self.assertIsNone(GENERATE_DOCS.get_configured(meta, "paper", "arxiv_id"))
        self.assertIsNone(
            GENERATE_DOCS.get_configured(meta, "paper", "missing_field")
        )
        self.assertIsNone(GENERATE_DOCS.get_configured(meta, "missing", "field"))

    def test_load_project_meta_missing_file_returns_empty_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            meta = GENERATE_DOCS.load_project_meta(path)
        self.assertEqual(meta, {})

    def test_default_project_meta_has_contribution_text_and_contacts(self) -> None:
        meta = GENERATE_DOCS.load_project_meta(ROOT / "data" / "project_meta.json")
        self.assertEqual(
            meta["text"],
            "Contributions are welcome: add a missing work in a PR using "
            "``- **`Venue Year`** Title. [[paper](URL)] [[code](URL)]``.",
        )
        self.assertEqual(
            meta["contact_email"],
            "wkqscut@gmail.com, wenjinhou@zju.edu.cn, "
            "yanyuchen@zju.edu.cn, hehefan@zju.edu.cn",
        )


class ReadmeHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = json.loads(
            (ROOT / "data" / "taxonomy.json").read_text(encoding="utf-8")
        )
        cls.validation = json.loads(
            (ROOT / "data" / "validation_report.json").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads(
            (ROOT / "data" / "manuscript_manifest.json").read_text(encoding="utf-8")
        )
        cls.catalog = json.loads(
            (ROOT / "data" / "papers.json").read_text(encoding="utf-8")
        )

    def _header_text(
        self, project_meta: dict[str, object] | None = None
    ) -> str:
        lines = GENERATE_DOCS.render_readme_header(
            project_title=self.catalog["title"],
            survey_title=self.catalog["survey_title"],
            works_count=len(self.catalog["works"]),
            coverage_badge=str(
                self.validation["active_manuscript_coverage"]
            ).replace("/", "%2F"),
            project_meta=project_meta,
        )
        return "\n".join(lines)

    def _readme_text(
        self, project_meta: dict[str, object] | None = None
    ) -> str:
        lines = GENERATE_DOCS.make_readme(
            self.catalog["works"],
            self.taxonomy,
            self.manifest,
            self.validation,
            {"checked_at": "2026-08-06"},
            self.catalog["title"],
            self.catalog["survey_title"],
            project_meta,
        )
        return "\n".join(lines)

    def test_default_meta_renders_repository_badges_without_paper_placeholders(
        self,
    ) -> None:
        header = self._header_text(
            project_meta=json.loads(
                (ROOT / "data" / "project_meta.json").read_text(encoding="utf-8")
            )
        )
        self.assertIn("awesome.re/badge.svg", header)
        self.assertIn(f"papers-{len(self.catalog['works'])}", header)
        coverage = str(
            self.validation["active_manuscript_coverage"]
        ).replace("/", "%2F")
        self.assertIn(f"manuscript-{coverage}", header)
        self.assertIn("license-MIT", header)
        self.assertIn('href="LICENSE"', header)
        self.assertNotIn("CC%20BY", header)
        self.assertNotIn("LICENSES/", header)
        self.assertIn("<picture>", header)
        self.assertIn('prefers-color-scheme: dark', header)
        self.assertIn('prefers-color-scheme: light', header)
        self.assertIn('src="assets/banner.jpg" width="90%"', header)
        self.assertNotIn("Star this list if it helps you place a paper", header)
        self.assertNotIn("badge/version-", header)
        self.assertNotIn("catalog-machine--readable", header)
        self.assertIn(
            "github/last-commit/wkqdzkd/Awesome-Reliable-Self-Evolving-Agents",
            header,
        )
        self.assertIn(
            "github/stars/wkqdzkd/Awesome-Reliable-Self-Evolving-Agents",
            header,
        )
        self.assertNotIn("arxiv.org", header)
        self.assertNotIn("huggingface.co", header)
        self.assertNotIn('href="#citation"', header)
        self.assertNotIn('<a id="citation"></a>', header)
        self.assertNotIn("📚 Citation", header)
        self.assertIn(
            "Contributions are welcome: add a missing work in a PR using "
            "``- **`Venue Year`** Title. [[paper](URL)] [[code](URL)]``.",
            header,
        )
        self.assertIn(
            "wkqscut@gmail.com, wenjinhou@zju.edu.cn, "
            "yanyuchen@zju.edu.cn, hehefan@zju.edu.cn",
            header,
        )

    def test_full_meta_renders_conditional_badges_cite_and_citation(self) -> None:
        meta = {
            "github": {"owner": "alanqwang", "repo": "RSI_survey"},
            "paper": {
                "arxiv_id": "2607.12345",
                "openreview_url": "https://openreview.net/forum?id=abc123",
                "project_page": "https://example.org/project",
                "hf_paper": "2607.12345",
            },
            "bibtex": (
                "@article{rsi2026,\n"
                "  title={Diving into Reliable Self-Evolving Agents: A Survey},\n"
                "  year={2026}\n"
                "}"
            ),
        }
        header = self._header_text(project_meta=meta)
        self.assertIn("arxiv.org/abs/2607.12345", header)
        self.assertIn("openreview.net/forum?id=abc123", header)
        self.assertIn("https://example.org/project", header)
        self.assertIn("huggingface.co/papers/2607.12345", header)
        self.assertIn("github/last-commit/alanqwang/RSI_survey", header)
        self.assertIn("github/stars/alanqwang/RSI_survey?style=social", header)
        self.assertIn('href="#citation"', header)
        self.assertIn('<a id="citation"></a>', header)
        self.assertIn("<summary><strong>📚 Citation</strong></summary>", header)
        self.assertIn("```bibtex", header)
        self.assertIn("@article{rsi2026,", header)

    def test_make_readme_preserves_core_navigation_without_cite_when_unconfigured(
        self,
    ) -> None:
        readme = self._readme_text(
            project_meta=json.loads(
                (ROOT / "data" / "project_meta.json").read_text(encoding="utf-8")
            )
        )
        self.assertIn("#why-this-list-is-different", readme)
        self.assertIn("#contents", readme)
        self.assertIn("#data-and-reproducibility", readme)
        self.assertIn("CONTRIBUTING.md", readme)
        self.assertNotIn('href="#citation"', readme)

    def test_make_readme_omits_whats_new_section(self) -> None:
        readme = self._readme_text(
            project_meta=json.loads(
                (ROOT / "data" / "project_meta.json").read_text(encoding="utf-8")
            )
        )
        self.assertNotIn('<div id="whats-new"></div>', readme)
        self.assertNotIn("## 🎉 What's New", readme)

    def test_make_readme_uses_repository_wide_mit_license(self) -> None:
        readme = self._readme_text(
            project_meta=json.loads(
                (ROOT / "data" / "project_meta.json").read_text(encoding="utf-8")
            )
        )
        license_section = readme.split('<div id="license"></div>', maxsplit=1)[1]
        self.assertIn("[MIT License](LICENSE)", license_section)
        self.assertIn("Original text, catalog data, code, and images", license_section)
        self.assertIn("third-party metadata", license_section)
        self.assertNotIn("CC BY", license_section)
        self.assertNotIn("LICENSES/", license_section)

    def test_url_helpers_normalize_ids_and_escape_html(self) -> None:
        self.assertEqual(
            GENERATE_DOCS.normalize_arxiv_url("2607.12345"),
            "https://arxiv.org/abs/2607.12345",
        )
        self.assertEqual(
            GENERATE_DOCS.normalize_arxiv_url(
                "https://arxiv.org/abs/2607.12345"
            ),
            "https://arxiv.org/abs/2607.12345",
        )
        self.assertEqual(
            GENERATE_DOCS.normalize_hf_paper_url("2607.12345"),
            "https://huggingface.co/papers/2607.12345",
        )
        self.assertEqual(
            GENERATE_DOCS.escape_html('Say "hello" & <goodbye>'),
            "Say &quot;hello&quot; &amp; &lt;goodbye&gt;",
        )
        self.assertFalse(
            GENERATE_DOCS.is_configured_bibtex(
                "@article{TODO,\n  title={Example}\n}"
            )
        )
        self.assertTrue(
            GENERATE_DOCS.is_configured_bibtex(
                "@article{rsi2026,\n  title={Example}\n}"
            )
        )

    def test_header_omits_unsafe_urls_and_invalid_github_coordinates(self) -> None:
        header = self._header_text(
            {
                "github": {"owner": "bad/name", "repo": "RSI_survey"},
                "paper": {
                    "arxiv_id": "javascript:alert(1)",
                    "openreview_url": "javascript:alert(1)",
                    "project_page": "data:text/html,boom",
                    "hf_paper": "https://[",
                },
            }
        )
        self.assertNotIn("github/last-commit", header)
        self.assertNotIn("javascript:", header)
        self.assertNotIn("data:text", header)
        self.assertNotIn("huggingface.co/papers/", header)

    def test_header_accepts_safe_paper_ids_and_urls(self) -> None:
        header = self._header_text(
            {
                "paper": {
                    "arxiv_id": "hep-th/9901001",
                    "openreview_url": "https://openreview.net/forum?id=abc123",
                    "project_page": "https://example.org/project",
                    "hf_paper": "https://huggingface.co/papers/2607.12345",
                }
            }
        )
        self.assertIn("arxiv.org/abs/hep-th/9901001", header)
        self.assertIn("openreview.net/forum?id=abc123", header)
        self.assertIn("https://example.org/project", header)
        self.assertIn("https://huggingface.co/papers/2607.12345", header)


class OperationsFooterTests(unittest.TestCase):
    def test_github_slug_requires_valid_owner_and_repo(self) -> None:
        self.assertEqual(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": "alanqwang", "repo": "RSI_survey"}}
            ),
            "alanqwang/RSI_survey",
        )
        self.assertIsNone(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": "TODO", "repo": "RSI_survey"}}
            )
        )
        self.assertIsNone(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": "alanqwang", "repo": "TODO"}}
            )
        )
        self.assertIsNone(
            GENERATE_DOCS.get_github_slug(
                {
                    "github": {
                        "owner": 'alan" onclick="alert(1)',
                        "repo": "RSI_survey",
                    }
                }
            )
        )

    def test_related_lists_filter_invalid_entries(self) -> None:
        meta = {
            "related_lists": [
                {"name": "Valid List", "url": "https://example.com/list"},
                {
                    "name": "With Description",
                    "url": "https://example.com/described",
                    "description": "Line one.\n\nLine two.",
                },
                {"name": "TODO", "url": "https://example.com/todo-name"},
                {"name": "Missing URL"},
                {"url": "https://example.com/missing-name"},
                {"name": "Relative URL", "url": "/lists/relative"},
                {"name": "TODO URL", "url": "TODO"},
                {"name": "No Host", "url": "https://"},
                {"name": "Whitespace URL", "url": "https://example.com/a b"},
                {"name": "Control Char URL", "url": "https://example.com/\x07"},
                "not-a-dict",
            ]
        }
        entries = GENERATE_DOCS.parse_related_list_entries(meta)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["name"], "Valid List")
        self.assertEqual(entries[0]["url"], "https://example.com/list")
        self.assertNotIn("description", entries[0])
        self.assertEqual(entries[1]["name"], "With Description")
        self.assertEqual(
            entries[1]["description"], "Line one. Line two."
        )

    def test_related_lists_reject_urls_without_hostname(self) -> None:
        rejected_urls = [
            "https://",
            "http://",
            "https:///path",
        ]
        for url in rejected_urls:
            with self.subTest(url=url):
                self.assertFalse(GENERATE_DOCS.is_safe_absolute_http_url(url))

    def test_related_lists_reject_malformed_urls_without_raising(self) -> None:
        malformed_urls = [
            "https://[",
            "https://example.com:notaport",
        ]
        for url in malformed_urls:
            with self.subTest(url=url):
                self.assertFalse(GENERATE_DOCS.is_safe_absolute_http_url(url))

    def test_parse_related_list_entries_filters_malformed_urls_without_raising(
        self,
    ) -> None:
        meta = {
            "related_lists": [
                {"name": "Valid", "url": "https://example.com/ok"},
                {"name": "Broken IPv6", "url": "https://["},
                {"name": "Bad Port", "url": "https://example.com:notaport"},
            ]
        }
        entries = GENERATE_DOCS.parse_related_list_entries(meta)
        self.assertEqual(
            entries,
            [{"name": "Valid", "url": "https://example.com/ok"}],
        )
        rendered = "\n".join(GENERATE_DOCS.render_related_lists_section(entries))
        self.assertIn(
            '- <a href="https://example.com/ok">Valid</a>',
            rendered,
        )

    def test_parse_related_list_entries_rejects_raw_url_whitespace(self) -> None:
        meta = {
            "related_lists": [
                {"name": "Valid", "url": "https://example.com/ok"},
                {"name": "Leading Space", "url": " https://example.com/padded"},
                {"name": "Trailing Tab", "url": "https://example.com/padded\t"},
                {"name": "Both", "url": "\t https://example.com/padded \t"},
            ]
        }
        entries = GENERATE_DOCS.parse_related_list_entries(meta)
        self.assertEqual(
            entries,
            [{"name": "Valid", "url": "https://example.com/ok"}],
        )

    def test_is_safe_absolute_http_url_ipv6_authority_boundaries(self) -> None:
        accepted = [
            "https://example.com/path",
            "https://[::1]",
            "https://[::1]:8443/path",
        ]
        rejected = [
            "https://[::1]x",
            "https://[::1]foo",
            "https://[::1]:notaport",
            "https://user:pass@example.com/path",
        ]
        for url in accepted:
            with self.subTest(url=url, accepted=True):
                self.assertTrue(GENERATE_DOCS.is_safe_absolute_http_url(url))
        for url in rejected:
            with self.subTest(url=url, accepted=False):
                self.assertFalse(GENERATE_DOCS.is_safe_absolute_http_url(url))

    def test_is_safe_absolute_http_url_rejects_zero_port(self) -> None:
        rejected = [
            "https://example.com:0/path",
            "https://127.0.0.1:0/path",
        ]
        accepted = [
            "https://example.com/path",
            "https://example.com:1/path",
            "https://127.0.0.1:65535/path",
        ]
        for url in rejected:
            with self.subTest(url=url, accepted=False):
                self.assertFalse(GENERATE_DOCS.is_safe_absolute_http_url(url))
        for url in accepted:
            with self.subTest(url=url, accepted=True):
                self.assertTrue(GENERATE_DOCS.is_safe_absolute_http_url(url))

    def test_render_related_lists_uses_safe_html_links(self) -> None:
        entries = [
            {
                "name": 'Evil](javascript:alert(1)',
                "url": "https://example.com/list",
                "description": (
                    '<img src=x onerror=alert(1)> **bold** '
                    "[docs](https://example.com/docs)"
                ),
            }
        ]
        rendered = "\n".join(GENERATE_DOCS.render_related_lists_section(entries))
        self.assertIn(
            '- <a href="https://example.com/list">Evil](javascript:alert(1)</a>',
            rendered,
        )
        self.assertNotIn("<img src=x", rendered)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", rendered)
        self.assertIn("**bold**", rendered)
        self.assertIn("[docs](https://example.com/docs)", rendered)
        self.assertNotIn("[Evil](javascript:alert(1)", rendered)

    def test_github_owner_validation_boundaries(self) -> None:
        owner_39 = "a" + ("b" * 38)
        self.assertEqual(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": owner_39, "repo": "RSI_survey"}}
            ),
            f"{owner_39}/RSI_survey",
        )
        self.assertEqual(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": "a-b", "repo": "RSI_survey"}}
            ),
            "a-b/RSI_survey",
        )
        invalid_owners = [
            "a" * 40,
            "alan_qwang",
            "alan.qwang",
            "-alan",
            "alan-",
            "al--an",
        ]
        for owner in invalid_owners:
            with self.subTest(owner=owner):
                self.assertIsNone(
                    GENERATE_DOCS.get_github_slug(
                        {"github": {"owner": owner, "repo": "RSI_survey"}}
                    )
                )

    def test_github_repo_validation_boundaries(self) -> None:
        repo_100 = "r" + ("s" * 99)
        self.assertEqual(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": "alanqwang", "repo": repo_100}}
            ),
            f"alanqwang/{repo_100}",
        )
        self.assertEqual(
            GENERATE_DOCS.get_github_slug(
                {"github": {"owner": "alanqwang", "repo": "RSI_survey"}}
            ),
            "alanqwang/RSI_survey",
        )
        invalid_repos = [".", "..", "r" * 101]
        for repo in invalid_repos:
            with self.subTest(repo=repo):
                self.assertIsNone(
                    GENERATE_DOCS.get_github_slug(
                        {"github": {"owner": "alanqwang", "repo": repo}}
                    )
                )

    def test_invalid_github_coordinates_omit_entire_operations_footer(self) -> None:
        meta = {
            "github": {"owner": "al--an", "repo": "RSI_survey"},
            "related_lists": [
                {"name": "Awesome RSI", "url": "https://example.com/awesome"},
            ],
        }
        self.assertEqual(GENERATE_DOCS.render_operations_footer(meta), [])

    def test_render_star_history_picture_modes(self) -> None:
        lines = GENERATE_DOCS.render_star_history_section("alanqwang/RSI_survey")
        rendered = "\n".join(lines)
        self.assertIn('<div id="star-history"></div>', rendered)
        self.assertIn("## ", rendered)
        self.assertIn('<sub><a href="#toc">↑ contents</a></sub>', rendered)
        self.assertIn('<div align="center">', rendered)
        self.assertIn(
            'href="https://star-history.com/#alanqwang/RSI_survey&amp;Date"',
            rendered,
        )
        self.assertIn("<picture>", rendered)
        self.assertIn(
            'srcset="https://api.star-history.com/svg?repos=alanqwang/RSI_survey'
            '&amp;type=Date&amp;theme=dark"',
            rendered,
        )
        self.assertIn(
            'srcset="https://api.star-history.com/svg?repos=alanqwang/RSI_survey'
            '&amp;type=Date"',
            rendered,
        )
        self.assertIn(
            'src="https://api.star-history.com/svg?repos=alanqwang/RSI_survey'
            '&amp;type=Date"',
            rendered,
        )
        self.assertIn('media="(prefers-color-scheme: dark)"', rendered)
        self.assertIn('media="(prefers-color-scheme: light)"', rendered)
        self.assertIn('alt="Star history chart for alanqwang/RSI_survey"', rendered)

    def test_render_contributors_section(self) -> None:
        lines = GENERATE_DOCS.render_contributors_section("alanqwang/RSI_survey")
        rendered = "\n".join(lines)
        self.assertIn('<div id="contributors"></div>', rendered)
        self.assertIn('<sub><a href="#toc">↑ contents</a></sub>', rendered)
        self.assertIn(
            'href="https://github.com/alanqwang/RSI_survey/graphs/contributors"',
            rendered,
        )
        self.assertIn(
            'src="https://contrib.rocks/image?repo=alanqwang/RSI_survey"',
            rendered,
        )
        self.assertIn('alt="Contributors to alanqwang/RSI_survey"', rendered)
        self.assertIn('<div align="center">', rendered)

    def test_render_related_lists_section(self) -> None:
        entries = [
            {"name": "Awesome RSI", "url": "https://example.com/awesome"},
            {
                "name": "Companion List",
                "url": "https://example.com/companion",
                "description": "A related catalog.",
            },
        ]
        lines = GENERATE_DOCS.render_related_lists_section(entries)
        rendered = "\n".join(lines)
        self.assertIn('<div id="related-lists"></div>', rendered)
        self.assertIn('<sub><a href="#toc">↑ contents</a></sub>', rendered)
        self.assertIn(
            '- <a href="https://example.com/awesome">Awesome RSI</a>',
            rendered,
        )
        self.assertIn(
            '- <a href="https://example.com/companion">Companion List</a> — A related catalog.',
            rendered,
        )

    def test_render_operations_footer_with_full_github_config(self) -> None:
        meta = {
            "github": {"owner": "alanqwang", "repo": "RSI_survey"},
            "related_lists": [
                {"name": "Awesome RSI", "url": "https://example.com/awesome"},
            ],
        }
        rendered = "\n".join(GENERATE_DOCS.render_operations_footer(meta))
        self.assertIn('<div id="star-history"></div>', rendered)
        self.assertIn('<div id="contributors"></div>', rendered)
        self.assertIn('<div id="related-lists"></div>', rendered)
        self.assertIn("star-history.com", rendered)
        self.assertIn("contrib.rocks/image", rendered)
        self.assertIn("Awesome RSI", rendered)

    def test_render_operations_footer_omits_related_lists_when_empty(self) -> None:
        meta = {
            "github": {"owner": "alanqwang", "repo": "RSI_survey"},
            "related_lists": [],
        }
        rendered = "\n".join(GENERATE_DOCS.render_operations_footer(meta))
        self.assertIn('<div id="star-history"></div>', rendered)
        self.assertIn('<div id="contributors"></div>', rendered)
        self.assertNotIn('<div id="related-lists"></div>', rendered)

    def test_render_operations_footer_omits_entire_section_without_github(self) -> None:
        meta = {
            "github": {"owner": "TODO", "repo": "TODO"},
            "related_lists": [
                {"name": "Awesome RSI", "url": "https://example.com/awesome"},
            ],
        }
        self.assertEqual(GENERATE_DOCS.render_operations_footer(meta), [])

    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = json.loads(
            (ROOT / "data" / "taxonomy.json").read_text(encoding="utf-8")
        )
        cls.validation = json.loads(
            (ROOT / "data" / "validation_report.json").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads(
            (ROOT / "data" / "manuscript_manifest.json").read_text(encoding="utf-8")
        )
        cls.catalog = json.loads(
            (ROOT / "data" / "papers.json").read_text(encoding="utf-8")
        )

    def _readme_text(
        self, project_meta: dict[str, object] | None = None
    ) -> str:
        lines = GENERATE_DOCS.make_readme(
            self.catalog["works"],
            self.taxonomy,
            self.manifest,
            self.validation,
            {"checked_at": "2026-08-06"},
            self.catalog["title"],
            self.catalog["survey_title"],
            project_meta,
        )
        return "\n".join(lines)

    def test_default_readme_renders_repository_operations_footer(self) -> None:
        readme = self._readme_text(
            project_meta=json.loads(
                (ROOT / "data" / "project_meta.json").read_text(encoding="utf-8")
            )
        )
        self.assertIn('<div id="star-history"></div>', readme)
        self.assertIn('<div id="contributors"></div>', readme)
        self.assertNotIn('<div id="related-lists"></div>', readme)
        license_section = readme.split('<div id="license"></div>', maxsplit=1)[1]
        self.assertIn("star-history.com", license_section)

    def test_readme_places_operations_footer_after_license(self) -> None:
        meta = {
            "github": {"owner": "alanqwang", "repo": "RSI_survey"},
            "related_lists": [],
        }
        readme = self._readme_text(project_meta=meta)
        license_index = readme.index("## ⚖️ License")
        star_index = readme.index('<div id="star-history"></div>')
        contributors_index = readme.index('<div id="contributors"></div>')
        self.assertGreater(star_index, license_index)
        self.assertGreater(contributors_index, star_index)


class DocumentationTests(unittest.TestCase):
    def test_publication_label_compacts_venue_and_qualifiers(self) -> None:
        self.assertEqual(
            GENERATE_DOCS.publication_label(
                {
                    "venue": (
                        "The Fourteenth International Conference on "
                        "Learning Representations"
                    ),
                    "year": 2026,
                    "paper_url": "https://openreview.net/forum?id=example",
                }
            ),
            "ICLR 2026",
        )
        self.assertEqual(
            GENERATE_DOCS.publication_label(
                {
                    "venue": "[W] ICLR 2026 Workshop (Spotlight)",
                    "year": 2026,
                    "paper_url": "https://openreview.net/forum?id=example",
                }
            ),
            "ICLR 2026 Workshop (Spotlight)",
        )

    def test_markdown_entry_uses_venue_title_and_explicit_links(self) -> None:
        work = {
            "title": (
                "MemAgent: Reshaping Long-Context LLM with Multi-Conv "
                "RL-based Memory Agent"
            ),
            "venue": "ICLR 2026",
            "year": 2026,
            "paper_url": "https://example.com/paper",
            "classification_status": "strict",
            "artifacts": [
                {
                    "kind": "paper",
                    "url": "https://example.com/paper",
                    "verification_status": "verified",
                },
                {
                    "kind": "code",
                    "url": "https://example.com/code",
                    "relation": "official",
                    "verification_status": "verified",
                },
            ],
        }
        self.assertEqual(
            GENERATE_DOCS.markdown_entry(work),
            "- **`ICLR 2026`** MemAgent: Reshaping Long-Context LLM with "
            "Multi-Conv RL-based Memory Agent. "
            "[[paper](https://example.com/paper)] "
            "[[code](https://example.com/code)]",
        )

    def test_link_audit_overrides_stored_artifact_statuses(self) -> None:
        works = [
            {
                "title": "Audit invalid",
                "venue": "ICLR 2026",
                "year": 2026,
                "paper_url": "https://example.com/paper",
                "classification_status": "strict",
                "artifacts": [
                    {
                        "kind": "paper",
                        "url": "https://example.com/paper",
                        "verification_status": "verified",
                    },
                    {
                        "kind": "code",
                        "url": "https://example.com/invalid-code",
                        "verification_status": "verified",
                    },
                ],
            },
            {
                "title": "Audit verified",
                "venue": "ICLR 2026",
                "year": 2026,
                "paper_url": "https://example.com/paper-two",
                "classification_status": "strict",
                "artifacts": [
                    {
                        "kind": "paper",
                        "url": "https://example.com/paper-two",
                        "verification_status": "verified",
                    },
                    {
                        "kind": "project",
                        "url": "https://example.com/verified-project",
                        "verification_status": "invalid",
                    },
                ],
            },
        ]
        audit = {
            "checked_at": "2026-08-06T15:04:05Z",
            "url_count": 4,
            "status_counts": {"invalid": 1, "verified": 3},
            "results": {
                "https://example.com/invalid-code": {"status": "invalid"},
                "https://example.com/verified-project": {"status": "verified"},
            },
        }
        self.assertNotIn(
            "[[code](https://example.com/invalid-code)]",
            GENERATE_DOCS.markdown_entry(works[0], audit),
        )
        self.assertIn(
            "[[project](https://example.com/verified-project)]",
            GENERATE_DOCS.markdown_entry(works[1], audit),
        )
        report = "\n".join(GENERATE_DOCS.make_link_report(works, audit))
        self.assertIn("Audit invalid — `code` — https://example.com/invalid-code", report)
        self.assertNotIn(
            "Audit verified — `project` — https://example.com/verified-project",
            report,
        )


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = json.loads(
            (ROOT / "data" / "taxonomy.json").read_text(encoding="utf-8")
        )
        cls.catalog = json.loads(
            (ROOT / "data" / "papers.json").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads(
            (ROOT / "data" / "manuscript_manifest.json").read_text(encoding="utf-8")
        )
        cls.validation = json.loads(
            (ROOT / "data" / "validation_report.json").read_text(encoding="utf-8")
        )
        cls.works = cls.catalog["works"]
        cls.grouped = GENERATE_DOCS.group_works_by_collection(cls.works)

    def _readme_text(self) -> str:
        lines = GENERATE_DOCS.make_readme(
            self.works,
            self.taxonomy,
            self.manifest,
            self.validation,
            {"checked_at": "2026-08-06"},
            self.catalog["title"],
            self.catalog["survey_title"],
            json.loads(
                (ROOT / "data" / "project_meta.json").read_text(encoding="utf-8")
            ),
        )
        return "\n".join(lines)

    def test_level_badge_colors_and_labels(self) -> None:
        expectations = {
            "L0": ("9AA5B1", "L0-Output", "l0-output-level-self-evolution"),
            "L1": ("4C78A8", "L1-Model", "l1-model-level-self-evolution"),
            "L2": ("2E8B57", "L2-Scaffold", "l2-scaffold-level-self-evolution"),
            "L3": ("E8842C", "L3-Improver", "l3-improver-level-self-evolution"),
            "L4": ("C0392B", "L4-Criterion", "l4-criterion-level-self-evolution"),
        }
        for level in self.taxonomy["levels"]:
            color, label, anchor = expectations[level["id"]]
            badge = GENERATE_DOCS.render_level_badge(level, self.taxonomy)
            self.assertIn(f"badge/{label}-{color}?style=flat-square", badge)
            self.assertIn(f"(#{anchor})", badge)
            self.assertIn(f"[![{label}]", badge)

    def test_level_summary_table_counts(self) -> None:
        table = "\n".join(
            GENERATE_DOCS.render_level_summary_table(
                self.taxonomy, self.grouped
            )
        )
        self.assertIn("| Level | Deepest active evolution target |", table)
        self.assertIn("| 42 |", table)
        self.assertIn("| 189 |", table)
        self.assertIn("| 287 |", table)
        self.assertIn("| 23 |", table)
        self.assertIn("| 66 |", table)
        self.assertIn("Current output or task-local trajectory", table)
        self.assertIn("Self-confirmation", table)
        self.assertNotIn("- ✍️ **L0 — Output:**", table)

    def test_contents_catalog_counts(self) -> None:
        readme = self._readme_text()
        expected = {
            "surveys-and-positioning": GENERATE_DOCS.collection_work_count(
                self.grouped, "surveys"
            ),
            "l0-output-level-self-evolution": GENERATE_DOCS.collection_work_count(
                self.grouped, "L0"
            ),
            "l1-model-level-self-evolution": GENERATE_DOCS.collection_work_count(
                self.grouped, "L1"
            ),
            "l2-scaffold-level-self-evolution": GENERATE_DOCS.collection_work_count(
                self.grouped, "L2"
            ),
            "l3-improver-level-self-evolution": GENERATE_DOCS.collection_work_count(
                self.grouped, "L3"
            ),
            "l4-criterion-level-self-evolution": GENERATE_DOCS.collection_work_count(
                self.grouped, "L4"
            ),
            "cross-level-reliability-evidence-acceptance-and-control":
                GENERATE_DOCS.collection_work_count(
                    self.grouped, "cross_level"
                ),
            "open-problems-and-outlook": GENERATE_DOCS.collection_work_count(
                self.grouped, "open_problems"
            ),
        }
        for anchor, count in expected.items():
            self.assertRegex(
                readme,
                rf"\(#{anchor}\)\s*`{count}`",
                msg=f"missing contents count for #{anchor}",
            )
        self.assertNotRegex(
            readme,
            r"#data-and-reproducibility\)\s*`\d+`",
        )

    def test_toc_stable_anchors_and_backlinks(self) -> None:
        readme = self._readme_text()
        self.assertIn('<div id="toc"></div>', readme)
        self.assertIn('<div id="contents"></div>', readme)
        self.assertIn('<div id="why-this-list-is-different"></div>', readme)
        self.assertIn('<div id="l1-model-level-self-evolution"></div>', readme)
        self.assertNotIn('<a id="l1-model-level-self-evolution"></a>', readme)
        self.assertIn(
            "## 🧭 Why This List Is Different "
            '<sub><a href="#toc">↑ contents</a></sub>',
            readme,
        )
        self.assertIn(
            "## ✍️ L0: Output-Level Self-Evolution "
            '<sub><a href="#toc">↑ contents</a></sub>',
            readme,
        )
        self.assertNotIn(
            "## 🗂️ Contents <sub><a href=\"#toc\">↑ contents</a></sub>",
            readme,
        )
        self.assertNotIn("⬆️ Back to top", readme)

    def test_explicit_anchors_are_separated_from_headings(self) -> None:
        readme = self._readme_text()
        self.assertRegex(readme, r'<div id="why-this-list-is-different"></div>\n\n## ')
        self.assertRegex(readme, r'<div id="L1\.self_training"></div>\n\n### ')
        self.assertNotRegex(readme, r'<div id="[^"]+"></div>\n#{2,3} ')

    def test_subcategory_jump_links_and_counts(self) -> None:
        readme = self._readme_text()
        self.assertIn(
            "**Jump to:** "
            "[Single-Model Self-Training (100)](#L1.self_training)",
            readme,
        )
        survey_count = GENERATE_DOCS.collection_work_count(
            self.grouped, "surveys"
        )
        self.assertIn(
            f"[Field Positioning and Related Surveys "
            f"({survey_count})](#surveys.positioning)",
            readme,
        )
        self.assertIn('<div id="L1.self_training"></div>', readme)
        self.assertIn('<div id="surveys.positioning"></div>', readme)
        jump_section = readme.split("## 🧠 L1: Model-Level Self-Evolution")[1]
        jump_section = jump_section.split("### Definition and Update Boundary")[0]
        self.assertIn("**Jump to:**", jump_section)
        self.assertNotIn("Definition and Update Boundary", jump_section)

    def test_collection_counts_helper(self) -> None:
        self.assertEqual(
            GENERATE_DOCS.collection_work_count(self.grouped, "surveys"),
            sum(
                len(works)
                for works in self.grouped.get("surveys", {}).values()
            ),
        )
        self.assertEqual(
            GENERATE_DOCS.collection_work_count(self.grouped, "L1"), 189
        )
        self.assertEqual(
            GENERATE_DOCS.subcategory_anchor_id(None, "L3"), "L3.additional"
        )


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(
            (ROOT / "data" / "papers.json").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads(
            (ROOT / "data" / "manuscript_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        cls.exclusions = json.loads(
            (ROOT / "data" / "exclusions.json").read_text(encoding="utf-8")
        )
        cls.works = cls.catalog["works"]

    def test_unique_work_ids(self) -> None:
        ids = [work["id"] for work in self.works]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_works_have_paper_links(self) -> None:
        self.assertTrue(all(work["paper_url"] for work in self.works))

    def test_active_manuscript_coverage(self) -> None:
        catalog_keys = {
            key
            for work in self.works
            if work["manuscript"]["active"]
            for key in work["manuscript"]["cited_bib_keys"]
        }
        self.assertEqual(catalog_keys, set(self.manifest["active_bib_keys"]))

    def test_taxonomy_representative_coverage(self) -> None:
        covered = {
            key
            for work in self.works
            if work["manuscript"]["representative"]
            for key in work["manuscript"]["cited_bib_keys"]
        }
        self.assertTrue(
            set(self.manifest["representative_bib_keys"]) <= covered
        )

    def test_subcategories_belong_to_their_level(self) -> None:
        for work in self.works:
            level = work.get("primary_level")
            subcategory = work.get("primary_subcategory")
            if level and subcategory:
                self.assertTrue(
                    subcategory.startswith(f"{level}."),
                    f"{work['id']}: {subcategory} does not belong to {level}",
                )

    def test_detailed_source_counts_are_preserved(self) -> None:
        """Every curated entry is either in the catalog or declared excluded."""
        counts = Counter(
            work["catalog_source"]["collection"]
            for work in self.works
            if work["catalog_source"]["file"]
            == "references/paper_detailed.md"
        )
        counts.update(
            record["collection"] for record in self.exclusions["works"].values()
        )
        self.assertEqual(
            counts,
            Counter(
                {
                    "surveys": 15,
                    "L0": 14,
                    "L1": 182,
                    "L2": 262,
                    "L3": 27,
                    "L4": 50,
                    "cross_level": 45,
                    "open_problems": 23,
                }
            ),
        )

    def test_exclusions_are_justified_and_uncited(self) -> None:
        catalog_ids = {work["id"] for work in self.works}
        for work_id, record in self.exclusions["works"].items():
            self.assertNotIn(work_id, catalog_ids)
            self.assertTrue(record.get("reason"))
            self.assertTrue(record.get("evidence"))


def extract_issue_form_field_blocks(text: str) -> dict[str, str]:
    """Split a GitHub issue form YAML body into per-field blocks keyed by id."""
    blocks: dict[str, str] = {}
    for match in re.finditer(
        r"^\s{2}-\s+type:\s+\S+\s*\n(.*?)(?=^\s{2}-\s+type:|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    ):
        block = match.group(0)
        id_match = re.search(r"^\s+id:\s+(\S+)\s*$", block, flags=re.MULTILINE)
        if id_match:
            blocks[id_match.group(1)] = block
    return blocks


def issue_field_is_required(block: str) -> bool:
    """Return True when a field block declares validations.required: true."""
    return bool(
        re.search(r"validations:\s*\n\s+required:\s+true\b", block)
    )


class GitHubConfigTests(unittest.TestCase):
    """Validate .github/ templates and workflows without extra YAML deps."""

    GITHUB = ROOT / ".github"
    ISSUE_TEMPLATES = GITHUB / "ISSUE_TEMPLATE"
    WORKFLOWS = GITHUB / "workflows"

    PAPER_SUGGESTION_REQUIRED_FIELD_IDS = (
        "canonical_title",
        "canonical_paper_url",
        "first_public_date_and_venue",
        "official_code_and_project_urls",
        "code_project_evidence",
        "proposed_level_and_subcategory",
        "evolution_target",
        "persists_across_tasks",
    )

    BROKEN_LINK_REQUIRED_FIELD_IDS = (
        "broken_url",
        "work_title",
        "artifact_kind",
        "observed_behavior",
    )

    BROKEN_LINK_OPTIONAL_FIELD_IDS = ("alternative_url",)

    PR_CHECK_ITEMS = (
        "Identifiers are unique",
        "Paper URLs are canonical and reachable",
        "Code/project URLs are official or explicitly marked third-party",
        "Classification rationale names the evolution target",
        "Primary level and subcategory agree",
        "Existing source counts and manuscript coverage do not regress",
        "Generated documentation is up to date",
        "No local file paths, private hosts, credentials, or unpublished "
        "identity-bearing metadata",
    )

    LINK_ISSUE_TITLE = "Link audit: dead URLs detected"

    def _read(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    def _lower(self, path: Path) -> str:
        return self._read(path).lower()

    def test_issue_template_files_exist(self) -> None:
        expected = [
            self.ISSUE_TEMPLATES / "paper_suggestion.yml",
            self.ISSUE_TEMPLATES / "broken_link.yml",
            self.ISSUE_TEMPLATES / "config.yml",
        ]
        for path in expected:
            self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")

    def test_workflow_files_exist(self) -> None:
        expected = [
            self.WORKFLOWS / "validate.yml",
            self.WORKFLOWS / "link-check.yml",
        ]
        for path in expected:
            self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")

    def test_pull_request_template_exists(self) -> None:
        self.assertTrue(
            (self.GITHUB / "PULL_REQUEST_TEMPLATE.md").is_file(),
            "missing .github/PULL_REQUEST_TEMPLATE.md",
        )

    def test_paper_suggestion_form_covers_contributing_fields(self) -> None:
        text = self._read(self.ISSUE_TEMPLATES / "paper_suggestion.yml")
        blocks = extract_issue_form_field_blocks(text)
        self.assertIn("contributing", text.lower())
        for field_id in self.PAPER_SUGGESTION_REQUIRED_FIELD_IDS:
            self.assertIn(
                field_id,
                blocks,
                f"paper_suggestion missing field block {field_id!r}",
            )
            self.assertTrue(
                issue_field_is_required(blocks[field_id]),
                f"paper_suggestion.{field_id} must declare validations.required: true",
            )
        self.assertNotIn(
            "additional_context",
            self.PAPER_SUGGESTION_REQUIRED_FIELD_IDS,
        )
        self.assertIn("additional_context", blocks)
        self.assertFalse(
            issue_field_is_required(blocks["additional_context"]),
            "paper_suggestion.additional_context must remain optional",
        )

    def test_broken_link_form_covers_required_fields(self) -> None:
        text = self._read(self.ISSUE_TEMPLATES / "broken_link.yml")
        blocks = extract_issue_form_field_blocks(text)
        for field_id in self.BROKEN_LINK_REQUIRED_FIELD_IDS:
            self.assertIn(
                field_id,
                blocks,
                f"broken_link missing field block {field_id!r}",
            )
            self.assertTrue(
                issue_field_is_required(blocks[field_id]),
                f"broken_link.{field_id} must declare validations.required: true",
            )
        for field_id in self.BROKEN_LINK_OPTIONAL_FIELD_IDS:
            self.assertIn(
                field_id,
                blocks,
                f"broken_link missing field block {field_id!r}",
            )
            self.assertFalse(
                issue_field_is_required(blocks[field_id]),
                f"broken_link.{field_id} must remain optional",
            )

    def test_issue_template_config_disables_blank_issues(self) -> None:
        text = self._read(self.ISSUE_TEMPLATES / "config.yml")
        self.assertIn("blank_issues_enabled: false", text)
        self.assertIn("contact_links: []", text)

    def test_pull_request_template_has_eight_checks(self) -> None:
        text = self._read(self.GITHUB / "PULL_REQUEST_TEMPLATE.md")
        self.assertIn("README.md", text)
        self.assertIn("generated", text.lower())
        self.assertIn("data/", text)
        self.assertIn("generate_docs.py", text)
        checkboxes = [line for line in text.splitlines() if line.startswith("- [ ]")]
        self.assertEqual(len(checkboxes), 8, checkboxes)
        for item in self.PR_CHECK_ITEMS:
            self.assertIn(item, text, f"PR template missing check: {item}")

    def test_validate_workflow_commands_and_permissions(self) -> None:
        text = self._read(self.WORKFLOWS / "validate.yml")
        self.assertIn("pull_request:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("contents: read", text)
        self.assertIn("actions/checkout@v4", text)
        self.assertIn("actions/setup-python@v5", text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn("python -m pytest tests", text)
        self.assertIn(
            "python scripts/validate_catalog.py --report data/validation_report.json",
            text,
        )
        self.assertIn("python scripts/generate_docs.py", text)
        self.assertIn("git diff --exit-code", text)

    def test_link_check_workflow_audit_issue_and_artifacts(self) -> None:
        text = self._read(self.WORKFLOWS / "link-check.yml")
        self.assertIn("schedule:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("contents: read", text)
        self.assertIn("issues: write", text)
        self.assertIn("actions/checkout@v4", text)
        self.assertIn("actions/setup-python@v5", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("actions/github-script@v7", text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn("python scripts/check_links.py", text)
        self.assertNotIn("--write", text)
        self.assertNotIn("--fail-on-dead", text)
        self.assertIn("python scripts/generate_docs.py", text)
        self.assertIn("data/link_audit.json", text)
        self.assertIn("docs/LINK_AUDIT.md", text)
        self.assertIn("README.md", text)
        self.assertIn("dead_urls", text)
        self.assertIn(self.LINK_ISSUE_TITLE, text)
        self.assertIn("github.paginate(github.rest.issues.listForRepo", text)
        self.assertIn("pull_request", text)
        self.assertIn("github.rest.issues.create", text)
        self.assertIn("github.rest.issues.update", text)
        self.assertIn("concurrency:", text)
        self.assertIn("timeout-minutes:", text)
        self.assertNotIn("git commit", text.lower())
        self.assertNotIn("git push", text.lower())
        self.assertNotIn("labels:", text)


if __name__ == "__main__":
    unittest.main()
