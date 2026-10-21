import contextlib
import copy
import hashlib
import io
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hubradar import finalize, prepare, radar
from hubradar.cli import main
from hubradar.html_report import render_file, render_markdown


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "source"
        self.repo.mkdir()
        self.source = "export function original() {\n" + "\n".join(f"  const v{i} = {i};" for i in range(25)) + "\n  return 42;\n}\n"
        (self.repo / "index.ts").write_text(self.source)
        (self.repo / "package.json").write_text('{"name":"fixture","exports":"./index.ts"}')
        (self.repo / "README.md").write_text("# Fixture\n\nOriginal source.\n")
        secret = self.base / "secret.ts"
        secret.write_text("NEVER_READ_OUTSIDE_REPOSITORY")
        (self.repo / "escape.ts").symlink_to(secret)
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=HubRadar Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
        self.sha = self.git("rev-parse", "HEAD").strip()
        self.facts = {
            "repo": "fixture/source", "sha": self.sha, "signal_index": {"issues": []},
            "coverage": {"grade": "filtered_static_scan", "src_files": 1},
            "tokens": {"evidence_total": 10, "source_full_estimate": 30},
            "timings": {"total_s": 0},
        }
        self.raw = {
            "repo": "fixture/source", "sha": self.sha,
            "essence": {"text": "A fixture.", "claim_ids": ["c1"]},
            "solves": "fixture", "not_solves": "production",
            "abstractions": [], "patterns": [], "tradeoffs": [], "pitfalls": [], "steal": [],
            "dataflow": {"nodes": [{"id": "a", "label": "entry"}], "edges": []},
            "state_machines": [],
            "mvp": {"language": "ts", "code": "return 42;", "mappings": []},
            "verdict": {"decision": "learn", "reason": "example"},
            "reading_route": [{"path": "index.ts", "why": "entry"}],
            "claims": [{"id": "c1", "type": "源码事实", "text": "Exports original.",
                        "anchors": [{"path": "index.ts", "start": 1, "end": 1, "quote": "export function original() {"}]}],
        }

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True)

    def test_prepare_uses_head_and_excludes_symlinks(self):
        (self.repo / "index.ts").write_text("export function tampered() { return -1; }")
        with patch.object(prepare, "gh_json", side_effect=AssertionError("offline must not request GitHub")):
            with contextlib.redirect_stdout(io.StringIO()):
                prepare.main(self.repo, "fixture/source", self.base / "work", offline=True)
        evidence = (self.base / "work/evidence.md").read_text()
        self.assertIn("original", evidence)
        self.assertNotIn("tampered", evidence)
        self.assertNotIn("NEVER_READ_OUTSIDE_REPOSITORY", evidence)
        facts = json.loads((self.base / "work/facts.json").read_text())
        self.assertEqual(facts["sha"], self.sha)
        self.assertEqual(facts["coverage"]["source"], "committed_HEAD")

    def test_reject_output_inside_source(self):
        with self.assertRaises(ValueError):
            prepare.main(self.repo, "fixture/source", self.repo / "output", offline=True)

    def test_valid_claim_and_tamper_detection(self):
        self.assertEqual(finalize.validate(self.raw, self.facts, self.repo)[1], [])
        for change in ("missing_quote", "wrong_quote", "wrong_sha", "duplicate_id", "bad_edge"):
            raw = copy.deepcopy(self.raw)
            if change == "missing_quote":
                del raw["claims"][0]["anchors"][0]["quote"]
            elif change == "wrong_quote":
                raw["claims"][0]["anchors"][0]["quote"] = "this was never in source"
            elif change == "wrong_sha":
                raw["sha"] = "0" * 40
            elif change == "duplicate_id":
                raw["claims"].append(copy.deepcopy(raw["claims"][0]))
            else:
                raw["dataflow"]["edges"].append({"from": "a", "to": "missing", "label": "", "claim_ids": []})
            with self.subTest(change=change):
                self.assertTrue(finalize.validate(raw, self.facts, self.repo)[1])

    def test_cli_finalize_and_html(self):
        work = self.base / "work"
        work.mkdir()
        (work / "facts.json").write_text(json.dumps(self.facts))
        (work / "raw_distill.json").write_text(json.dumps(self.raw))
        out = self.base / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["finalize", str(work), "--source", str(self.repo), "-o", str(out), "--html"])
        self.assertEqual(result, 0)
        self.assertTrue((out / "index.html").is_file())
        self.assertNotIn("Hono", (out / "card.md").read_text())
        self.raw["claims"][0]["anchors"][0]["quote"] = ""
        (work / "raw_distill.json").write_text(json.dumps(self.raw))
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["finalize", str(work), "--source", str(self.repo), "-o", str(self.base / "invalid"), "--html"])
        self.assertEqual(result, 1)
        self.assertFalse((self.base / "invalid/index.html").exists())

    def test_cli_arch(self):
        out = self.base / "arch.svg"
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["arch", "-o", str(out)])
        self.assertEqual(result, 0)
        self.assertTrue(out.is_file())
        self.assertIn("Hono 核心系统架构", out.read_text(encoding="utf-8"))


class ReportTests(unittest.TestCase):
    def test_sanitize_and_keep_details_code_table(self):
        source = """# <img src=x onerror=alert(1)> Title

## Details
<details><summary>More</summary>

```python
print("<script>alert('not executable')</script>")
```

</details>

| A | B |
|---|---|
| 1 | 2 |

<script>alert("malicious")</script>
<a href="javascript:alert(1)" onclick="alert(1)">unsafe</a>
"""
        page = render_markdown(source)
        article = page.split('<article id="report">')[1].split("</article>")[0]
        self.assertNotIn('<script>alert("malicious")', article)
        self.assertNotIn('onclick="alert', article)
        self.assertNotIn('href="javascript:', article)
        self.assertNotIn("<img ", article)
        self.assertIn("<details><summary>More</summary>", article)
        self.assertIn("<table>", article)
        self.assertIn('id="section-1"', article)
        self.assertIn("&lt;script&gt;", article)
        self.assertNotIn("<script src=", page)

    def test_mermaid_source_is_preserved_for_browser_engine(self):
        page = render_markdown("# Flow\n\n```mermaid\nflowchart LR\n a[\"Start\"]\n b[\"End\"]\n a --> b\n```\n")
        article = page.split('<article id="report">')[1].split("</article>")[0]
        self.assertIn('data-diagram-status="pending"', article)
        self.assertIn("a --&gt; b", article)
        page = render_markdown("# Sequence\n\n```mermaid\nsequenceDiagram\n A->>B: hi\n```\n")
        self.assertIn('class="mermaid-target"', page)
        self.assertIn("sequenceDiagram", page)

    def test_card_fixture_schedules_all_diagrams(self):
        source = Path(__file__).resolve().parents[1] / "gallery/honojs__hono/card.md"
        page = render_markdown(source.read_text())
        self.assertEqual(page.count('class="diagram-card"'), 3)
        self.assertIn('id="hubradar-mermaid"', page)

    def test_vendor_integrity_license_and_script_boundaries(self):
        vendor = Path(__file__).resolve().parents[1] / "hubradar/assets/vendor"
        metadata = json.loads((vendor / "mermaid.provenance.json").read_text())
        self.assertEqual(hashlib.sha256((vendor / "mermaid.min.js").read_bytes()).hexdigest(), metadata["sha256"])
        page = render_markdown('# Test\n\n```mermaid\nflowchart TD\n a["</script><script>bad()</script>"]\n```\n')
        # Exactly the two trusted runtime scripts; a Mermaid label cannot end one.
        self.assertEqual(len(re.findall(r"</script\s*>", page, re.IGNORECASE)), 2)
        self.assertIn("Copyright (c) 2014 - 2022 Knut Sveidqvist", page)
        self.assertIn("&lt;/script&gt;", page)

    def test_output_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "card.md"
            path.write_text("# Card")
            with self.assertRaises(ValueError):
                render_file(path, path)
            self.assertEqual(path.read_text(), "# Card")

    def test_dsh_architecture_svg_generation_and_safety(self):
        import xml.etree.ElementTree as ET
        from hubradar.dsh_architecture import build_hono_architecture_spec, generate_dsh_svg
        spec = build_hono_architecture_spec()
        svg = generate_dsh_svg(spec)
        root = ET.fromstring(svg)
        self.assertEqual(root.get("viewBox"), "0 0 1000 680")
        self.assertEqual(root.get("width"), "1000")
        self.assertEqual(root.get("height"), "680")
        self.assertEqual(root.get("role"), "img")
        anchors = root.findall(".//{http://www.w3.org/2000/svg}a")
        self.assertEqual(len(anchors), 8)
        for a in anchors:
            self.assertTrue(a.get("href", "").startswith("https://github.com/"))
            self.assertEqual(a.get("target"), "_blank")
        # Ensure no javascript injection
        bad_spec = {"title": "XSS", "layers": [{"name": "L", "cards": [{"title": "T", "href": "javascript:alert(1)"}]}]}
        bad_svg = generate_dsh_svg(bad_spec)
        self.assertNotIn("javascript:", bad_svg)

    def test_dsh_fence_rendering_and_bleach_bypass(self):
        page = render_markdown("# Architecture\n\n```dsh-architecture\nhono\n```\n")
        self.assertIn('class="diagram-card dsh-architecture"', page)
        self.assertIn("<svg", page)
        self.assertIn('class="card-anchor"', page)
        # Verify SVG elements survived bleach
        self.assertIn("<rect", page)
        self.assertIn("viewBox=", page)

    def test_dsh_only_page_omits_mermaid_runtime(self):
        page = render_markdown("# Architecture\n\n```dsh-architecture\nhono\n```\n")
        self.assertNotIn('id="hubradar-mermaid"', page)
        # Should be lightweight (< 50KB) instead of 3.6MB
        self.assertLess(len(page.encode("utf-8")), 50000)

    def test_mermaid_page_includes_mermaid_runtime(self):
        page = render_markdown("# Flow\n\n```mermaid\nflowchart LR\n A --> B\n```\n")
        self.assertIn('id="hubradar-mermaid"', page)
        self.assertGreater(len(page.encode("utf-8")), 3000000)


class RadarTests(unittest.TestCase):
    def test_api_failure_not_empty_success(self):
        with patch.object(radar, "gh", return_value=None):
            with self.assertRaises(ValueError):
                radar.search("topic:example")

    def test_missing_history_retains_unknown_repository(self):
        meta = {"nameWithOwner": "fixture/repo", "stargazerCount": 1000, "forkCount": 50,
                "createdAt": "2025-01-01T00:00:00Z", "pushedAt": "2026-10-01T00:00:00Z",
                "isArchived": False, "licenseInfo": {"spdxId": "MIT"}, "primaryLanguage": {"name": "TypeScript"},
                "description": "data | example", "repositoryTopics": {"nodes": []}, "issues": {"totalCount": 10},
                "defaultBranchRef": {"target": {"history": {"totalCount": 20}}}}
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            domain = base / "domain.json"
            domain.write_text(json.dumps({"name": "test", "queries": [], "seeds": ["fixture/repo"]}))
            with patch.object(radar, "enrich", return_value={"fixture/repo": meta}), \
                 patch.object(radar, "star_history", return_value=None), \
                 patch.object(radar, "adoption", return_value=(None, None)), \
                 contextlib.redirect_stdout(io.StringIO()):
                radar.main(domain, base / "out")
            rows = json.loads((base / "out/radar.json").read_text())["rows"]
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0]["v7"])
            self.assertEqual(rows[0]["tier"], "趋势未知")
            self.assertIn("data \\| example", (base / "out/radar.md").read_text())


if __name__ == "__main__":
    unittest.main()
