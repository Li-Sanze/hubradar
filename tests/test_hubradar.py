import contextlib
import copy
import hashlib
import io
import json
import re
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from hubradar import finalize, prepare, radar
from hubradar.cli import main
from hubradar.dsh_architecture import compile_dsh_spec, fit_text, generate_dsh_svg, get_example_spec
from hubradar.fixtures import build_hono_architecture_spec, build_hubradar_architecture_spec
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


class ArchitectureTests(unittest.TestCase):
    NS = {"s": "http://www.w3.org/2000/svg"}

    def spec(self, count=3):
        return {
            "title": "通用系统", "subtitle": "分层与数据流",
            "layers": [{"id": "ingress", "name": "接入平面", "cards": [
                {"id": f"node-{i}", "title": f"服务 {i}", "desc": "职责说明", "color": "blue"}
                for i in range(count)
            ]}],
            "edges": [],
        }

    def assert_disjoint(self, boxes):
        for i, left in enumerate(boxes):
            for right in boxes[i + 1:]:
                self.assertTrue(left["right"] <= right["left"] or right["right"] <= left["left"]
                                or left["bottom"] <= right["top"] or right["bottom"] <= left["top"],
                                f"Overlapping cards: {left}, {right}")

    def assert_orthogonal(self, points):
        for a, b in zip(points, points[1:]):
            self.assertTrue(a[0] == b[0] or a[1] == b[1], f"Diagonal segment: {a}, {b}")

    def assert_routes_clear_cards(self, compiled):
        for edge in compiled["connectors"]:
            for cid, card in compiled["card_index"].items():
                if cid in (edge["from"], edge["to"]):
                    continue
                for a, b in zip(edge["points"], edge["points"][1:]):
                    crosses = (a[0] == b[0] and card["left"] < a[0] < card["right"]
                               and min(a[1], b[1]) < card["bottom"] and max(a[1], b[1]) > card["top"])
                    crosses |= (a[1] == b[1] and card["top"] < a[1] < card["bottom"]
                                and min(a[0], b[0]) < card["right"] and max(a[0], b[0]) > card["left"])
                    self.assertFalse(crosses, f"Edge {edge} crosses {cid}")

    def test_semantic_layout_is_deterministic_bounded_and_non_overlapping(self):
        for layer_count in range(1, 5):
            for count in range(1, 5):
                with self.subTest(layers=layer_count, cards=count):
                    self.check_layout(layer_count, count)

    def check_layout(self, layer_count, count):
        spec = self.spec(count)
        spec["layers"] = [
            {"id": f"layer-{i}", "cards": [
                {**card, "id": f'{card["id"]}-{i}'} for card in spec["layers"][0]["cards"]]}
            for i in range(layer_count)
        ]
        original = copy.deepcopy(spec)
        compiled = compile_dsh_spec(spec)
        self.assertEqual(spec, original)
        self.assertEqual(generate_dsh_svg(spec), generate_dsh_svg(spec))
        boxes = list(compiled["card_index"].values())
        self.assert_disjoint(boxes)
        svg = ET.fromstring(generate_dsh_svg(spec))
        self.assertEqual(svg.get("viewBox"), f'0 0 1000 {compiled["height"]}')
        self.assertEqual(len(svg.findall('.//s:g[@data-card-id]', self.NS)), count * layer_count)
        for card in boxes:
            layer = compiled["layers"][card["layer"]]
            self.assertGreaterEqual(card["left"], 60)
            self.assertLessEqual(card["right"], 940)
            self.assertGreaterEqual(card["top"], layer["y"] + 35)
            self.assertLessEqual(card["bottom"], layer["y"] + layer["height"])
            self.assertLess(card["bottom"], compiled["height"])
        expected_width = 840 if count == 1 else 270 if count == 3 else 410
        self.assertEqual(boxes[0]["w"], expected_width)
        if layer_count == 4:
            self.assertGreater(compiled["height"], 680)

    def test_four_cards_wrap_as_two_by_two(self):
        compiled = compile_dsh_spec(self.spec(4))
        cards = list(compiled["card_index"].values())
        self.assertEqual(len({c["x"] for c in cards}), 2)
        self.assertEqual(len({c["y"] for c in cards}), 2)
        self.assertEqual(cards[0]["y"], cards[1]["y"])
        self.assertGreater(cards[2]["y"], cards[0]["bottom"])
        self.assertEqual(cards[0]["w"], 410)
        self.assert_disjoint(cards)

    def test_code_pills_flow_below_text_and_set_row_height(self):
        spec = self.spec(4)
        spec["layers"][0]["cards"][0].update(code_pill="main(sys.argv)", badge="1", pill_desc="源码入口")
        compiled = compile_dsh_spec(spec)
        card = compiled["layers"][0]["cards"][0]
        self.assertGreaterEqual(card["height"], 110)
        self.assertLessEqual(card["height"], 130)
        self.assertGreater(card["pill_y"], 48)
        self.assertLessEqual(card["pill_y"] + card["pill_h"] + 16, card["height"])
        self.assertGreater(compiled["card_index"]["node-2"]["top"], card["y"] + card["height"])
        group = ET.fromstring(generate_dsh_svg(spec)).find('.//s:g[@data-card-id="node-0"]', self.NS)
        pill = group.find('s:text[@class="code-pill"]', self.NS)
        title = group.find('s:text[@class="card-title"]', self.NS)
        self.assertGreater(float(pill.get("y")), float(title.get("y")) + 30)

    def test_card_titles_preserve_full_text_and_escape_markup(self):
        for code in (None, "", 'graph.add_node("<script>&")'):
            with self.subTest(code=code):
                spec = self.spec()
                card = spec["layers"][0]["cards"][0]
                card.update(title='完整标题 <script> & "节点"' * 5, desc="完整描述 <desc> & 证据" * 5,
                            code_pill=code, href="https://example.com/source#L1")
                root = ET.fromstring(generate_dsh_svg(spec))
                group = root.find('.//s:g[@data-card-id="node-0"]', self.NS)
                expected = f'{card["title"]} - {card["desc"]}' + (f": {code}" if code else "")
                self.assertEqual(group.find("s:title", self.NS).text, expected)
                self.assertEqual(len(group.find("s:title", self.NS)), 0)
                self.assertFalse(root.findall(".//s:script", self.NS))
                self.assertNotEqual(group.find('s:text[@class="card-title"]', self.NS).text, card["title"])
                # Unlinked cards also expose their complete text.
                self.assertEqual(root.find('.//s:g[@data-card-id="node-1"]/s:title', self.NS).text,
                                 "服务 1 - 职责说明")

    def test_code_pills_use_actual_font_size_and_keep_identifiers_whole(self):
        spec = self.spec()
        code = "top_defs(root, lang) & nx.DiGraph()"
        spec["layers"][0]["cards"][0]["code_pill"] = code
        root = ET.fromstring(generate_dsh_svg(spec))
        pill = root.find('.//s:g[@data-card-id="node-0"]/s:text[@class="code-pill"]', self.NS)
        self.assertEqual(pill.text, code)
        self.assertEqual(fit_text("nx.DiGraph()", 65, 10.5, preserve_tokens=True), "nx.…")
        self.assertEqual(fit_text("VeryLongIdentifier()", 65, 10.5, preserve_tokens=True), "…")
        self.assertEqual(fit_text("短代码()", 65, 10.5, preserve_tokens=True), "短代码()")

    def test_semantic_edges_are_orthogonal_and_use_distinct_gutter_lanes(self):
        spec = self.spec()
        spec["layers"][0]["cards"][0]["code_pill"] = "entry()"
        spec["layers"].append({"id": "kernel", "name": "执行平面", "cards": [
            {"id": "prepare", "title": "证据准备", "desc": "静态分析"}]})
        spec["edges"] = [{"from": "node-0", "to": "node-1"}] + [
            {"from": f"node-{i}", "to": "prepare", "style": "dashed", "color": "#94a3b8"}
            for i in range(3)]
        compiled = compile_dsh_spec(spec)
        source, target = compiled["layers"]
        self.assertGreater(target["y"], source["y"] + source["height"])
        self.assertEqual(len({c["points"][1][1] for c in compiled["connectors"][1:]}), 3)
        for conn in compiled["connectors"]:
            self.assert_orthogonal(conn["points"])
        for conn in compiled["connectors"][1:]:
            self.assertEqual(len(conn["points"]), 4)
            self.assertGreater(conn["points"][1][1], source["y"] + source["height"])
            self.assertLess(conn["points"][1][1], target["y"])
        self.assert_routes_clear_cards(compiled)
        svg = ET.fromstring(generate_dsh_svg(spec))
        lines = svg.findall('s:polyline[@data-edge-to="prepare"]', self.NS)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(line.get("stroke-dasharray") == "5 4" for line in lines))
        for line in lines:
            points = [[float(v) for v in point.split(",")] for point in line.get("points").split()]
            self.assert_orthogonal(points)

    def test_wrapped_reverse_and_skipped_layer_routes_avoid_other_cards(self):
        spec = self.spec(4)
        spec["layers"].extend([
            {"id": "middle", "cards": [{"id": "middle-card", "title": "中间层"}]},
            {"id": "bottom", "cards": [{"id": "last", "title": "目标"}]},
        ])
        spec["edges"] = [
            {"from": "node-0", "to": "node-3"}, {"from": "node-1", "to": "node-0"},
            {"from": "node-0", "to": "middle-card"}, {"from": "middle-card", "to": "node-2"},
            {"from": "node-0", "to": "last"}, {"from": "last", "to": "node-3"},
        ]
        compiled = compile_dsh_spec(spec)
        for conn in compiled["connectors"]:
            self.assert_orthogonal(conn["points"])
        self.assert_routes_clear_cards(compiled)
        ET.fromstring(generate_dsh_svg(spec))

    def test_legacy_geometry_connectors_and_source_anchors_are_preserved(self):
        spec = {"height": 680, "layers": [{"x": 40, "y": 80, "width": 920, "height": 200,
                "cards": [{"x": 60, "y": 120, "width": 300, "height": 100,
                           "href": "https://github.com/owner/repo/blob/SHA/main.py#L1"}]}],
                "connectors": [{"type": "line", "x1": 360, "y1": 170, "x2": 400, "y2": 170}]}
        compiled = compile_dsh_spec(spec)
        self.assertEqual(compiled["height"], 680)
        self.assertEqual(compiled["connectors"], spec["connectors"])
        before, after = spec["layers"][0], compiled["layers"][0]
        for field in ("x", "y", "width", "height"):
            self.assertEqual(before[field], after[field])
        for field in ("x", "y", "width", "height", "href"):
            self.assertEqual(before["cards"][0][field], after["cards"][0][field])
        root = ET.fromstring(generate_dsh_svg(spec))
        self.assertEqual(len(root.findall('.//s:a', self.NS)), 1)

    def test_fixtures_are_semantic_and_compile_to_clear_routes(self):
        for builder in (build_hono_architecture_spec, build_hubradar_architecture_spec):
            with self.subTest(builder=builder.__name__):
                spec = builder()
                self.assert_semantic(spec)
                self.assertTrue(spec["edges"])
                compiled = compile_dsh_spec(spec)
                self.assert_disjoint(list(compiled["card_index"].values()))
                self.assert_routes_clear_cards(compiled)
                for edge in compiled["connectors"]:
                    self.assert_orthogonal(edge["points"])
                root = ET.fromstring(generate_dsh_svg(spec))
                expected_cards = sum(len(layer["cards"]) for layer in spec["layers"])
                self.assertEqual(len(root.findall('.//s:a', self.NS)), expected_cards)

    def assert_semantic(self, value):
        if isinstance(value, dict):
            self.assertFalse({"x", "y", "width", "height", "points", "connectors", "pill_y", "pill_h"} & value.keys())
            for child in value.values():
                self.assert_semantic(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_semantic(child)

    def test_gallery_contracts_render_without_fixtures_and_reproduce_artifacts(self):
        gallery = Path(__file__).resolve().parents[1] / "gallery"
        for folder, name, builder in (("hubradar", "hubradar", build_hubradar_architecture_spec),
                                      ("honojs__hono", "hono", build_hono_architecture_spec)):
            with self.subTest(folder=folder):
                card = (gallery / folder / "card.md").read_text(encoding="utf-8")
                source = re.search(r"```dsh-architecture\n(.*?)\n```", card, re.S).group(1)
                spec = json.loads(source)
                self.assert_semantic(spec)
                self.assertEqual(spec, builder())
                with patch("hubradar.fixtures.build_hono_architecture_spec", side_effect=AssertionError("fixture called")), \
                     patch("hubradar.fixtures.build_hubradar_architecture_spec", side_effect=AssertionError("fixture called")):
                    page = render_markdown(card)
                    svg = generate_dsh_svg(spec)
                    self.assertIn(svg, page)
                    self.assertNotIn('data-diagram-status="error"', page)
                    self.assertEqual(svg, (gallery / folder / f"{name}-architecture.svg").read_text(encoding="utf-8"))
                    self.assertEqual(page, (gallery / folder / "index.html").read_text(encoding="utf-8"))
                    original = compile_dsh_spec(spec)
                    spec["layers"][0]["cards"][0]["title"] = "契约修改后重新排版"
                    spec["layers"][0]["cards"].append({"id": "extra", "title": "新卡片"})
                    spec["edges"].append({"from": "extra", "to": spec["layers"][1]["cards"][0]["id"]})
                    compiled = compile_dsh_spec(spec)
                    first = spec["layers"][0]["cards"][0]["id"]
                    self.assertNotEqual(original["card_index"][first]["w"], compiled["card_index"][first]["w"])
                    while len(spec["layers"][0]["cards"]) < 4:
                        spec["layers"][0]["cards"].append({"id": f"wrap_{len(spec['layers'][0]['cards'])}", "title": "网格换行卡片"})
                    wrapped = compile_dsh_spec(spec)
                    last_id = spec["layers"][0]["cards"][-1]["id"]
                    self.assertGreater(wrapped["card_index"][last_id]["y"], wrapped["card_index"][first]["y"])
                    self.assert_routes_clear_cards(compiled)
                    changed = render_markdown(f"```dsh-architecture\n{json.dumps(spec)}\n```\n")
                    self.assertIn("契约修改后重新排版", changed)
                    self.assertIn('data-card-id="extra"', changed)
                    self.assertIn(generate_dsh_svg(spec), changed)

    def test_invalid_schema_and_geometry_raise_instead_of_creating_another_diagram(self):
        invalid = [None, [], {}, {"layers": {}}, {"layers": [{"cards": {}}]},
                   {"layers": [{"cards": []}]}, self.spec(5), {"layers": self.spec()["layers"] * 5}]
        for field, value in (("id", "node-1"), ("height", 0), ("width", -1), ("x", float("nan"))):
            spec = self.spec()
            spec["layers"][0]["cards"][0][field] = value
            invalid.append(spec)
        spec = self.spec()
        spec["edges"] = [{"from": "node-0", "to": "absent"}]
        invalid.append(spec)
        for spec in invalid:
            with self.subTest(spec=spec), self.assertRaises((ValueError, TypeError)):
                generate_dsh_svg(spec)

    def test_compiled_spec_can_be_rendered_again_without_duplicate_edges(self):
        spec = self.spec(2)
        spec["edges"] = [{"from": "node-0", "to": "node-1"}]
        compiled = compile_dsh_spec(spec)
        self.assertEqual(compile_dsh_spec(compiled), compiled)
        root = ET.fromstring(generate_dsh_svg(compiled))
        self.assertEqual(len(root.findall('s:polyline', self.NS)), 1)

    def test_dynamic_attributes_and_text_cannot_inject_svg_elements(self):
        attack = '\"><script>alert(1)</script><rect onload="alert(1)'
        spec = self.spec(1)
        spec.update(title=attack, subtitle=attack, slug=attack)
        spec["layers"][0].update(name=attack, container_fill=attack)
        spec["layers"][0]["cards"][0].update(title=attack, desc=attack, badge=attack,
                                                href='https://example.com/?q=" onclick="alert(1)', code_pill=attack)
        spec["connectors"] = [{"type": "polyline", "points": [[10, 10], [20, 10]], "color": attack, "dash": attack}]
        spec["legend"] = {"items": [{"label": attack, "color": attack}]}
        svg = generate_dsh_svg(spec)
        root = ET.fromstring(svg)
        for element in root.iter():
            self.assertNotEqual(element.tag.rsplit("}", 1)[-1], "script")
            self.assertFalse(any(key.lower().startswith("on") for key in element.attrib))
        self.assertIn("&lt;script&gt;", svg)
        spec["connectors"][0]["marker"] = "url(https://untrusted.invalid/arrow.svg#arrow-blue)"
        with self.assertRaises(ValueError):
            generate_dsh_svg(spec)

    def test_examples_are_explicit_benchmarks_and_independent(self):
        for name in ("hubradar", "hono"):
            spec = get_example_spec(name)
            self.assertIn("Benchmark", spec["subtitle"])
            spec["layers"].clear()
            self.assertTrue(get_example_spec(name)["layers"])
        with self.assertRaises(ValueError):
            get_example_spec("unknown")

    def test_cli_missing_or_invalid_spec_returns_two_and_preserves_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out = base / "arch.svg"
            out.write_text("existing diagram")
            invalid = base / "invalid.json"
            invalid.write_text('{"layers":')
            for inputs in (["--spec", str(base / "missing.json")], [str(base / "missing.json")],
                           ["--spec", str(invalid)], ["--spec", str(base)]):
                stdout, stderr = io.StringIO(), io.StringIO()
                with self.subTest(inputs=inputs), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    self.assertEqual(main(["arch", *inputs, "-o", str(out)]), 2)
                self.assertTrue(stderr.getvalue())
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(out.read_text(), "existing diagram")

    def test_cli_semantic_spec_and_named_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "spec.json"
            source.write_text(json.dumps(self.spec(4)))
            for inputs in (["--spec", str(source)], [str(source)], ["--example", "hono"], ["--example", "hubradar"]):
                stdout = io.StringIO()
                with self.subTest(inputs=inputs), contextlib.redirect_stdout(stdout):
                    self.assertEqual(main(["arch", *inputs]), 0)
                svg = stdout.getvalue()
                ET.fromstring(svg)
                if "--example" in inputs:
                    self.assertIn("Benchmark", svg)
                else:
                    self.assertIn("通用系统", svg)
                    self.assertNotIn("Hono", svg)
            for inputs in (["--spec", str(source), "--example", "hono"], [str(source), "--example", "hono"]):
                with self.subTest(inputs=inputs), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                    main(["arch", *inputs])
                self.assertEqual(exc.exception.code, 2)


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
        spec = build_hono_architecture_spec()
        height = compile_dsh_spec(spec)["height"]
        svg = generate_dsh_svg(spec)
        root = ET.fromstring(svg)
        self.assertEqual(root.get("viewBox"), f"0 0 1000 {height}")
        self.assertEqual(root.get("width"), "1000")
        self.assertEqual(root.get("height"), str(height))
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
        source = json.dumps(build_hono_architecture_spec())
        page = render_markdown(f"# Architecture\n\n```dsh-architecture\n{source}\n```\n")
        self.assertIn('class="diagram-card dsh-architecture"', page)
        self.assertIn("<svg", page)
        self.assertIn('class="card-anchor"', page)
        # Verify SVG elements survived bleach
        self.assertIn("<rect", page)
        self.assertIn("viewBox=", page)

    def test_dsh_only_page_omits_mermaid_runtime(self):
        source = json.dumps(build_hono_architecture_spec())
        page = render_markdown(f"# Architecture\n\n```dsh-architecture\n{source}\n```\n")
        self.assertNotIn('id="hubradar-mermaid"', page)
        # Should be lightweight (< 50KB) instead of 3.6MB
        self.assertLess(len(page.encode("utf-8")), 50000)

    def test_readme_four_stage_workflow_stays_lightweight(self):
        source = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?m)^\s*```mermaid\b")
        page = render_markdown(source)
        self.assertNotIn('id="hubradar-mermaid"', page)
        self.assertLess(len(page.encode("utf-8")), 50000)
        for stage in ("领域发现", "证据准备", "Agent 提炼", "核验与交付"):
            self.assertIn(stage, page)

    def test_dsh_invalid_json_schema_and_unknown_labels_show_error_with_source(self):
        for lang in ("dsh", "architecture", "dsh-architecture"):
            for source in ('{"layers":', 'not-a-known-example', '[]', '{}', '<svg onload="bad()"><script>bad()</script></svg>'):
                with self.subTest(lang=lang, source=source):
                    page = render_markdown(f"# 架构\n\n```{lang}\n{source}\n```\n")
                    article = page.split('<article id="report">')[1].split("</article>")[0]
                    self.assertIn('data-diagram-status="error"', article)
                    self.assertIn('<details class="diagram-source" open>', article)
                    self.assertIn('role="alert"', article)
                    self.assertNotIn('<svg', article)
                    self.assertNotIn('Hono', article)
                    self.assertNotIn('HubRadar 核心系统架构', article)
                    self.assertNotIn('data-diagram-status="ready"', article)
                    self.assertIn(source.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'), article)
                    self.assertNotIn('id="hubradar-mermaid"', page)

    def test_dsh_renderer_exception_is_escaped_and_does_not_load_a_fixture(self):
        source = json.dumps({"layers": [{"cards": [{"title": "真实系统"}]}]})
        with patch("hubradar.html_report.generate_dsh_svg", side_effect=RuntimeError('<script>bad()</script>')), \
             patch("hubradar.dsh_architecture.get_example_spec") as fixture:
            page = render_markdown(f"# 架构\n\n```dsh\n{source}\n```\n")
        fixture.assert_not_called()
        self.assertIn('data-diagram-status="error"', page)
        self.assertIn('&lt;script&gt;bad()&lt;/script&gt;', page)
        self.assertNotIn('<script>bad()', page)

    def test_dsh_fences_reject_magic_example_names(self):
        for lang in ("dsh", "architecture", "dsh-architecture"):
            for name in ("hono", "hubradar", "Hono", '"hono"'):
                with self.subTest(lang=lang, name=name), \
                     patch("hubradar.dsh_architecture.get_example_spec") as fixture:
                    page = render_markdown(f"# 架构\n\n```{lang}\n{name}\n```\n")
                    fixture.assert_not_called()
                    self.assertIn('data-diagram-status="error"', page)
                    self.assertNotIn('<svg', page)

    def test_dsh_semantic_json_renders_its_own_system(self):
        source = json.dumps({"title": "独立应用", "layers": [{"cards": [{"id": "app", "title": "应用入口", "code_pill": "run()"}]}]})
        page = render_markdown(f"# 架构\n\n```dsh\n{source}\n```\n")
        article = page.split('<article id="report">')[1].split("</article>")[0]
        self.assertIn('data-diagram-status="ready"', article)
        self.assertIn('独立应用', article)
        self.assertIn('data-card-id="app"', article)
        self.assertNotIn('Benchmark', article)

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
