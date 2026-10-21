# hubradar

> 发现增长黑马，拆解架构核心，拒绝重复造轮子。

HubRadar 是一个专注开源技术选型与架构拆解的工具，提供周级 Star 增长加速度雷达与 3 分钟源码事实锚定白皮书。

本 npm 包为 HubRadar CLI 的官方 Node.js 启动包装器。

## 安装与使用

HubRadar 核心引擎由 Python 驱动，推荐使用 [uv](https://github.com/astral-sh/uv) 安装：

```sh
# 推荐全局安装
uv tool install hubradar

# 或者使用 pip
pip install hubradar
```

安装后即可直接在命令行使用 `hubradar`，也可以通过 `npx hubradar` 调用。

## 快速体验

```sh
# 查看版本
npx hubradar --version

# 生成离线白皮书
npx hubradar html card.md -o report.html
```

## 官方链接

- GitHub: [https://github.com/Li-Sanze/hubradar](https://github.com/Li-Sanze/hubradar)
- 许可证: MIT
