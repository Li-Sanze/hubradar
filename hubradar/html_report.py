"""Render Markdown with bundled DSH and Mermaid engines as one offline whitepaper."""

import html
import json
import re
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

import bleach
from markdown_it import MarkdownIt

from .dsh_architecture import generate_dsh_svg, get_example_spec


def render_markdown(markdown, *, title=None):
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    tokens = md.parse(markdown)
    title_token = next((tokens[i + 1] for i, t in enumerate(tokens[:-1]) if t.type == "heading_open" and t.tag == "h1"), None)
    page_title = title or (title_token.content if title_token else "HubRadar 报告")
    # Plain-text title; inline markup is rendered in the document, never in <head>.
    plain_title = html.unescape(bleach.clean(md.renderInline(page_title), tags=[], strip=True))
    sections = []
    section_index = 0
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2":
            section_index += 1
            anchor = f"section-{section_index}"
            token.attrSet("id", anchor)
            sections.append((anchor, tokens[i + 1].content))
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h1":
            del tokens[i:i + 3]
            break

    diagrams = {}
    original_fence = md.renderer.rules["fence"]

    def fence(items, index, options, env):
        token = items[index]
        lang = token.info.strip().lower()
        if lang not in ("mermaid", "dsh", "architecture", "dsh-architecture"):
            return original_fence(items, index, options, env)

        if lang in ("dsh", "architecture", "dsh-architecture"):
            key = f"HUBRADARDSH{uuid4().hex}"
            content = token.content.strip()
            tag = content.lower()
            try:
                spec = get_example_spec(tag) if tag in ("hubradar", "hono") else json.loads(content)
                svg_markup = generate_dsh_svg(spec)
                label = f"DSH Benchmark 样例 · {tag}" if tag in ("hubradar", "hono") else "DSH 盒模型 · 架构全景 (可点击代码锚点)"
                markup = (
                    '<div class="diagram-card dsh-architecture" data-diagram-status="ready">'
                    f'<div class="diagram-bar"><span class="diagram-status" role="status">{label}</span>'
                    '<div class="diagram-controls">'
                    '<button type="button" data-zoom="-0.2" aria-label="缩小图形">−</button>'
                    '<button type="button" data-zoom="0" aria-label="适应容器">适应</button>'
                    '<button type="button" data-zoom="0.2" aria-label="放大图形">＋</button>'
                    '</div></div>'
                    '<div class="diagram-scroll" tabindex="0" aria-label="可缩放的 DSH 架构全景图">'
                    f'<div class="dsh-svg-target">{svg_markup}</div>'
                    '</div></div>'
                )
            except Exception as exc:
                # A failed diagram must remain a visible failure, with its own
                # source. Never substitute a diagram about a different system.
                markup = (
                    '<div class="diagram-card dsh-architecture" data-diagram-status="error">'
                    '<div class="diagram-bar"><span class="diagram-status" role="status">⚠ DSH 图形未生成，已保留源码</span></div>'
                    f'<div class="diagram-scroll"><p class="diagram-error" role="alert">DSH：{html.escape(str(exc)[:300])}</p></div>'
                    '<details class="diagram-source" open><summary>查看 DSH 原文</summary>'
                    f'<pre><code>{html.escape(token.content)}</code></pre></details></div>'
                )
            diagrams[key] = {"is_mermaid": False, "html": markup}
            return f"<p>{key}</p>"

        # Mermaid handling
        key = f"HUBRADARGRAPH{uuid4().hex}"
        diagrams[key] = {
            "is_mermaid": True,
            "html": (
                '<div class="diagram-card" data-diagram-status="pending">'
                '<div class="diagram-bar"><span class="diagram-status" role="status">正在排版…</span>'
                '<div class="diagram-controls"><label>布局 <select class="diagram-layout" aria-label="图形布局">'
                '<option value="auto">自动适配</option><option value="original">原始方向</option>'
                '</select></label><button type="button" data-zoom="-0.2" aria-label="缩小图形">−</button>'
                '<button type="button" data-zoom="0" aria-label="适应容器">适应</button>'
                '<button type="button" data-zoom="0.2" aria-label="放大图形">＋</button></div></div>'
                '<div class="diagram-scroll" tabindex="0" aria-label="可缩放的 Mermaid 图">'
                '<div class="mermaid-target" aria-busy="true"></div></div>'
                '<noscript><p>请启用 JavaScript 使用内置 Mermaid 排版；源码仍可阅读。</p></noscript>'
                f'<details class="diagram-source"><summary>查看 Mermaid 源码</summary><pre><code class="language-mermaid">{html.escape(token.content)}</code></pre></details></div>'
            ),
        }
        return f"<p>{key}</p>"

    md.renderer.rules["fence"] = fence
    rendered = md.renderer.render(tokens, md.options, {})
    tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "strong", "em", "s", "code", "pre",
            "blockquote", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td", "hr",
            "br", "details", "summary", "sub", "sup"}
    rendered = bleach.clean(
        rendered, tags=tags,
        attributes={"a": ["href", "title"], "code": ["class"], "h2": ["id"], "ol": ["start"],
                    "th": ["align"], "td": ["align"], "details": ["open"]},
        protocols={"https", "http", "mailto"}, strip=True,
    )
    for key, diagram_info in diagrams.items():
        rendered = rendered.replace(f"<p>{key}</p>", diagram_info["html"])
    toc = "".join(
        f'<a href="#{anchor}"><span>{index:02d}</span>{html.escape(label)}</a>'
        for index, (anchor, label) in enumerate(sections, 1)
    )
    css = files("hubradar").joinpath("assets/report.css").read_text(encoding="utf-8")
    js = files("hubradar").joinpath("assets/report.js").read_text(encoding="utf-8")
    mermaid_script = ""
    has_mermaid = any(d["is_mermaid"] for d in diagrams.values())
    if has_mermaid:
        vendor = files("hubradar").joinpath("assets/vendor/mermaid.min.js").read_text(encoding="utf-8")
        license_text = files("hubradar").joinpath("assets/vendor/MERMAID-LICENSE.txt").read_text(encoding="utf-8")
        # Preserve the vendored file verbatim on disk, but protect the HTML raw-text
        # boundary if a future build contains this sequence in a string or comment.
        vendor = re.sub(r"</script", r"<\\/script", vendor, flags=re.IGNORECASE)
        safe_license = license_text.replace("*/", "* /")
        mermaid_script = f'<script id="hubradar-mermaid">/* Mermaid 11.17.2 — bundled for offline use.\n{safe_license} */\n{vendor}</script>'
    kind = "领域雷达" if "雷达" in plain_title else "仓库蒸馏"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<meta name="color-scheme" content="light dark"><title>{html.escape(plain_title)} · HubRadar</title>
<style>{css}</style></head><body>
<a href="#report" class="skip-link">跳到报告正文</a><div class="reading-progress" aria-hidden="true"></div>
<div class="shell"><header class="masthead"><a class="brand" href="#top">◎ HubRadar</a>
<div class="actions"><button id="theme" type="button" aria-pressed="false">深色模式</button>
<button id="expand" type="button" aria-pressed="false">展开详情</button><button id="print" type="button">打印 / PDF</button></div></header>
<main id="top"><div class="badge-bar"><span class="badge blue">{kind}</span><span class="badge purple">源码 · 结构 · 取舍</span><span class="badge">离线阅读</span></div>
<h1>{html.escape(plain_title)}</h1>
<nav class="toc-card" aria-label="报告目录"><div class="toc-top"><strong>阅读导航</strong><span>{len(sections):02d} 个章节</span></div><div class="toc-grid">{toc}</div></nav>
<div class="filter-bar" hidden><label for="table-search">筛选仓库</label><input id="table-search" type="search" placeholder="仓库、分层、关键词…" autocomplete="off"><output id="row-count" aria-live="polite"></output></div>
<article id="report">{rendered}</article></main>
<footer>HubRadar · 带着证据理解代码。引用校验不替代语义复核或运行测试。<a href="#top">回到顶部 ↑</a></footer></div>
<div id="notice" class="sr-only" aria-live="polite"></div>
{mermaid_script}
<script id="hubradar-interactions">{js}</script></body></html>"""


def render_file(markdown_path, out_path=None, *, title=None):
    source = Path(markdown_path)
    output = Path(out_path) if out_path else source.with_name("index.html")
    if output.resolve() == source.resolve():
        raise ValueError("HTML 输出不能覆盖 Markdown 输入")
    document = render_markdown(source.read_text(encoding="utf-8"), title=title)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return output
