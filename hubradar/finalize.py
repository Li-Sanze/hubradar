#!/usr/bin/env python3
"""Finalize stage: validate host-written raw_distill.json against the pinned SHA, then render card.md.

Exit code 0 only when every 源码事实/作者声明 claim has a resolvable anchor with a verbatim quote.
"""
import json, re, subprocess, sys, time
from pathlib import Path

TYPES = {"源码事实", "作者声明", "社区信号", "报告综合", "批判审计"}
NEEDS_ANCHOR = {"源码事实", "作者声明"}
LIMITS = {"abstractions": 5, "dataflow_nodes": 10, "mvp_lines": 120}


def git_show(repo, sha, path):
    r = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=repo, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def validate(raw, facts, repo):
    sha, errors, status = raw["sha"], [], {}
    if raw["sha"] != facts["sha"] or raw["repo"] != facts["repo"]:
        errors.append("报告 repo/SHA 与 prepare 的 facts 不一致")
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", sha):
        raise ValueError("sha 必须为完整 commit ID")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", raw["repo"]):
        raise ValueError("repo 必须为 owner/repo")
    cache = {}
    issue_ok = {f"https://github.com/{raw['repo']}/issues/{n}" for n in facts["signal_index"]["issues"]}
    for c in raw["claims"]:
        cid, problems = c["id"], []
        if cid in status:
            errors.append(f"重复 claim ID: {cid}")
        if c["type"] not in TYPES:
            problems.append(f"未知类型 {c['type']}")
        if c["type"] in NEEDS_ANCHOR and not c.get("anchors"):
            problems.append("缺少锚点")
        for a in c.get("anchors", []):
            if a["path"] not in cache:
                cache[a["path"]] = git_show(repo, sha, a["path"])
            text = cache[a["path"]]
            if text is None:
                problems.append(f"{a['path']} 在 {sha[:8]} 不存在"); continue
            lines = text.splitlines()
            if not (1 <= a["start"] <= a["end"] <= len(lines)) or a["end"] - a["start"] > 80:
                problems.append(f"{a['path']}:L{a['start']}-L{a['end']} 行号越界（文件 {len(lines)} 行）"); continue
            if c["type"] in NEEDS_ANCHOR and not a.get("quote", "").strip():
                problems.append("源码事实/作者声明锚点缺少逐字引文")
            if a.get("quote") and squash(a["quote"]) not in squash("\n".join(lines[a["start"] - 1:a["end"]])):
                problems.append(f"{a['path']}:L{a['start']}-L{a['end']} 引文不在该区间")
        if c["type"] == "社区信号":
            bad = [u for u in c.get("links", []) if u not in issue_ok]
            if not c.get("links"):
                problems.append("社区信号缺少链接")
            if bad:
                problems.append(f"链接不在本次采集的信号中: {bad}")
        status[cid] = problems
        errors += [f"{cid}: {p}" for p in problems]
    ids = set(status)
    refs = [cid for sec in ("abstractions", "patterns", "tradeoffs", "pitfalls", "steal") for it in raw[sec] for cid in it["claim_ids"]]
    refs += [cid for e in raw["dataflow"]["edges"] for cid in e["claim_ids"]] + raw["essence"]["claim_ids"]
    refs += [cid for m in raw["mvp"]["mappings"] for cid in m["claim_ids"]] + [cid for s in raw["state_machines"] for cid in s["claim_ids"]]
    errors += [f"引用了不存在的 claim {r}" for r in sorted(set(refs) - ids)]
    if len(raw["abstractions"]) > LIMITS["abstractions"]:
        errors.append("核心抽象超过 5 个")
    if len(raw["dataflow"]["nodes"]) > LIMITS["dataflow_nodes"]:
        errors.append("数据流节点超过 10 个")
    if len(raw["mvp"]["code"].splitlines()) > LIMITS["mvp_lines"]:
        errors.append("MVP 骨架超过 120 行")
    nodes = [n["id"] for n in raw["dataflow"]["nodes"]]
    if len(set(nodes)) != len(nodes):
        errors.append("数据流节点 ID 重复")
    for edge in raw["dataflow"]["edges"]:
        if edge["from"] not in nodes or edge["to"] not in nodes:
            errors.append("数据流边引用未知节点")
    for machine in raw["state_machines"]:
        if not machine["states"]:
            errors.append("状态机没有状态")
        for transition in machine["transitions"]:
            if transition["from"] not in machine["states"] or transition["to"] not in machine["states"]:
                errors.append("状态迁移引用未知状态")
    for r in raw["reading_route"]:
        if git_show(repo, sha, r["path"]) is None:
            errors.append(f"阅读路线文件不存在: {r['path']}")
    return status, errors


def render(raw, facts, status, errors, timings):
    repo, sha = raw["repo"], raw["sha"]
    claims = {c["id"]: c for c in raw["claims"]}

    def cite(ids):
        out = []
        for cid in ids:
            c = claims.get(cid)
            if not c:
                continue
            mark = "✓" if not status[cid] else "✗"
            if c.get("anchors"):
                a = c["anchors"][0]
                out.append(f"[{c['type']}{mark} {a['path'].split('/')[-1]}#L{a['start']}](https://github.com/{repo}/blob/{sha}/{a['path']}#L{a['start']}-L{a['end']})")
            elif c.get("links"):
                out.append(f"[{c['type']}{mark} #{c['links'][0].rsplit('/', 1)[-1]}]({c['links'][0]})")
            else:
                out.append(f"〔{c['type']}{mark}〕")
        return " ".join(out)

    ok = sum(1 for v in status.values() if not v)
    flow = ["```mermaid", "flowchart LR"]
    flow += [f'  {n["id"]}["{n["label"]}"]' for n in raw["dataflow"]["nodes"]]
    flow += [f'  {e["from"]} -->|{e["label"] or " "}| {e["to"]}' if e["label"] else f'  {e["from"]} --> {e["to"]}' for e in raw["dataflow"]["edges"]]
    flow.append("```")
    sm = []
    for m in raw["state_machines"]:
        if not m["states"]:
            continue
        ids = {s: f"s{i}" for i, s in enumerate(m["states"])}
        sm += [f"**{m['name']}** {cite(m['claim_ids'])}", "```mermaid", "stateDiagram-v2"]
        sm += [f"  {ids[s]} : {s}" for s in m["states"]]
        sm += [f"  [*] --> {ids[m['states'][0]]}"] + [f"  {ids[t['from']]} --> {ids[t['to']]} : {t['on']}" for t in m["transitions"]]
        sm.append("```")
    L = [f"# {repo} @ `{sha[:8]}` · 3 分钟卡片",
         f"> 覆盖：{facts['coverage']['grade']}（源码 {facts['coverage']['src_files']} 文件）· 证据包约 {facts['tokens']['evidence_total']:,} tokens / 全量约 {facts['tokens']['source_full_estimate']:,} · 结论校验 {ok}/{len(status)} 通过",
         "", f"**本质**：{raw['essence']['text']} {cite(raw['essence']['claim_ids'])}",
         "", f"**解决**：{raw['solves']}  ", f"**不解决**：{raw['not_solves']} {cite(raw.get('not_solves_claim_ids', []))}",
         "", "## 核心抽象", "| 抽象 | 职责 | 证据 |", "|---|---|---|"]
    L += [f"| {a['name']} | {a['role']} | {cite(a['claim_ids'])} |" for a in raw["abstractions"]]
    L += ["", "## 主数据流"] + flow + ["", "## 状态机"] + sm
    L += ["", "## 承重模式"] + [f"- **{p['name']}**：{p['why_load_bearing']} {cite(p['claim_ids'])}" for p in raw["patterns"]]
    L += ["", "## 架构权衡"] + [f"- 选了 **{t['choice']}**，放弃 {t['gave_up']}；代价：{t['cost']} {cite(t['claim_ids'])}" for t in raw["tradeoffs"]]
    language = re.sub(r"[^a-zA-Z0-9_+-]", "", raw["mvp"].get("language", "text"))
    L += ["", "## 最小 MVP 骨架", f"<details><summary>教学骨架 · {len(raw['mvp']['code'].splitlines())} 行（展开）</summary>", "",
          f"```{language}", raw["mvp"]["code"].rstrip(), "```", ""]
    L += [f"- 第 {m['lines']} 行 ↔ {cite(m['claim_ids'])}" for m in raw["mvp"]["mappings"]]
    L += ["</details>", "", "## 避坑"] + [f"- {p['text']} {cite(p['claim_ids'])}" for p in raw["pitfalls"]]
    L += ["", "## 可以偷的点"] + [f"- {s['text']} {cite(s['claim_ids'])}" for s in raw["steal"]]
    L += ["", f"## 判断：{raw['verdict']['decision']}", raw["verdict"]["reason"], "", "## 阅读路线"]
    L += [f"{i}. [`{r['path']}`](https://github.com/{repo}/blob/{sha}/{r['path']}) — {r['why']}" for i, r in enumerate(raw["reading_route"], 1)]
    L += ["", "---", f"<sub>由 HubRadar 生成：prepare {timings['prepare_s']}s · 宿主综合 {timings['host_s']}s · finalize {timings['finalize_s']}s。"
          f"✓ 仅表示引用结构/引文校验通过，不证明语义正确或运行测试通过。校验错误 {len(errors)} 条。</sub>"]
    if errors:
        L[1:1] = ["", "> **验证未通过，请勿作为已校验报告使用。**", ""] + [f"- {error}" for error in errors] + [""]
    return "\n".join(L) + "\n"


def main(work, repo, out_dir):
    t0 = time.time()
    work, out = Path(work), Path(out_dir)
    raw = json.loads((work / "raw_distill.json").read_text(encoding="utf-8"))
    facts = json.loads((work / "facts.json").read_text(encoding="utf-8"))
    status, errors = validate(raw, facts, repo)
    host_s = None
    if (work / "host_start.ts").exists() and (work / "host_end.ts").exists():
        host_s = int((work / "host_end.ts").read_text()) - int((work / "host_start.ts").read_text())
    timings = {"prepare_s": facts["timings"]["total_s"], "host_s": host_s, "finalize_s": None}
    timings["finalize_s"] = round(time.time() - t0, 2)
    out.mkdir(parents=True, exist_ok=True)
    (out / "card.md").write_text(render(raw, facts, status, errors, timings), encoding="utf-8")
    report = {"valid": not errors, "claims_total": len(status), "claims_passed": sum(1 for v in status.values() if not v),
              "by_type": {t: sum(1 for c in raw["claims"] if c["type"] == t) for t in TYPES}, "errors": errors, "timings": timings}
    (out / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:4]))
