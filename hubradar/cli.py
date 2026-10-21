"""Unified, lazy-loading command line interface."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import __version__


def parser():
    root = argparse.ArgumentParser(
        prog="hubradar",
        description="源码证据 → 宿主 Agent 综合 → 引文验证 → 可离线分享的报告",
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="从本地 Git HEAD 准备证据包，不执行目标源码")
    prepare.add_argument("repo_dir", type=Path)
    prepare.add_argument("--repo", required=True, help="GitHub owner/repo，用于证据链接")
    prepare.add_argument("-o", "--out", required=True, type=Path)
    prepare.add_argument("--offline", action="store_true", help="不获取 GitHub 社区信号")
    finalize = commands.add_parser("finalize", help="验证 raw_distill.json 并生成 card.md")
    finalize.add_argument("work", type=Path, help="包含 facts.json 与 raw_distill.json")
    finalize.add_argument("--source", required=True, type=Path, help="包含固定提交的本地 Git 仓库")
    finalize.add_argument("-o", "--out", required=True, type=Path)
    finalize.add_argument("--html", action="store_true", help="验证成功后同时生成 index.html")
    radar = commands.add_parser("radar", help="按领域配置搜索、补全并生成雷达")
    radar.add_argument("domain", type=Path, help="领域 JSON 配置")
    radar.add_argument("-o", "--out", required=True, type=Path)
    radar.add_argument("--html", action="store_true")
    html = commands.add_parser("html", help="把 card.md / radar.md 渲染为离线单文件 HTML")
    html.add_argument("markdown", type=Path)
    html.add_argument("-o", "--out", type=Path, help="默认同目录 index.html")
    html.add_argument("--title", help="可选页面标题")
    arch = commands.add_parser("arch", help="生成 DSH 盒模型架构 SVG（支持 JSON spec 或预置模板）")
    arch.add_argument("spec", nargs="?", type=Path, help="可选架构 spec JSON 文件；缺省生成 Hono 模板")
    arch.add_argument("-o", "--out", type=Path, help="输出 SVG 路径，缺省打印到标准输出")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            from .prepare import main as prepare
            prepare(args.repo_dir, args.repo, args.out, offline=args.offline)
        elif args.command == "finalize":
            from .finalize import main as finalize
            result = finalize(args.work, args.source, args.out)
            if result:
                if args.html and (args.out / "index.html").exists():
                    print("hubradar: 验证失败，已有 index.html 未更新，请勿把旧 HTML 当作本次结果。", file=sys.stderr)
                return result
            if args.html:
                from .html_report import render_file
                render_file(args.out / "card.md", args.out / "index.html")
        elif args.command == "radar":
            from .radar import main as radar
            result = radar(args.domain, args.out)
            if result:
                return result
            if args.html:
                from .html_report import render_file
                render_file(args.out / "radar.md", args.out / "index.html")
        elif args.command == "arch":
            from .dsh_architecture import (
                build_hono_architecture_spec,
                build_hubradar_architecture_spec,
                generate_dsh_svg,
            )
            if args.spec:
                spec_str = str(args.spec).strip()
                if spec_str.lower() == "hubradar":
                    spec_data = build_hubradar_architecture_spec()
                elif spec_str.lower() == "hono":
                    spec_data = build_hono_architecture_spec()
                elif Path(args.spec).exists():
                    spec_data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
                else:
                    spec_data = build_hubradar_architecture_spec()
            else:
                spec_data = build_hono_architecture_spec()
            svg_content = generate_dsh_svg(spec_data)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(svg_content, encoding="utf-8")
                print(args.out)
            else:
                print(svg_content)
        else:
            from .html_report import render_file
            path = render_file(args.markdown, args.out, title=args.title)
            print(path)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"hubradar: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("hubradar: 已中断；已写入的证据保留。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

