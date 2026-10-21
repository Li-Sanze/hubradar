#!/usr/bin/env node

const { spawnSync } = require("child_process");

const args = process.argv.slice(2);

// Check if Python hubradar is installed in PATH
const check = spawnSync("hubradar", ["--version"], { encoding: "utf-8" });

if (check.status === 0) {
  // Proxy directly to Python hubradar CLI
  const result = spawnSync("hubradar", args, { stdio: "inherit" });
  process.exit(result.status ?? 0);
}

// Fallback message when Python hubradar is not installed
console.log(`
◎ HubRadar — 发现增长黑马，拆解架构核心，拒绝重复造轮子。

HubRadar 核心引擎由 Python 驱动。请先安装底层 CLI：

  1. 推荐方式 (uv):
     $ uv tool install hubradar

  2. 或使用 pip:
     $ pip install hubradar

安装后即可全局使用 hubradar 命令，或直接运行 npx hubradar。
文档与源代码: https://github.com/Li-Sanze/hubradar
`);

if (args.includes("--version") || args.includes("-v")) {
  console.log("hubradar (npm wrapper) v0.1.0");
}
