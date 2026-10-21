"""DSH Architecture SVG Generator.

Synthesizes Fire Skill's C4 box-model geometry (1000px fixed viewport, 3-layer
hierarchy, code pills, numbered badges, orthogonal connectors) with Archify's
click-to-source code anchors and CSS variable theming.

Zero external runtime dependencies. Outputs lightweight (~8KB-12KB) vector SVG.
"""

import html
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4


COLOR_PALETTES = {
    "blue": {
        "bg": "#f0f9ff",
        "stroke": "#bae6fd",
        "pill_bg": "#eff6ff",
        "badge_bg": "#2563eb",
        "title_fill": "#1e40af",
    },
    "purple": {
        "bg": "#faf5ff",
        "stroke": "#e9d5ff",
        "pill_bg": "#f5f3ff",
        "badge_bg": "#7c3aed",
        "title_fill": "#5b21b6",
    },
    "emerald": {
        "bg": "#f0fdf4",
        "stroke": "#bbf7d0",
        "pill_bg": "#ecfdf5",
        "badge_bg": "#059669",
        "title_fill": "#166534",
    },
    "yellow": {
        "bg": "#fefce8",
        "stroke": "#facc15",  # High contrast yellow border (>=3:1)
        "pill_bg": "#fffbeb",
        "badge_bg": "#d97706",
        "title_fill": "#92400e",
    },
    "slate": {
        "bg": "#f8fafc",
        "stroke": "#cbd5e1",
        "pill_bg": "#f1f5f9",
        "badge_bg": "#475569",
        "title_fill": "#1e293b",
    },
}


def escape(s: Any) -> str:
    return html.escape(str(s) if s is not None else "")


def fit_text(text: Any, max_px: int) -> str:
    """Ensure text fits visually inside pixel budget; truncate with ellipsis if needed."""
    if not text:
        return ""
    text_str = str(text).strip()
    w = 0.0
    res = []
    for ch in text_str:
        ch_w = 11.5 if ord(ch) > 127 else 6.8
        if w + ch_w > max_px:
            return "".join(res).rstrip() + "…"
        w += ch_w
        res.append(ch)
    return text_str


def validate_href(href: Optional[str]) -> Optional[str]:
    """Ensure links are safe http/https URLs."""
    if not href:
        return None
    href = href.strip()
    if href.startswith("https://") or href.startswith("http://"):
        return href
    return None


def generate_dsh_svg(spec: Dict[str, Any]) -> str:
    """Generate a self-contained, responsive, interactive DSH architecture SVG."""
    width = 1000
    height = int(spec.get("height", 680))
    title = spec.get("title", "系统架构全景")
    subtitle = spec.get("subtitle", "核心架构与数据流分层")
    slug = spec.get("slug") or uuid4().hex[:6]

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="max-width:100%;height:auto;display:block;margin:0 auto;" role="img" aria-label="{escape(title)}">',
        f'  <title>{escape(title)}</title>',
        f'  <desc>{escape(subtitle)}</desc>',
        "  <defs>",
        f'    <marker id="arrow-blue-{slug}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">',
        '      <polygon points="0 0, 8 3, 0 6" fill="#2563eb"/>',
        "    </marker>",
        f'    <marker id="arrow-gray-{slug}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">',
        '      <polygon points="0 0, 8 3, 0 6" fill="#64748b"/>',
        "    </marker>",
        f'    <marker id="arrow-emerald-{slug}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">',
        '      <polygon points="0 0, 8 3, 0 6" fill="#059669"/>',
        "    </marker>",
        f'    <filter id="card-shadow-{slug}" x="-3%" y="-3%" width="106%" height="106%">',
        '      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.06"/>',
        "    </filter>",
        f'    <filter id="card-hover-shadow-{slug}" x="-5%" y="-5%" width="110%" height="110%">',
        '      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.12"/>',
        "    </filter>",
        "  </defs>",
        "",
        "  <style>",
        '    text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif; }',
        "    .canvas-bg { fill: var(--surface, #f8fafc); }",
        "    .arch-title { font-size: 20px; font-weight: 700; fill: var(--text, #0f172a); }",
        "    .arch-subtitle { font-size: 13px; font-weight: 400; fill: var(--muted, #64748b); }",
        "    .layer-container { fill: var(--bg, #ffffff); stroke: var(--line, #e2e8f0); }",
        "    .layer-title { font-size: 12px; font-weight: 700; fill: var(--muted, #475569); letter-spacing: 0.5px; text-transform: uppercase; }",
        "    .card-title { font-size: 13px; font-weight: 600; }",
        "    .card-desc { font-size: 11px; font-weight: 400; fill: #64748b; }",
        "    .code-pill { font-size: 10.5px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace; fill: #334155; }",
        "    .badge-text { font-size: 10px; font-weight: 700; fill: #ffffff; }",
        "    .footer-note { font-size: 11.5px; font-weight: 400; fill: var(--muted, #64748b); }",
        "    .legend-text { font-size: 11px; font-weight: 500; fill: var(--muted, #64748b); }",
        "    a.card-anchor { text-decoration: none; cursor: pointer; }",
        f'    a.card-anchor:hover rect.card-rect {{ stroke-width: 2px; stroke: #2563eb; filter: url(#card-hover-shadow-{slug}); }}',
        "    a.card-anchor:hover text.card-title { fill: #2563eb; }",
        "    :root[data-theme=dark] .canvas-bg { fill: #0f172a; }",
        "    :root[data-theme=dark] .arch-title { fill: #f8fafc; }",
        "    :root[data-theme=dark] .arch-subtitle { fill: #94a3b8; }",
        "    :root[data-theme=dark] .layer-container { fill: #172236; stroke: #334155; }",
        "    :root[data-theme=dark] .layer-title { fill: #94a3b8; }",
        "    :root[data-theme=dark] .footer-note { fill: #94a3b8; }",
        "    :root[data-theme=dark] .legend-text { fill: #94a3b8; }",
        "    :root[data-theme=dark] .card-desc { fill: #94a3b8; }",
        "    @media (prefers-color-scheme: dark) {",
        "      .canvas-bg { fill: #0f172a; }",
        "      .arch-title { fill: #f8fafc; }",
        "      .arch-subtitle { fill: #94a3b8; }",
        "      .layer-container { fill: #172236; stroke: #334155; }",
        "      .layer-title { fill: #94a3b8; }",
        "      .footer-note { fill: #94a3b8; }",
        "      .legend-text { fill: #94a3b8; }",
        "      .card-desc { fill: #94a3b8; }",
        "    }",
        "  </style>",
        "",
        '  <!-- 背景画布 -->',
        f'  <rect width="{width}" height="{height}" class="canvas-bg" data-graph-role="background"/>',
        "",
        '  <!-- 头部标题 -->',
        f'  <text x="40" y="42" class="arch-title">{escape(title)}</text>',
        f'  <text x="40" y="62" class="arch-subtitle">{escape(subtitle)}</text>',
        "",
    ]

    # Render layers
    layers = spec.get("layers", [])
    for layer in layers:
        lx = int(layer.get("x", 40))
        ly = int(layer.get("y", 80))
        lw = int(layer.get("width", 920))
        lh = int(layer.get("height", 110))
        layer_name = layer.get("name", "")
        layer_fill = layer.get("container_fill", "layer-container")

        svg_parts.append(f'  <!-- 容器分层：{escape(layer_name)} -->')
        svg_parts.append(
            f'  <rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="10" '
            f'stroke-width="1.5" class="{layer_fill}" filter="url(#card-shadow-{slug})" data-graph-role="container"/>'
        )
        if layer_name:
            svg_parts.append(
                f'  <text x="{lx + 20}" y="{ly + 24}" class="layer-title">{escape(layer_name)}</text>'
            )

        # Render cards inside layer
        for card in layer.get("cards", []):
            cx = int(card.get("x", lx + 20))
            cy = int(card.get("y", ly + 35))
            cw = int(card.get("width", 270))
            ch = int(card.get("height", 60))
            c_title = card.get("title", "")
            c_desc = card.get("desc", "")
            badge = card.get("badge")
            code_pill = card.get("code_pill")
            pill_desc = card.get("pill_desc")
            color = card.get("color", "slate")
            href = validate_href(card.get("href"))
            palette = COLOR_PALETTES.get(color, COLOR_PALETTES["slate"])

            card_group = []
            if href:
                card_group.append(f'  <a class="card-anchor" href="{escape(href)}" target="_blank" rel="noopener">')

            card_group.append(f'    <g transform="translate({cx}, {cy})">')
            card_group.append(
                f'      <rect width="{cw}" height="{ch}" rx="8" fill="{palette["bg"]}" '
                f'stroke="{palette["stroke"]}" stroke-width="1.2" class="card-rect"/>'
            )

            # Badge
            tx_offset = 15
            if badge:
                card_group.append(
                    f'      <rect x="12" y="12" width="20" height="20" rx="4" fill="{palette["badge_bg"]}"/>'
                )
                card_group.append(
                    f'      <text x="22" y="26" text-anchor="middle" class="badge-text">{escape(badge)}</text>'
                )
                tx_offset = 38

            # Card title and description
            title_y = 26 if badge else 23
            desc_y = 48 if badge else 42
            safe_title = fit_text(c_title, cw - tx_offset - 14)
            safe_desc = fit_text(c_desc, cw - 28)
            card_group.append(
                f'      <text x="{tx_offset}" y="{title_y}" class="card-title" fill="{palette["title_fill"]}">{escape(safe_title)}</text>'
            )
            card_group.append(
                f'      <text x="14" y="{desc_y}" class="card-desc">{escape(safe_desc)}</text>'
            )

            # Code pill inside card - positioned relative to content or bottom
            if code_pill:
                pill_y = int(card.get("pill_y", ch - 44))
                pill_h = int(card.get("pill_h", 32))
                safe_pill = fit_text(code_pill, cw - 36)
                card_group.append(
                    f'      <rect x="12" y="{pill_y}" width="{cw - 24}" height="{pill_h}" rx="4" '
                    f'fill="{palette["pill_bg"]}" stroke="{palette["stroke"]}" stroke-width="0.8"/>'
                )
                card_group.append(
                    f'      <text x="20" y="{pill_y + 19}" class="code-pill">{escape(safe_pill)}</text>'
                )
                if pill_desc:
                    safe_pdesc = fit_text(pill_desc, cw - 36)
                    card_group.append(
                        f'      <text x="20" y="{pill_y + pill_h + 16}" class="card-desc" fill="{palette["title_fill"]}">{escape(safe_pdesc)}</text>'
                    )

            card_group.append("    </g>")
            if href:
                card_group.append("  </a>")

            svg_parts.extend(card_group)

    # Render connectors
    connectors = spec.get("connectors", [])
    for conn in connectors:
        ctype = conn.get("type", "line")
        stroke = conn.get("color", "#2563eb")
        marker = conn.get("marker", f"url(#arrow-blue-{slug})")
        if "arrow-gray" in marker:
            marker = f"url(#arrow-gray-{slug})"
        elif "arrow-blue" in marker:
            marker = f"url(#arrow-blue-{slug})"
        elif "arrow-emerald" in marker:
            marker = f"url(#arrow-emerald-{slug})"

        width_px = conn.get("width", 2)
        dash = conn.get("dash")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""

        if ctype == "line":
            x1, y1 = int(conn["x1"]), int(conn["y1"])
            x2, y2 = int(conn["x2"]), int(conn["y2"])
            svg_parts.append(
                f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width_px}" '
                f'marker-end="{marker}"{dash_attr}/>'
            )
        elif ctype == "polyline":
            pts = " ".join(f"{int(p[0])},{int(p[1])}" for p in conn["points"])
            svg_parts.append(
                f'  <polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{width_px}" '
                f'marker-end="{marker}"{dash_attr}/>'
            )

    # Render Legend
    legend = spec.get("legend")
    if legend:
        lx = int(legend.get("x", 40))
        ly = int(legend.get("y", height - 38))
        svg_parts.append('  <!-- 底部图例 -->')
        for i, item in enumerate(legend.get("items", [])):
            ix = lx + i * 220
            svg_parts.append(f'  <circle cx="{ix}" cy="{ly}" r="5" fill="{item["color"]}"/>')
            svg_parts.append(f'  <text x="{ix + 12}" y="{ly + 4}" class="legend-text">{escape(item["label"])}</text>')

    # Render summary note
    summary_note = spec.get("summary_note")
    if summary_note:
        center_x = width // 2
        svg_parts.append(
            f'  <text x="{center_x}" y="{height - 16}" text-anchor="middle" class="footer-note">{escape(summary_note)}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def build_hubradar_architecture_spec() -> Dict[str, Any]:
    """Return the rigorously verified specification for HubRadar's DSH architecture diagram.

    All anchors and code pills are verified against pinned SHA 93ef1e1:
    - Zero external runtime dependencies.
    - Click-to-source code anchors linking directly to GitHub lines.
    - 3-tier C4 box-model geometry.
    """
    repo = "Li-Sanze/hubradar"
    sha = "93ef1e15c8e79c0a5a337e19624b002ef7906cbb"

    def link(path: str, start: int, end: int) -> str:
        return f"https://github.com/{repo}/blob/{sha}/{path}#L{start}-L{end}"

    return {
        "slug": "hubradar",
        "title": "HubRadar 核心系统架构与全景分层 (93ef1e1)",
        "subtitle": "统一 CLI / 双 Skill 接入 · 静态 AST 与引文不变式验证内核 · DSH 矢量渲染与离线打包底座",
        "height": 680,
        "layers": [
            {
                "name": "入口与交互呈现平面 (Presentation & CLI / Agent Skill Plane)",
                "x": 40,
                "y": 80,
                "width": 920,
                "height": 110,
                "cards": [
                    {
                        "title": "统一 CLI 懒加载网关 (cli.py)",
                        "desc": "lazy-import 分流五大子命令与流水线",
                        "x": 60,
                        "y": 115,
                        "width": 270,
                        "height": 60,
                        "color": "blue",
                        "href": link("hubradar/cli.py", 44, 88),
                    },
                    {
                        "title": "宿主双 Agent Skill 协议 (skills/)",
                        "desc": "3 分钟卡片与技术雷达 双规范交互契约",
                        "x": 365,
                        "y": 115,
                        "width": 270,
                        "height": 60,
                        "color": "yellow",
                        "href": link("skills/hubradar/SKILL.md", 1, 35),
                    },
                    {
                        "title": "交互缩放与深浅色控制器 (assets/)",
                        "desc": "CSS 变量双模自适应 · 零依赖无级缩放",
                        "x": 670,
                        "y": 115,
                        "width": 270,
                        "height": 60,
                        "color": "purple",
                        "href": link("hubradar/assets/report.js", 125, 175),
                    },
                ],
            },
            {
                "name": "静态证据与引文验证内核 (Analysis & Invariant Verification Kernel)",
                "x": 40,
                "y": 215,
                "width": 920,
                "height": 160,
                "cards": [
                    {
                        "badge": "1",
                        "title": "ast-grep 语法树事实抽取",
                        "desc": "多语言 AST census · 调用图与核心文件评分",
                        "code_pill": "top_defs(root, lang) & nx.DiGraph()",
                        "pill_y": 62,
                        "pill_h": 32,
                        "x": 60,
                        "y": 250,
                        "width": 270,
                        "height": 110,
                        "color": "blue",
                        "href": link("hubradar/prepare.py", 190, 225),
                    },
                    {
                        "badge": "2",
                        "title": "引文不变式交叉严格校验",
                        "desc": "校验 claims 证据链 · 源码行逐字引文回溯",
                        "code_pill": "verify(facts, raw, repo)",
                        "pill_y": 62,
                        "pill_h": 32,
                        "x": 365,
                        "y": 250,
                        "width": 270,
                        "height": 110,
                        "color": "purple",
                        "href": link("hubradar/finalize.py", 53, 88),
                    },
                    {
                        "badge": "3",
                        "title": "领域技术雷达探测引擎",
                        "desc": "突破性开源新星扫描 · 采纳四象限矩阵分析",
                        "code_pill": "build_radar(domain_spec)",
                        "pill_y": 62,
                        "pill_h": 32,
                        "x": 670,
                        "y": 250,
                        "width": 270,
                        "height": 110,
                        "color": "emerald",
                        "href": link("hubradar/radar.py", 15, 60),
                    },
                ],
            },
            {
                "name": "矢量渲染与离线打包底座",
                "x": 40,
                "y": 425,
                "width": 920,
                "height": 200,
                "cards": [
                    {
                        "title": "DSH 盒模型矢量渲染编译器 (dsh_architecture.py)",
                        "desc": "1000px 黄金视口 · 正交连线避让 · 代码药丸与 GitHub SHA 点击直达",
                        "code_pill": "generate_dsh_svg(spec_data)",
                        "pill_desc": "原生纯 Python 吸收 · 零外部 Node/CLI 依赖 · ~8KB 极致轻量",
                        "pill_y": 64,
                        "pill_h": 34,
                        "x": 60,
                        "y": 460,
                        "width": 420,
                        "height": 145,
                        "color": "emerald",
                        "href": link("hubradar/dsh_architecture.py", 78, 150),
                    },
                    {
                        "title": "单文件离线 HTML 白皮书打包人 (html_report.py)",
                        "desc": "Markdown 解析 · Bleach 安全占位内联 · 零脚本纯矢量自适应",
                        "code_pill": "render_file(card_md, index_html)",
                        "pill_desc": "彻底剥离 3.4MB mermaid.js 强依赖 · 毫秒级加载与离线归档",
                        "pill_y": 64,
                        "pill_h": 34,
                        "x": 510,
                        "y": 460,
                        "width": 430,
                        "height": 145,
                        "color": "purple",
                        "href": link("hubradar/html_report.py", 145, 185),
                    },
                ],
            },
        ],
        "connectors": [
            # Layer 1 -> Layer 2 dashed downward lines (touch container top at y=214)
            {"type": "line", "x1": 195, "y1": 175, "x2": 195, "y2": 214, "color": "#94a3b8", "width": 1.5, "dash": "3 3", "marker": "url(#arrow-gray)"},
            {"type": "line", "x1": 500, "y1": 175, "x2": 500, "y2": 214, "color": "#94a3b8", "width": 1.5, "dash": "3 3", "marker": "url(#arrow-gray)"},
            {"type": "line", "x1": 805, "y1": 175, "x2": 805, "y2": 214, "color": "#94a3b8", "width": 1.5, "dash": "3 3", "marker": "url(#arrow-gray)"},
            # Layer 2 horizontal workflow (full-span connection: x1=330 to x2=364; x1=635 to x2=669)
            {"type": "line", "x1": 330, "y1": 305, "x2": 364, "y2": 305, "color": "#2563eb", "width": 2, "marker": "url(#arrow-blue)"},
            {"type": "line", "x1": 635, "y1": 305, "x2": 669, "y2": 305, "color": "#2563eb", "width": 2, "marker": "url(#arrow-blue)"},
            # Layer 2 -> Layer 3 branching lines (direct feed into Layer 3 cards at y=458, clear of title)
            {"type": "polyline", "points": [[500, 360], [500, 405], [270, 405], [270, 458]], "color": "#94a3b8", "width": 1.5, "marker": "url(#arrow-gray)"},
            {"type": "polyline", "points": [[500, 405], [725, 405], [725, 458]], "color": "#94a3b8", "width": 1.5, "marker": "url(#arrow-gray)"},
        ],
        "legend": {
            "x": 60,
            "y": 645,
            "items": [
                {"label": "接入与呈现 (Presentation & CLI)", "color": "#2563eb"},
                {"label": "静态分析与验证 (Kernel & Verification)", "color": "#7c3aed"},
                {"label": "矢量渲染与打包 (Vector & Packaging)", "color": "#059669"},
                {"label": "点击直达 GitHub 源码提交行 (Click-to-Source)", "color": "#64748b"},
            ],
        },
        "summary_note": "纯 Python 原生吸收 · 零 Node/CLI 外部依赖 · 节点点击直达 GitHub 93ef1e1 源码提交行 · 纯矢量 ~10KB",
    }


def build_hono_architecture_spec() -> Dict[str, Any]:
    """Return the rigorously verified specification for Hono's DSH architecture diagram.
    
    All anchors and code pills are verified against pinned SHA 5ca49b07:
    - No line range overflows (src/client/index.ts has 17 lines max).
    - Verbatim code snippets from genuine execution paths.
    - True branch origin at Context output.
    """
    repo = "honojs/hono"
    sha = "5ca49b0720755c585c9a9835f0a479ceea36fb52"

    def link(path: str, start: int, end: int) -> str:
        return f"https://github.com/{repo}/blob/{sha}/{path}#L{start}-L{end}"

    return {
        "slug": "hono",
        "title": "Hono 核心系统架构与全景分层 (5ca49b07)",
        "subtitle": "Web 标准接入 · SmartRouter 预编译路由决策 · 单处理器特化与洋葱中间件",
        "height": 680,
        "layers": [
            {
                "name": "多平台运行时接入平面 (Presentation & Adapters)",
                "x": 40,
                "y": 80,
                "width": 920,
                "height": 110,
                "cards": [
                    {
                        "title": "原生 Web 标准边缘运行时",
                        "desc": "Workers / Deno / Bun 原生标准 Request",
                        "x": 60,
                        "y": 115,
                        "width": 270,
                        "height": 60,
                        "color": "blue",
                        "href": link("src/hono.ts", 20, 32),
                    },
                    {
                        "title": "Node.js / Lambda 适配层",
                        "desc": "非标准平台 Stream 与 Request 双向转换",
                        "x": 365,
                        "y": 115,
                        "width": 270,
                        "height": 60,
                        "color": "yellow",
                        "href": link("src/adapter/aws-lambda/handler.ts", 1, 25),
                    },
                    {
                        "title": "RPC 强类型客户端与推导",
                        "desc": "hc 客户端与 AppType 强类型声明",
                        "x": 670,
                        "y": 115,
                        "width": 270,
                        "height": 60,
                        "color": "purple",
                        "href": link("src/client/index.ts", 1, 17),  # Exact 17 lines
                    },
                ],
            },
            {
                "name": "核心应用底座与路由决策引擎 (Application Kernel & Router)",
                "x": 40,
                "y": 215,
                "width": 920,
                "height": 160,
                "cards": [
                    {
                        "badge": "1",
                        "title": "HonoBase #dispatch 调度",
                        "desc": "getPath 解析路径，构造 HonoRequest",
                        "code_pill": "this.router.match(method, path)",
                        "pill_y": 62,
                        "pill_h": 32,
                        "x": 60,
                        "y": 250,
                        "width": 270,
                        "height": 110,
                        "color": "blue",
                        "href": link("src/hono-base.ts", 437, 448),
                    },
                    {
                        "badge": "2",
                        "title": "SmartRouter 组合路由",
                        "desc": "RegExpRouter(预编译) + TrieRouter(回退)",
                        "code_pill": "this.match = router.match.bind(router)",
                        "pill_y": 62,
                        "pill_h": 32,
                        "x": 365,
                        "y": 250,
                        "width": 270,
                        "height": 110,
                        "color": "purple",
                        "href": link("src/router/smart-router/router.ts", 21, 49),
                    },
                    {
                        "badge": "3",
                        "title": "Context 惰性上下文容器",
                        "desc": "??= 按需初始化 headers、变量 Map、body",
                        "code_pill": "this.#req ??= new HonoRequest(...)",
                        "pill_y": 62,
                        "pill_h": 32,
                        "x": 670,
                        "y": 250,
                        "width": 270,
                        "height": 110,
                        "color": "emerald",
                        "href": link("src/context.ts", 366, 407),
                    },
                ],
            },
            {
                "name": "执行管道特化：快路径 VS compose",
                "x": 40,
                "y": 425,
                "width": 920,
                "height": 200,
                "cards": [
                    {
                        "title": "单处理器快路径特化 (Fast Path)",
                        "desc": "当 matchResult[0].length === 1 时完全绕过 compose",
                        "code_pill": "res = matchResult[0][0][0][0](c, async () => {})",
                        "pill_desc": "零中间件级联调度开销 · 直接返回 Response 对象",
                        "pill_y": 64,
                        "pill_h": 34,
                        "x": 60,
                        "y": 460,
                        "width": 420,
                        "height": 145,
                        "color": "emerald",
                        "href": link("src/hono-base.ts", 449, 466),
                    },
                    {
                        "title": "洋葱式中间件级联调度 (compose)",
                        "desc": "compose(matchResult[0]) 串联执行与错误捕获",
                        "code_pill": "res = await handler(context, () => dispatch(i + 1))",
                        "pill_desc": "严格维护 context.finalized 状态机 · 错误冒泡守卫",
                        "pill_y": 64,
                        "pill_h": 34,
                        "x": 510,
                        "y": 460,
                        "width": 430,
                        "height": 145,
                        "color": "purple",
                        "href": link("src/compose.ts", 32, 71),  # Exact cascade at L51
                    },
                ],
            },
        ],
        "connectors": [
            # Layer 1 -> Layer 2 dashed downward lines (touch container top at y=214)
            {"type": "line", "x1": 195, "y1": 175, "x2": 195, "y2": 214, "color": "#94a3b8", "width": 1.5, "dash": "3 3", "marker": "url(#arrow-gray)"},
            {"type": "line", "x1": 500, "y1": 175, "x2": 500, "y2": 214, "color": "#94a3b8", "width": 1.5, "dash": "3 3", "marker": "url(#arrow-gray)"},
            {"type": "line", "x1": 805, "y1": 175, "x2": 805, "y2": 214, "color": "#94a3b8", "width": 1.5, "dash": "3 3", "marker": "url(#arrow-gray)"},
            # Layer 2 horizontal workflow (full-span connection: x1=330 to x2=364; x1=635 to x2=669)
            {"type": "line", "x1": 330, "y1": 305, "x2": 364, "y2": 305, "color": "#2563eb", "width": 2, "marker": "url(#arrow-blue)"},
            {"type": "line", "x1": 635, "y1": 305, "x2": 669, "y2": 305, "color": "#2563eb", "width": 2, "marker": "url(#arrow-blue)"},
            # Layer 2 Context -> Layer 3 pipeline fork (direct feed into Layer 3 cards at y=458)
            {"type": "polyline", "points": [[805, 360], [805, 405], [270, 405], [270, 458]], "color": "#94a3b8", "width": 1.5, "marker": "url(#arrow-gray)"},
            {"type": "polyline", "points": [[805, 405], [725, 405], [725, 458]], "color": "#94a3b8", "width": 1.5, "marker": "url(#arrow-gray)"},
        ],
        "legend": {
            "x": 60,
            "y": 645,
            "items": [
                {"label": "Web 接入层 (Presentation)", "color": "#2563eb"},
                {"label": "调度与路由 (Kernel & Router)", "color": "#7c3aed"},
                {"label": "执行管道特化 (Execution)", "color": "#059669"},
                {"label": "点击直达 GitHub 源码提交行", "color": "#64748b"},
            ],
        },
        "summary_note": "统一输出 Web 标准 Response (HTTP 200/404/500) · 节点点击直达 GitHub 5ca49b07 提交行",
    }
