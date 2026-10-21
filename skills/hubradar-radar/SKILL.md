---
name: hubradar-radar
description: 建立某技术领域的 GitHub 版图，发现可复用候选与近期趋势，并生成有来源和覆盖边界的领域雷达。用于领域调研、寻找现成轮子或跨领域发现；单仓库深读使用 hubradar。
metadata:
  requirements: 已安装的 hubradar CLI、已认证的 gh，以及可访问 GitHub 和 ecosyste.ms 的网络。
---

# HubRadar 领域雷达

帮助开发者决定下一步看谁、借什么。趋势、成熟度与需求适配分开解释。

1. 确认 `hubradar --version` 可用；不自行猜测同名包安装地址。
2. 根据领域和目标列出边界、近义词、相邻类别和排除项。通常无需连续追问，先说明合理假设。
3. 在用户授权的输出目录写领域 JSON：

```json
{
  "id": "my-domain",
  "name": "领域名称",
  "seeds": ["owner/repo"],
  "queries": ["topic:topic-name stars:>100"],
  "history_top": 20,
  "history_cap": 30,
  "ignore_topics": ["ai", "python"],
  "exclude_desc": "$^"
}
```

4. 执行 `hubradar radar DOMAIN_JSON -o OUT --html`，读取 `radar.json`、`radar.md`。查询日期按当前调研窗口填写，不照抄过期样例。
5. 说明查询切片、每次仅取最多 30 个候选、history cap 和 API 缺失。数据不可用时保留“未知”，不要补造增长曲线。
6. 从结果选 5—12 个代表，按实际职责和使用场景组织；topic 共现只是线索，不等于已经核实的技术分类。作者想避免重复实现时，优先给能直接安装或组合的候选。
7. 对 1—3 个真正相关的候选建议转入 hubradar 深读。返回本地 HTML/Markdown 和来源，不自动发布，也不批量给候选项目发推广消息。

## 解读规则

- “爆发/新星/基石”来自脚本启发式，不是代码质量或安全认证。
- 7/28 天趋势仅在历史覆盖足够时解释；数据窗口和观察时间必须可见。
- 缺少 issue、fork 少或提交少只是待核验信号，不能据此指控刷星或判断项目不可用。
- downloads、依赖方、Star 是不同指标，不能混算成真实生产用户数。
- 未发包、API 失败和真实零采用应分开说明；不要把缺失数据当 0。
- HTML 是离线单文件，当前提供筛选、排序、主题和打印；宽表在自身容器中滚动。
- 只要求咨询时可以直接在对话中给结论；持久化和自动化刷新须在用户授权范围内。
