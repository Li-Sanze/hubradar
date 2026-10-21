"""Declarative, pinned-source semantic examples for the DSH compiler."""

from typing import Any, Dict


def build_hubradar_architecture_spec() -> Dict[str, Any]:
    """Return semantic layers and edges with source links pinned to 93ef1e1."""
    repo = "Li-Sanze/hubradar"
    sha = "93ef1e15c8e79c0a5a337e19624b002ef7906cbb"

    def link(path: str, start: int, end: int) -> str:
        return f"https://github.com/{repo}/blob/{sha}/{path}#L{start}-L{end}"

    return {
        "slug": "hubradar",
        "title": "HubRadar 核心系统架构与工作流全景 (93ef1e1)",
        "subtitle": "统一 CLI / Agent Skill 双入口 · 双轮分析与验证内核 · 零依赖离线交付",
        "layers": [
            {
                "id": "presentation",
                "name": "使用入口与调度平面 (Presentation & CLI / Agent Skill Plane)",
                "cards": [
                    {
                        "id": "cli",
                        "title": "统一 CLI 懒加载网关 (cli.py)",
                        "desc": "lazy-import 分流五大子命令与完整流水线",
                        "color": "blue",
                        "href": link("hubradar/cli.py", 44, 88),
                    },
                    {
                        "id": "skills",
                        "title": "宿主双 Agent Skill 协议 (skills/)",
                        "desc": "3 分钟卡片与技术雷达 双规范交互契约",
                        "color": "blue",
                        "href": link("skills/hubradar/SKILL.md", 1, 35),
                    },
                ],
            },
            {
                "id": "analysis",
                "name": "双轮分析与验证内核 (Analysis & Invariant Verification Kernel)",
                "cards": [
                    {
                        "badge": "1",
                        "id": "distill",
                        "title": "代码库 3 分钟白皮书流水线",
                        "desc": "ast-grep 证据抽取 ➔ 宿主 Agent 归纳 ➔ 引文校验",
                        "code_pill": "prepare() ➔ Agent ➔ finalize()",
                        "pill_desc": "严格代码引文逐字回溯",
                        "color": "purple",
                        "href": link("hubradar/finalize.py", 53, 88),
                    },
                    {
                        "badge": "2",
                        "id": "radar",
                        "title": "领域开源技术雷达引擎",
                        "desc": "突破性开源新星扫描 · 采纳四象限矩阵分析",
                        "code_pill": "build_radar(domain_spec)",
                        "pill_desc": "零外部 API 依赖极速生成",
                        "color": "purple",
                        "href": link("hubradar/radar.py", 15, 60),
                    },
                ],
            },
            {
                "id": "output",
                "name": "矢量渲染与离线打包底座 (Vector Rendering & Offline Packaging)",
                "cards": [
                    {
                        "id": "svg",
                        "title": "分层矢量架构图编译器 (dsh_architecture.py)",
                        "desc": "纯 Python 零依赖 · 自动网格排版与正交避障连线",
                        "code_pill": "generate_dsh_svg(spec_data)",
                        "pill_desc": "声明式 JSON 编译为 SVG",
                        "color": "emerald",
                        "href": link("hubradar/dsh_architecture.py", 78, 150),
                    },
                    {
                        "id": "html",
                        "title": "零依赖交互式白皮书打包 (html_report.py)",
                        "desc": "单文件离线归档 · 内嵌 CSS/JS 缩放与深浅色控制器",
                        "code_pill": "render_file(card_md, index_html)",
                        "pill_desc": "浏览器极速秒开 · 支持无级缩放",
                        "color": "emerald",
                        "href": link("hubradar/html_report.py", 145, 185),
                    },
                ],
            },
        ],
        "edges": [
            {"from": "cli", "to": "distill"},
            {"from": "cli", "to": "radar"},
            {"from": "skills", "to": "distill"},
            {"from": "skills", "to": "radar"},
            {"from": "distill", "to": "svg"},
            {"from": "distill", "to": "html"},
            {"from": "radar", "to": "html"},
            {"from": "svg", "to": "html"},
        ],
        "legend": {
            "items": [
                {"label": "使用入口 (Presentation & CLI)", "color": "#2563eb"},
                {"label": "双轮分析与验证 (Kernel & Verification)", "color": "#7c3aed"},
                {"label": "矢量渲染与打包 (Vector & Packaging)", "color": "#059669"},
                {"label": "点击直达 GitHub 源码提交行 (Click-to-Source)", "color": "#64748b"},
            ],
        },
        "summary_note": "Python 标准库原生编译 SVG · 实线箭头表示核心数据流动 · 点击直达固定提交 93ef1e1 源码行",
    }


def build_hono_architecture_spec() -> Dict[str, Any]:
    """Return semantic layers and edges with source links pinned to 5ca49b07."""
    repo = "honojs/hono"
    sha = "5ca49b0720755c585c9a9835f0a479ceea36fb52"

    def link(path: str, start: int, end: int) -> str:
        return f"https://github.com/{repo}/blob/{sha}/{path}#L{start}-L{end}"

    return {
        "slug": "hono",
        "title": "Hono 核心系统架构与全景分层 (5ca49b07)",
        "subtitle": "Web 标准接入 · SmartRouter 预编译路由决策 · 单处理器特化与洋葱中间件",
        "layers": [
            {
                "id": "adapters",
                "name": "多平台运行时接入平面 (Presentation & Adapters)",
                "cards": [
                    {
                        "id": "web",
                        "title": "原生 Web 标准边缘运行时",
                        "desc": "Workers / Deno / Bun 原生标准 Request",
                        "color": "blue",
                        "href": link("src/hono.ts", 20, 32),
                    },
                    {
                        "id": "adapters",
                        "title": "Node.js / Lambda 适配层",
                        "desc": "非标准平台 Stream 与 Request 双向转换",
                        "color": "yellow",
                        "href": link("src/adapter/aws-lambda/handler.ts", 1, 25),
                    },
                    {
                        "id": "rpc",
                        "title": "RPC 强类型客户端与推导",
                        "desc": "hc 客户端与 AppType 强类型声明",
                        "color": "purple",
                        "href": link("src/client/index.ts", 1, 17),  # Exact 17 lines
                    },
                ],
            },
            {
                "id": "kernel",
                "name": "核心应用底座与路由决策引擎 (Application Kernel & Router)",
                "cards": [
                    {
                        "badge": "1",
                        "id": "dispatch",
                        "title": "HonoBase #dispatch 调度",
                        "desc": "getPath 解析路径，构造 HonoRequest",
                        "code_pill": "this.router.match(method, path)",
                        "color": "blue",
                        "href": link("src/hono-base.ts", 437, 448),
                    },
                    {
                        "badge": "2",
                        "id": "router",
                        "title": "SmartRouter 组合路由",
                        "desc": "RegExpRouter(预编译) + TrieRouter(回退)",
                        "code_pill": "this.match = router.match.bind(router)",
                        "color": "purple",
                        "href": link("src/router/smart-router/router.ts", 21, 49),
                    },
                    {
                        "badge": "3",
                        "id": "context",
                        "title": "Context 惰性上下文容器",
                        "desc": "??= 按需初始化 headers、变量 Map、body",
                        "code_pill": "this.#req ??= new HonoRequest(...)",
                        "color": "emerald",
                        "href": link("src/context.ts", 366, 407),
                    },
                ],
            },
            {
                "id": "execution",
                "name": "执行管道特化：快路径 VS compose",
                "cards": [
                    {
                        "id": "fast-path",
                        "title": "单处理器快路径特化 (Fast Path)",
                        "desc": "当 matchResult[0].length === 1 时完全绕过 compose",
                        "code_pill": "res = matchResult[0][0][0][0](c, async () => {})",
                        "pill_desc": "零中间件级联调度开销 · 直接返回 Response 对象",
                        "color": "emerald",
                        "href": link("src/hono-base.ts", 449, 466),
                    },
                    {
                        "id": "compose",
                        "title": "洋葱式中间件级联调度 (compose)",
                        "desc": "compose(matchResult[0]) 串联执行与错误捕获",
                        "code_pill": "res = await handler(context, () => dispatch(i + 1))",
                        "pill_desc": "严格维护 context.finalized 状态机 · 错误冒泡守卫",
                        "color": "purple",
                        "href": link("src/compose.ts", 32, 71),  # Exact cascade at L51
                    },
                ],
            },
        ],
        "edges": [
            {"from": "web", "to": "dispatch", "style": "dashed"},
            {"from": "adapters", "to": "dispatch", "style": "dashed"},
            {"from": "rpc", "to": "dispatch", "style": "dashed"},
            {"from": "dispatch", "to": "router"},
            {"from": "router", "to": "context"},
            {"from": "context", "to": "fast-path"},
            {"from": "context", "to": "compose"},
        ],
        "legend": {
            "items": [
                {"label": "Web 接入层 (Presentation)", "color": "#2563eb"},
                {"label": "调度与路由 (Kernel & Router)", "color": "#7c3aed"},
                {"label": "执行管道特化 (Execution)", "color": "#059669"},
                {"label": "点击直达 GitHub 源码提交行", "color": "#64748b"},
            ],
        },
        "summary_note": "统一输出 Web 标准 Response (HTTP 200/404/500) · 节点点击直达 GitHub 5ca49b07 提交行",
    }
