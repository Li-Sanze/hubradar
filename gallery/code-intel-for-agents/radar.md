# 领域雷达：给 AI/Agent 用的代码理解工具（2026-10-20）
> 候选 111 → GraphQL 补全 111 → star 曲线 78/87 → 入表 74；爆发阈值 v7≥max(200, P90=122) 且加速度≥3

## 版图（topic 共现聚类，前 6 簇）
- 簇 1（42 个 topic）：developer-tools · code-intelligence · ai-agents · mcp · code-search · mcp-server
- 簇 2（33 个 topic）：claude-code · code-analysis · codex · knowledge-graph · ast · agent-skills
- 簇 3（23 个 topic）：claude · cursor · documentation · agent-orchestration · agent-memory · agent
- 簇 4（23 个 topic）：cli · openai · gemini · github · chatgpt · model-context-protocol
- 簇 5（20 个 topic）：ai-coding · coding-agent · golang · ai-tools · vibe-coding · context-engineering
- 簇 6（15 个 topic）：codebase-analysis · static-analysis · code-understanding · call-graph · code-generation · claude-code-skill

## 分层
| 层 | 仓库 | ★ | 近7天 | 近28天 | 加速度 | 近12周 | 采用（依赖方或月下载） | 90天提交 | 标记 | 说明 |
|---|---|---|---|---|---|---|---|---|---|---|
| 新星 | [trailhq/Trail-Code](https://github.com/trailhq/Trail-Code) | 10,471 | 494 | 1,584 | 0.68 | `▄▄█▆▃▆█▅▂▂▃▃` | 27,454/月 | 380 |  | Turbocharge Claude Code, Cursor, Codex, Gemini & every coding agent: f |
| 新星 | [AxiomCodeAI/axiomcodegraph](https://github.com/AxiomCodeAI/axiomcodegraph) | 237 | 119 | 235 | 119.0 | `▁▁▁▁▁▁▄▄█` | - | 1906 |  | Turn any codebase into a knowledge graph grounded in formal methods. Y |
| 新星 | [aoci-spec/aoci-code](https://github.com/aoci-spec/aoci-code) | 1,636 | 109 | 1,179 | 1.03 | `▁▁▂▂▁▂▂▄█▅▂` | 0/月 | 281 |  | A persistent, Git-versioned map of your whole codebase and database sc |
| 新星 | [MichaelKinsy/PiG](https://github.com/MichaelKinsy/PiG) | 661 | 63 | 657 | 0.47 | `▁█▅▂▂` | 4,987/月 | 115 |  | PiG (Pi in Go) is a faithful Go port of upstream Pi, the TypeScript co |
| 新星 | [FinanceFlash/unvibecode](https://github.com/FinanceFlash/unvibecode) | 323 | 59 | 202 | 7.38 | `▁▅▁▁▁▁▂▁▁█▄` | - | 251 |  | Complex code hides connections, workflows, and business risks.Unvibe c |
| 新星 | [Sidiora-Labs/hyperfide](https://github.com/Sidiora-Labs/hyperfide) | 433 | 2 | 418 | 2.0 | `▁▁▁▁▁▁█▅▅▁` | - | 3369 |  | The ai agent workflow tool that scales from small, simple projects to  |
| 新星 | [Raja0sama/vibex](https://github.com/Raja0sama/vibex) | 389 | 0 | 385 | 0.0 | `▁▁█▁▁` | - | 71 |  | Architecture diagrams and checkable docs from your codebase — ERD, C4, |
| 基石 | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | 129,418 | 3,278 | 9,414 | 1.41 | `█▅▅▅▆▅▄▅▄▄▄▆` | 1,630,115/月 | 1206 |  | Turn any codebase, with its docs, SQL schemas, configs, and PDFs, into |
| 基石 | [Aider-AI/aider](https://github.com/Aider-AI/aider) | 49,653 | 155 | 672 | 0.84 | `████▇█▇▆▇▆▇▆` | - | 0 | 90 天提交<5 | aider is AI pair programming in your terminal |
| 基石 | [yamadashy/repomix](https://github.com/yamadashy/repomix) | 28,923 | 122 | 531 | 1.01 | `▇▇█▆▅▅▆▅▇▆▅▆` | 589,156/月 | 332 |  | 📦 Repomix is a powerful tool that packs your entire repository into a  |
| 基石 | [coderamp-labs/gitingest](https://github.com/coderamp-labs/gitingest) | 15,961 | 56 | 402 | 0.83 | `▂▂▂▂▂▃▄██▆▄▃` | 163,303/月 | 0 | 90 天提交<5 | Replace 'hub' with 'ingest' in any GitHub URL to get a prompt-friendly |
| 主流/长尾 | [tt-a1i/archify](https://github.com/tt-a1i/archify) | 86,042 | 2,926 | 16,308 | 0.54 | `▁▁▁▁█▄▃▂▂▂▂▁` | 33,078/月 | 1676 |  | Turn any idea, plan, or codebase into a beautiful interactive diagram. |
| 主流/长尾 | [Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) | 87,107 | 971 | 3,604 | 1.19 | `▆█▅▅▅▄▇▅▆▅▅▆` | 0/月 | 102 |  | Graphs that teach > graphs that impress. Turn any code into an interac |
| 主流/长尾 | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | 46,984 | 507 | 2,934 | 0.56 | `██▆██▆▅▆█▃▅▄` | 61,005/月 | 2653 |  | High-performance code intelligence MCP server. Indexes codebases into  |
| 主流/长尾 | [repowise-dev/repowise](https://github.com/repowise-dev/repowise) | 7,865 | 204 | 951 | 1.08 | `▄▅█▂▁▁▃▃▂▁▅▂` | 22,639/月 | 2296 |  | Codebase intelligence for AI and humans: code health scores, auto-gene |
| 主流/长尾 | [ahmedkhaleel2004/gitdiagram](https://github.com/ahmedkhaleel2004/gitdiagram) | 18,332 | 168 | 1,430 | 1.14 | `▁▁▁▁▁▁▁█▆▄▃▂` | 0/月 | 448 |  | Visualize any GitHub codebase: free interactive architecture diagrams  |
| 主流/长尾 | [AsyncFuncAI/deepwiki-open](https://github.com/AsyncFuncAI/deepwiki-open) | 18,231 | 54 | 229 | 0.77 | `▇▇███▆▇▆▆▄▇▅` | 0/月 | 20 |  | Open Source DeepWiki: AI-Powered Wiki Generator for GitHub/Gitlab/Bitb |
| 主流/长尾 | [vitali87/code-graph-rag](https://github.com/vitali87/code-graph-rag) | 5,268 | 22 | 124 | 0.49 | `▁█▅▂▁▂▁▁▁▁▁▁` | 0/月 | 6778 |  | The ultimate RAG for your monorepo. Query, understand, and edit multi- |
| 主流/长尾 | [giancarloerra/SocratiCode](https://github.com/giancarloerra/SocratiCode) | 3,346 | 13 | 40 | 1.08 | `▇█▃▃▂▃▂▃▂▂▁▂` | 32,199/月 | 390 |  | Enterprise-grade (40m+ LOC) codebase intelligence, zero-setup, local & |
| 主流/长尾 | [sopaco/deepwiki-rs](https://github.com/sopaco/deepwiki-rs) | 3,135 | 12 | 59 | 0.8 | `▁▃▁▁▁▁█▂▁▁▁▁` | 8,608/月 | 21 |  | Turn code into clarity. Generate accurate technical docs and AI-ready  |
| 主流/长尾 | [sourcebot-dev/sourcebot](https://github.com/sourcebot-dev/sourcebot) | 4,000 | 10 | 61 | 0.83 | `▁█▃▁▁▁▁▁▁▂▁▁` | 1,415/月 | 176 |  | Sourcebot is a self-hosted tool that helps humans and agents understan |
| 主流/长尾 | [AIDotNet/OpenDeepWiki](https://github.com/AIDotNet/OpenDeepWiki) | 3,634 | 9 | 36 | 0.64 | `▃█▁▃▃▃▂▂▁▁▂▂` | 0/月 | 64 |  | OpenDeepWiki is the open-source version of the DeepWiki project, aimin |
| 主流/长尾 | [Ataraxy-Labs/sem](https://github.com/Ataraxy-Labs/sem) | 3,415 | 7 | 64 | 0.48 | `▃▆▄▄▄▃▄▃▃█▄▂` | 74,823/月 | 142 |  | Semantic version control => entity-level diffs, blame, and impact anal |
| 衰退/沉寂 | [regenrek/deepwiki-mcp](https://github.com/regenrek/deepwiki-mcp) | 1,386 | 1 | 3 | 1.0 | `▁▇▄▁▁█▂▄▁▄▁▂` | 10,006/月 | 0 |  | 📖 MCP server for fetch deepwiki.com and get latest knowledge in Cursor |
| 衰退/沉寂 | [salesforce/CodeT5](https://github.com/salesforce/CodeT5) | 3,092 | 0 | 2 | 0.0 | `▄▁▁▁▁▁▁▁▁█▁▁` | 0/月 | 0 |  | Home of CodeT5: Open Code LLMs for Code Understanding and Generation |

## 数据质量
- star 历史：`GET /repos/{o}/{r}/stargazers/history`（API 版本 2026-03-10），成功 78/87
- stargazer 列表接口已对非协作者关闭：反刷星只用聚合信号，命中标记即“热度未验证”，不剔除
- 依赖方：ecosyste.ms packages lookup，仅前 40 个候选；未发包的仓库显示“-”
- 未使用：GH Archive / OSS Insight 事件排行 / ClickHouse github_events（2026 年数据缺失）
- 耗时：{"search_s": 63.8, "graphql_s": 45.4, "star_history_s": 42.1, "adoption_s": 82.6, "total_s": 233.9}

## 查询切片
- `topic:code-intelligence stars:>100 pushed:>2026-04-20` → total 39，取 30
- `topic:codebase-analysis stars:>50 pushed:>2026-04-20` → total 12，取 12
- `topic:code-graph stars:>50 pushed:>2026-04-20` → total 17，取 17
- `codebase knowledge graph in:description stars:>200 pushed:>2026-04-20` → total 13，取 13
- `codebase llm context in:description stars:>200 pushed:>2026-04-20` → total 2，取 2
- `deepwiki in:name,description stars:>100` → total 12，取 12
- `repository map llm in:description stars:>100` → total 0，取 0
- `codebase in:description created:>2026-07-20 stars:>200` → total 12，取 12
- `agent skill codebase in:description,topics stars:>20 created:>2026-04-01` → total 16，取 16
