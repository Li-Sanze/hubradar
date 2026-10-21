"""DSH Architecture SVG Generator.

Compiles semantic layers/cards/edges into layered vector box-model geometry
(1000px viewport, code pills, numbered badges, orthogonal connectors) with
Archify's click-to-source anchors and CSS variable theming.

Zero external runtime dependencies. Explicit legacy geometry is preserved.
"""

import html
import hashlib
import json
import math
import re
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, Optional

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


def fit_text(text: Any, max_px: float, font_size: float = 11.5, *, preserve_tokens: bool = False) -> str:
    """Ensure text fits visually inside pixel budget; truncate with ellipsis if needed."""
    if not text:
        return ""
    text_str = str(text).strip()
    units = re.findall(r"\w+|\s+|[^\w\s]", text_str) if preserve_tokens else text_str
    widths = [sum(font_size if ord(ch) > 127 else font_size * 0.6 for ch in unit) for unit in units]
    if sum(widths) <= max_px:
        return text_str
    w = 0.0
    res = []
    for unit, ch_w in zip(units, widths):
        if w + ch_w > max_px - font_size:
            return "".join(res).rstrip() + "…"
        w += ch_w
        res.append(unit)
    return text_str


def validate_href(href: Optional[str]) -> Optional[str]:
    """Ensure links are safe http/https URLs."""
    if not href:
        return None
    if not isinstance(href, str):
        raise ValueError("Card href must be an HTTP(S) URL string")
    href = href.strip()
    if href.startswith("https://") or href.startswith("http://"):
        return href
    return None


def get_example_spec(name: str) -> Dict[str, Any]:
    """Load an explicitly named Benchmark, never a fallback for invalid input."""
    from .fixtures import build_hono_architecture_spec, build_hubradar_architecture_spec

    builders = {"hono": build_hono_architecture_spec, "hubradar": build_hubradar_architecture_spec}
    if name not in builders:
        raise ValueError(f"Unknown DSH example: {name!r}; choose hubradar or hono")
    spec = builders[name]()
    spec["subtitle"] = "Benchmark 样例 · " + spec["subtitle"]
    return spec


def _number(value: Any, field: str, minimum: float = 0) -> Any:
    """Normalize geometry and reject NaN, infinity, booleans and negative sizes."""
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number >= {minimum}")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{field} must be a finite number >= {minimum}")
    return int(number) if number.is_integer() else number


def compile_dsh_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Compile semantic layers/cards/edges without mutating the caller's spec.

    Supports 1–4 layers of 1–4 cards; four wrap to 2×2. Explicit geometry is preserved.
    Edge order fixes routing. Edges become connectors, keeping compilation idempotent.
    """
    if not isinstance(spec, dict):
        raise ValueError("DSH spec must be a JSON object")
    result = deepcopy(spec)
    layers = result.get("layers")
    if not isinstance(layers, list) or not 1 <= len(layers) <= 4:
        raise ValueError("DSH spec requires 1–4 layers")
    edges = result.get("edges", [])
    if not isinstance(edges, list):
        raise ValueError("edges must be an array")
    owners, layer_ids = {}, set()
    for li, layer in enumerate(layers):
        if not isinstance(layer, dict) or not isinstance(layer.get("cards"), list) or not 1 <= len(layer["cards"]) <= 4:
            raise ValueError("Each layer requires 1–4 cards")
        layer_id = layer.setdefault("id", f"layer-{li}")
        if not isinstance(layer_id, str) or not layer_id or layer_id in layer_ids:
            raise ValueError(f"Invalid or duplicate layer id: {layer_id!r}")
        layer_ids.add(layer_id)
        for ci, card in enumerate(layer["cards"]):
            if not isinstance(card, dict):
                raise ValueError("Each card must be an object")
            cid = card.setdefault("id", f"card-{li}-{ci}")
            if not isinstance(cid, str) or not cid or cid in owners:
                raise ValueError(f"Invalid or duplicate card id: {cid!r}")
            owners[cid] = li
            if card.get("color", "slate") not in COLOR_PALETTES:
                raise ValueError(f"Unknown card color: {card['color']!r}")
    # Reserve independent lanes in every boundary crossed by an edge.
    lanes = {i: {} for i in range(len(layers) - 1)}
    for ei, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError("Each edge must be an object with from/to card IDs")
        for endpoint in ("from", "to"):
            if not isinstance(edge.get(endpoint), str) or edge[endpoint] not in owners:
                raise ValueError(f"Unknown edge {endpoint} card: {edge.get(endpoint)!r}")
        if edge["from"] == edge["to"]:
            raise ValueError("Self edges are not supported")
        if edge.get("style", "solid") not in ("solid", "dashed"):
            raise ValueError("Edge style must be solid or dashed")
        low, high = sorted((owners[edge["from"]], owners[edge["to"]]))
        for boundary in range(low, high):
            lanes[boundary][ei] = len(lanes[boundary])
    gutters = {i: max(48, 16 + 8 * len(group)) for i, group in lanes.items()}
    cursor, bottom, card_index = 80, 80, {}
    for li, layer in enumerate(layers):
        lx = layer["x"] = _number(layer.get("x", 40), "layer.x")
        ly = layer["y"] = _number(layer.get("y", cursor), "layer.y")
        lw = layer["width"] = _number(layer.get("width", 920), "layer.width", 1)
        cards = layer["cards"]
        columns = 2 if len(cards) == 4 else len(cards)
        cw = min({1: 840, 2: 410, 3: 270}[columns], (lw - 40 - 20 * (columns - 1)) / columns)
        if cw < 60 and any("width" not in card for card in cards):
            raise ValueError("Layer is too narrow for its cards")
        row_y = ly + 40
        for start in range(0, len(cards), columns):
            row = cards[start:start + columns]
            row_width = len(row) * cw + (len(row) - 1) * 20
            row_x, row_bottom = lx + (lw - row_width) / 2, row_y
            for ci, card in enumerate(row):
                desc_y = 48 if card.get("badge") else 42
                required_height = desc_y + 16
                if card.get("code_pill"):
                    card["pill_y"] = _number(card.get("pill_y", desc_y + 14), "pill_y", desc_y + 12)
                    card["pill_h"] = _number(card.get("pill_h", 32), "pill_h", 24)
                    required_height = card["pill_y"] + card["pill_h"] + (32 if card.get("pill_desc") else 16)
                default_height = max(110 if card.get("code_pill") else 65, required_height)
                for key, default in (("x", row_x + ci * (cw + 20)), ("y", row_y),
                                     ("width", cw), ("height", default_height)):
                    minimum = 1 if key in ("width", "height") else 0
                    card[key] = _number(card.get(key, default), f"card.{key}", minimum)
                x, y, w, h = (card[k] for k in ("x", "y", "width", "height"))
                card_index[card["id"]] = {
                    "x": x, "y": y, "w": w, "h": h, "center_x": x + w / 2,
                    "center_y": y + h / 2, "top": y, "bottom": y + h,
                    "left": x, "right": x + w, "layer": li, "row": start // columns,
                }
                row_bottom = max(row_bottom, y + h)
            row_y = row_bottom + 20
        lh = layer["height"] = _number(layer.get("height", row_y - ly), "layer.height", 1)
        bottom = max(bottom, ly + lh, row_y)
        cursor = bottom + gutters.get(li, 48)
    result["height"] = max(_number(result.get("height", 0), "height"), bottom + 55)
    if result.get("legend") and "y" in result["legend"]:
        result["height"] = max(result["height"], _number(result["legend"]["y"], "legend.y") + 35)

    def lane_y(boundary: int, edge_index: int) -> float:
        upper, lower = layers[boundary], layers[boundary + 1]
        top = upper["y"] + upper["height"]
        gap = lower["y"] - top
        if gap <= 0:
            raise ValueError("Connected layers require a positive routing gutter")
        group = lanes[boundary]
        return top + gap * (group[edge_index] + 1) / (len(group) + 1)

    def port_to_lane(node: dict, lane: float, downward: bool, custom_x: float = None) -> list:
        """Leave a wrapped row through its side margin if another card blocks it."""
        x = custom_x if custom_x is not None else node["center_x"]
        y = node["bottom"] if downward else node["top"]
        peers = [c for c in card_index.values() if c is not node and c["layer"] == node["layer"]]
        blocked = any(c["left"] < x < c["right"] and c["top"] < max(y, lane)
                      and c["bottom"] > min(y, lane) for c in peers)
        if not blocked:
            return [[x, y], [x, lane]]
        row = [c for c in peers if c["row"] == node["row"]] + [node]
        bend = max(c["bottom"] for c in row) + 10 if downward else min(c["top"] for c in row) - 10
        layer = layers[node["layer"]]
        side = layer["x"] + (10 if x < layer["x"] + layer["width"] / 2 else layer["width"] - 10)
        return [[x, y], [x, bend], [side, bend], [side, lane]]

    inter_out = defaultdict(list)
    inter_in = defaultdict(list)
    for ei, edge in enumerate(edges):
        src, dst = card_index[edge["from"]], card_index[edge["to"]]
        if src["layer"] != dst["layer"]:
            inter_out[edge["from"]].append((dst["center_x"], ei))
            inter_in[edge["to"]].append((src["center_x"], ei))

    edge_exit_x = {}
    for cid, items in inter_out.items():
        node = card_index[cid]
        items.sort(key=lambda t: t[0])
        count = len(items)
        for rank, (_, ei) in enumerate(items):
            offset = -18 if count > 1 and rank == 0 else (18 if count > 1 and rank == count - 1 else 0)
            edge_exit_x[ei] = node["left"] + node["w"] * (rank + 1) / (count + 1) + offset

    edge_entry_x = {}
    for cid, items in inter_in.items():
        node = card_index[cid]
        items.sort(key=lambda t: t[0])
        count = len(items)
        for rank, (_, ei) in enumerate(items):
            offset = 18 if count > 1 and rank == 0 else (-18 if count > 1 and rank == count - 1 else 0)
            edge_entry_x[ei] = node["left"] + node["w"] * (rank + 1) / (count + 1) + offset

    connectors = result.setdefault("connectors", [])
    if not isinstance(connectors, list):
        raise ValueError("connectors must be an array")
    if not all(isinstance(conn, dict) for conn in connectors):
        raise ValueError("Each connector must be an object")
    for ei, edge in enumerate(edges):
        source, target = (card_index[edge[k]] for k in ("from", "to"))
        si, ti = source["layer"], target["layer"]
        if si == ti:
            x1, y1, x2, y2 = source["right"], source["center_y"], target["left"], target["center_y"]
            if source["row"] == target["row"]:
                if source["center_x"] > target["center_x"]:
                    x1, x2 = source["left"], target["right"]
                mid = (x1 + x2) / 2
                points = [[x1, y1], [mid, y1], [mid, y2], [x2, y2]]
            else:
                upper, lower = sorted((source, target), key=lambda c: c["top"])
                mid = (upper["bottom"] + lower["top"]) / 2
                points = [[x1, y1], [x1 + 10, y1], [x1 + 10, mid],
                          [x2 - 10, mid], [x2 - 10, y2], [x2, y2]]
        else:
            down = si < ti
            exit_lane = lane_y(si if down else si - 1, ei)
            entry_lane = lane_y(ti - 1 if down else ti, ei)
            exit_x = edge_exit_x.get(ei, source["center_x"])
            entry_x = edge_entry_x.get(ei, target["center_x"])
            points = port_to_lane(source, exit_lane, down, exit_x)
            target_points = list(reversed(port_to_lane(target, entry_lane, not down, entry_x)))
            if abs(si - ti) > 1:
                # Skip intermediate layers via the outer margin, not their cards.
                side = 20 if source["center_x"] < 500 else 980
                points.extend([[side, exit_lane], [side, entry_lane]])
            points.extend(target_points)
        connectors.append({"type": "polyline", "points": points, "color": edge.get("color", "#94a3b8"),
                           "dash": "5 4" if edge.get("style") == "dashed" else None,
                           "marker": "url(#arrow-gray)", "from": edge["from"], "to": edge["to"]})
    result["card_index"] = card_index
    result.pop("edges", None)
    return result


def generate_dsh_svg(spec: Dict[str, Any]) -> str:
    """Generate a self-contained, responsive, interactive DSH architecture SVG."""
    spec = compile_dsh_spec(spec)
    width = 1000
    height = spec["height"]
    title = spec.get("title", "系统架构全景")
    subtitle = spec.get("subtitle", "核心架构与数据流分层")
    slug = spec.get("slug") or hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", str(slug)) or "dsh"

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
        lx, ly, lw, lh = (layer[k] for k in ("x", "y", "width", "height"))
        layer_name = layer.get("name", "")
        layer_fill = layer.get("container_fill", "layer-container")

        svg_parts.append(
            f'  <rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="10" '
            f'stroke-width="1.5" class="{escape(layer_fill)}" filter="url(#card-shadow-{slug})" data-graph-role="container" data-layer-id="{escape(layer["id"])}"/>'
        )
        if layer_name:
            svg_parts.append(
                f'  <text x="{lx + 20}" y="{ly + 24}" class="layer-title">{escape(layer_name)}</text>'
            )

        # Render cards inside layer
        for card in layer.get("cards", []):
            cx, cy, cw, ch = (card[k] for k in ("x", "y", "width", "height"))
            c_title = card.get("title", "")
            c_desc = card.get("desc", "")
            badge = card.get("badge")
            code_pill = card.get("code_pill")
            pill_desc = card.get("pill_desc")
            color = card.get("color", "slate")
            href = validate_href(card.get("href"))
            palette = COLOR_PALETTES[color]

            card_group = []
            if href:
                card_group.append(f'  <a class="card-anchor" href="{escape(href)}" target="_blank" rel="noopener">')

            card_group.append(f'    <g transform="translate({cx}, {cy})" data-card-id="{escape(card["id"])}">')
            card_group.append(
                f'      <title>{escape(c_title)} - {escape(c_desc)}{": " + escape(code_pill) if code_pill else ""}</title>'
            )
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
            safe_title = fit_text(c_title, cw - tx_offset - 14, 13)
            safe_desc = fit_text(c_desc, cw - 28)
            card_group.append(
                f'      <text x="{tx_offset}" y="{title_y}" class="card-title" fill="{palette["title_fill"]}">{escape(safe_title)}</text>'
            )
            card_group.append(
                f'      <text x="14" y="{desc_y}" class="card-desc">{escape(safe_desc)}</text>'
            )

            # Code pill inside card - positioned relative to content or bottom
            if code_pill:
                pill_y, pill_h = card["pill_y"], card["pill_h"]
                safe_pill = fit_text(code_pill, cw - 36, 10.5, preserve_tokens=True)
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
        marker = conn.get("marker", "url(#arrow-blue)")
        match = re.fullmatch(r"url\(#arrow-(blue|gray|emerald)(?:-[a-zA-Z0-9_-]+)?\)", str(marker))
        if not match:
            raise ValueError("Connector marker must reference an internal DSH arrow")
        marker = f"url(#arrow-{match.group(1)}-{slug})"

        width_px = _number(conn.get("width", 2), "connector.width", 0.1)
        dash = conn.get("dash")
        dash_attr = f' stroke-dasharray="{escape(dash)}"' if dash else ""
        stroke = escape(stroke)
        edge_attr = (f' data-edge-from="{escape(conn["from"])}" data-edge-to="{escape(conn["to"])}"'
                     if "from" in conn and "to" in conn else "")

        if ctype == "line":
            x1, y1 = (_number(conn[k], k) for k in ("x1", "y1"))
            x2, y2 = (_number(conn[k], k) for k in ("x2", "y2"))
            svg_parts.append(
                f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width_px}" '
                f'marker-end="{marker}"{dash_attr}{edge_attr}/>'
            )
        elif ctype == "polyline":
            if not isinstance(conn.get("points"), list) or len(conn["points"]) < 2 or not all(
                isinstance(p, (list, tuple)) and len(p) == 2 for p in conn["points"]
            ):
                raise ValueError("Polyline points must contain at least two [x, y] pairs")
            pts = " ".join(f'{_number(p[0], "point.x")},{_number(p[1], "point.y")}' for p in conn["points"])
            svg_parts.append(
                f'  <polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{width_px}" '
                f'marker-end="{marker}"{dash_attr}{edge_attr}/>'
            )
        else:
            raise ValueError(f"Unsupported connector type: {ctype!r}")

    # Render Legend
    legend = spec.get("legend")
    if legend:
        if not isinstance(legend, dict) or not isinstance(legend.get("items", []), list):
            raise ValueError("Legend must be an object with an items array")
        lx = int(legend.get("x", 40))
        ly = int(legend.get("y", height - 38))
        svg_parts.append('  <!-- 底部图例 -->')
        for i, item in enumerate(legend.get("items", [])):
            if not isinstance(item, dict):
                raise ValueError("Each legend item must be an object")
            ix = lx + i * 220
            svg_parts.append(f'  <circle cx="{ix}" cy="{ly}" r="5" fill="{escape(item["color"])}"/>')
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
