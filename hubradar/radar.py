#!/usr/bin/env python3
"""Domain radar prototype: search slices -> GraphQL enrich -> star-history velocity -> adoption -> tiers -> radar.md."""
import collections, concurrent.futures as cf, datetime as dt, json, math, re, statistics, subprocess, sys, time, urllib.request
from pathlib import Path

import networkx as nx

NOW = dt.datetime.now(dt.timezone.utc)
SPARK = "▁▂▃▄▅▆▇█"


def gh(args, timeout=60):
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=timeout)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def search(q):
    d = gh(["-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "sort=stars", "-f", "per_page=30"])
    if not isinstance(d, dict) or "items" not in d:
        raise ValueError(f"GitHub 搜索失败（检查 gh 认证/限流）：{q}")
    if d.get("incomplete_results"):
        print(f"警告：GitHub 查询超时，结果可能不完整：{q}", file=sys.stderr)
    return [i["full_name"] for i in (d or {}).get("items", [])], (d or {}).get("total_count", 0)


def enrich(names):
    since = (NOW - dt.timedelta(days=90)).strftime("%Y-%m-%dT00:00:00Z")
    out = {}
    for i in range(0, len(names), 40):
        parts = []
        for j, n in enumerate(names[i:i + 40]):
            o, r = n.split("/", 1)
            parts.append(f'r{j}: repository(owner:"{o}", name:"{r}") {{ nameWithOwner stargazerCount forkCount createdAt pushedAt isArchived '
                         f'licenseInfo{{spdxId}} primaryLanguage{{name}} description repositoryTopics(first:8){{nodes{{topic{{name}}}}}} '
                         f'issues(states:OPEN){{totalCount}} defaultBranchRef{{target{{... on Commit{{history(since:"{since}"){{totalCount}}}}}}}} }}')
        d = gh(["graphql", "-f", "query={" + " ".join(parts) + "}"]) or {}
        for v in (d.get("data") or {}).values():
            if v:
                out[v["nameWithOwner"]] = v
    return out


def star_history(name):
    d = gh(["-H", "X-GitHub-Api-Version: 2026-03-10", f"repos/{name}/stargazers/history?per_page=13"])
    if not isinstance(d, list):
        return None
    days = []
    for wk in d:  # newest week first; days[] starts on Sunday
        start = dt.datetime.fromtimestamp(wk["week"], dt.timezone.utc)
        for k in range(6, -1, -1):
            if start + dt.timedelta(days=k) <= NOW:
                days.append(wk["days"][k])
    return days


def adoption(name):
    url = f"https://packages.ecosyste.ms/api/v1/packages/lookup?repository_url=https://github.com/{name}"
    try:  # curl honours the system proxy/CA setup that urllib missed in the first dogfood run
        pk = json.loads(subprocess.run(["curl", "-s", "--max-time", "40", url], capture_output=True, text=True, timeout=50).stdout)
        return max((p.get("dependent_repos_count") or 0 for p in pk), default=0), sum((p.get("downloads") or 0) for p in pk)
    except Exception:
        return None, None


def spark(vals):
    m = max(vals) or 1
    return "".join(SPARK[min(7, int(v / m * 7.999))] for v in vals)


def main(domain_file, out_dir):
    global NOW
    NOW = dt.datetime.now(dt.timezone.utc)
    T, t0 = {}, time.time()
    dom = json.loads(Path(domain_file).read_text(encoding="utf-8"))
    if not isinstance(dom.get("name"), str) or not isinstance(dom.get("queries"), list):
        raise ValueError("领域配置需要 name 字符串和 queries 列表")
    if not all(isinstance(n, str) and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", n) for n in dom.get("seeds", [])):
        raise ValueError("seed 必须为 GitHub owner/repo")
    names, qlog = list(dom.get("seeds", [])), []
    for q in dom["queries"]:
        found, total = search(q)
        qlog.append((q, total, len(found)))
        names += found
        time.sleep(2.1)  # search API: 30 req/min
    names = list(dict.fromkeys(names))
    T["search_s"] = round(time.time() - t0, 1)
    t1 = time.time()
    meta = enrich(names)
    if not meta:
        raise ValueError("未获得仓库元数据；请检查 gh 认证、网络及领域查询")
    T["graphql_s"] = round(time.time() - t1, 1)
    ranked = sorted(meta.values(), key=lambda v: -v["stargazerCount"])
    young = [v for v in meta.values() if (NOW - dt.datetime.fromisoformat(v["createdAt"].replace("Z", "+00:00"))).days < 180]
    picks = list(dict.fromkeys([v["nameWithOwner"] for v in ranked[:dom.get("history_top", 60)] + young]))[: dom.get("history_cap", 90)]
    t2 = time.time()
    with cf.ThreadPoolExecutor(8) as ex:
        hist = dict(zip(picks, ex.map(star_history, picks)))
    T["star_history_s"] = round(time.time() - t2, 1)
    t3 = time.time()
    adopt_targets = [n for n in picks[:40]]
    with cf.ThreadPoolExecutor(6) as ex:
        adopt = dict(zip(adopt_targets, ex.map(adoption, adopt_targets)))
    T["adoption_s"] = round(time.time() - t3, 1)

    rows = []
    noise = re.compile(dom.get("exclude_desc", "$^"), re.I)
    for n in picks:
        v, days = meta[n], hist.get(n)
        if noise.search(v.get("description") or ""):
            continue
        known_history = bool(days and len(days) >= 28)
        days = days or []
        v7, v28 = (sum(days[:7]), sum(days[:28])) if known_history else (None, None)
        weeks = [sum(days[7 * k:7 * k + 7]) for k in range(1, 9) if len(days) >= 7 * k + 7]
        base = statistics.median(weeks) if weeks else 0
        accel = v7 / max(base, 1) if known_history else None
        age = (NOW - dt.datetime.fromisoformat(v["createdAt"].replace("Z", "+00:00"))).days
        pushed = (NOW - dt.datetime.fromisoformat(v["pushedAt"].replace("Z", "+00:00"))).days
        deps, dl = adopt.get(n, (None, None))
        flags = []
        stars, forks = v["stargazerCount"], v["forkCount"]
        if stars > 5000 and forks / stars < 0.005:
            flags.append("fork/star<0.5%")
        if stars > 5000 and v["issues"]["totalCount"] == 0:
            flags.append("无 open issue")
        if age < 30 and sum(days[:7]) > 0.8 * stars:
            flags.append("7 天内获星>80%")
        commits90 = ((v.get("defaultBranchRef") or {}).get("target") or {}).get("history", {}).get("totalCount", 0)
        if stars > 5000 and commits90 < 5:
            flags.append("90 天提交<5")
        if not v.get("licenseInfo"):
            flags.append("无许可证")
        weekly12 = [sum(days[7 * k:7 * k + 7]) for k in range(11, -1, -1) if len(days) >= 7 * k + 7]
        if not known_history:
            flags.append("趋势未知：历史缺失或不足28天")
        rows.append({"repo": n, "stars": stars, "v7": v7, "v28": v28, "accel": round(accel, 2) if accel is not None else None, "age_d": age, "pushed_d": pushed,
                     "commits90": commits90, "deps": deps, "downloads": dl, "flags": flags, "spark": spark(weekly12) if weekly12 else "-",
                     "lang": (v.get("primaryLanguage") or {}).get("name"), "desc": (v.get("description") or "")[:70],
                     "topics": [t["topic"]["name"] for t in v["repositoryTopics"]["nodes"]], "archived": v["isArchived"]})
    v7s = sorted(r["v7"] for r in rows if r["v7"] is not None)
    p90 = v7s[int(0.9 * (len(v7s) - 1))] if v7s else 0
    v28s = sorted(r["v28"] for r in rows if r["v28"] is not None)
    p75 = v28s[int(0.75 * (len(v28s) - 1))] if v28s else 0
    for r in rows:
        if r["archived"] or r["pushed_d"] > 180:
            r["tier"] = "衰退/沉寂"
        elif r["v7"] is None:
            r["tier"] = "趋势未知"
        elif r["accel"] >= 3 and r["v7"] >= max(200, p90):
            r["tier"] = "爆发"
        elif r["age_d"] < 180 and r["v28"] >= p75:
            r["tier"] = "新星"
        elif (r["deps"] or 0) >= 500 or (r["downloads"] or 0) >= 100000 or (r["age_d"] > 730 and r["stars"] >= 10000 and r["accel"] < 1.5):
            r["tier"] = "基石"
        else:
            r["tier"] = "主流/长尾"
    # topic co-occurrence clusters
    G = nx.Graph()
    for r in rows:
        ts = [t for t in r["topics"] if t not in dom.get("ignore_topics", [])]
        for i, a in enumerate(ts):
            for b in ts[i + 1:]:
                G.add_edge(a, b, weight=G.get_edge_data(a, b, {"weight": 0})["weight"] + 1)
    comms = sorted(nx.community.louvain_communities(G, seed=7), key=len, reverse=True) if G.number_of_edges() else []
    deg = dict(G.degree(weight="weight"))
    T["total_s"] = round(time.time() - t0, 1)

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    order = {"爆发": 0, "新星": 1, "基石": 2, "主流/长尾": 3, "趋势未知": 4, "衰退/沉寂": 5}
    rows.sort(key=lambda r: (order[r["tier"]], -(r["v7"] or 0)))
    hist_ok = sum(1 for n in picks if hist.get(n))
    L = [f"# 领域雷达：{dom['name']}（{NOW:%Y-%m-%d}）",
         f"> 候选 {len(names)} → GraphQL 补全 {len(meta)} → star 曲线 {hist_ok}/{len(picks)} → 入表 {len(rows)}；爆发阈值 v7≥max(200, P90={p90}) 且加速度≥3",
         "", "## 版图（topic 共现聚类，前 6 簇）"]
    for i, c in enumerate(comms[:6], 1):
        top = sorted(c, key=lambda t: -deg.get(t, 0))[:6]
        L.append(f"- 簇 {i}（{len(c)} 个 topic）：{' · '.join(top)}")
    L += ["", "## 分层", "| 层 | 仓库 | ★ | 近7天 | 近28天 | 加速度 | 近12周 | 采用（依赖方/下载代理） | 90天提交 | 标记 | 说明 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        deps = "-" if r["deps"] is None else (f"{r['deps']:,} 依赖方" if r["deps"] else f"{(r['downloads'] or 0):,} 下载（口径未核实）")
        v7 = f"{r['v7']:,}" if r["v7"] is not None else "未知"
        v28 = f"{r['v28']:,}" if r["v28"] is not None else "未知"
        desc = r["desc"].replace("|", "\\|").replace("\n", " ")
        L.append(f"| {r['tier']} | [{r['repo']}](https://github.com/{r['repo']}) | {r['stars']:,} | {v7} | {v28} | {r['accel'] if r['accel'] is not None else '-'} | `{r['spark']}` | {deps} | {r['commits90']} | {'；'.join(r['flags']) or ''} | {desc} |")
    L += ["", "## 数据质量", f"- star 历史：`GET /repos/{{o}}/{{r}}/stargazers/history`（API 版本 2026-03-10），成功 {hist_ok}/{len(picks)}",
          "- 只用聚合信号标记待核验热度；标记不是刷星结论，未知趋势不作为零增长",
          "- 依赖方：ecosyste.ms packages lookup，仅前 40 个候选；未发包的仓库显示“-”",
          "- 未使用：GH Archive / OSS Insight 事件排行 / ClickHouse github_events（2026 年数据缺失）",
          f"- 耗时：{json.dumps(T, ensure_ascii=False)}", "", "## 查询切片"]
    L += [f"- `{q}` → total {t}，取 {k}" for q, t, k in qlog]
    (out / "radar.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "radar.json").write_text(json.dumps({"domain": dom, "observed_at": NOW.isoformat(), "timings": T, "p90_v7": p90, "rows": rows, "queries": qlog}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"timings": T, "candidates": len(names), "enriched": len(meta), "history_ok": hist_ok, "rows": len(rows),
                      "tiers": collections.Counter(r["tier"] for r in rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]))
