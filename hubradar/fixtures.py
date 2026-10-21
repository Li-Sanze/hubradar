"""Official, pinned-source Benchmark examples for the DSH compiler."""

from typing import Any, Dict

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
