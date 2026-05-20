#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 RAW 文件夹中没有对应 JPG 的 RAW 文件。

目录结构假设：
    A/
    ├── JPG/   (存放 .jpg / .jpeg 文件)
    └── RAW/   (存放 .raw 文件)

用法：
    python clean_raw.py /absolute/path/to/A
    python clean_raw.py /absolute/path/to/A --dry-run     # 仅预览不删除
    python clean_raw.py /absolute/path/to/A --jpg-ext jpg jpeg
"""

import argparse
import sys
from pathlib import Path


def collect_stems(folder: Path, extensions):
    """
    返回 folder 下所有指定扩展名文件的「主文件名」(不含扩展名) 集合。
    扩展名比较不区分大小写，以兼容 .JPG / .jpg / .Jpg 等情况。
    """
    exts = {e.lower().lstrip(".") for e in extensions}
    stems = set()
    for entry in folder.iterdir():
        if entry.is_file() and entry.suffix.lower().lstrip(".") in exts:
            stems.add(entry.stem)
    return stems


def find_orphan_raws(jpg_dir: Path, raw_dir: Path, jpg_exts, raw_exts):
    """找到 RAW 目录中没有同名 JPG 的文件列表。"""
    jpg_stems = collect_stems(jpg_dir, jpg_exts)
    raw_exts_lower = {e.lower().lstrip(".") for e in raw_exts}

    orphans = []
    for entry in raw_dir.iterdir():
        if entry.is_file() and entry.suffix.lower().lstrip(".") in raw_exts_lower:
            if entry.stem not in jpg_stems:
                orphans.append(entry)
    return orphans


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="删除 RAW 文件夹中没有对应 JPG 的 RAW 文件。"
    )
    parser.add_argument(
        "root",
        help="目录 A 的绝对路径，里面应包含 JPG 与 RAW 两个子目录。",
    )
    parser.add_argument(
        "--jpg-dir", default="JPG", help="JPG 子目录名 (默认: JPG)"
    )
    parser.add_argument(
        "--raw-dir", default="RAW", help="RAW 子目录名 (默认: RAW)"
    )
    parser.add_argument(
        "--jpg-ext",
        nargs="+",
        default=["jpg", "jpeg"],
        help="视为 JPG 的扩展名列表 (默认: jpg jpeg)",
    )
    parser.add_argument(
        "--raw-ext",
        nargs="+",
        default=["raw"],
        help="视为 RAW 的扩展名列表 (默认: raw)。"
             "若你的相机是 NEF/CR2/ARW 等，可在此覆盖。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将被删除的文件，不实际删除。",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    root = Path(args.root)
    if not root.is_absolute():
        print(f"[错误] 必须传入绝对路径: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"[错误] 目录不存在: {root}", file=sys.stderr)
        return 2

    jpg_dir = root / args.jpg_dir
    raw_dir = root / args.raw_dir

    for d, label in [(jpg_dir, "JPG"), (raw_dir, "RAW")]:
        if not d.is_dir():
            print(f"[错误] 找不到 {label} 子目录: {d}", file=sys.stderr)
            return 2

    orphans = find_orphan_raws(jpg_dir, raw_dir, args.jpg_ext, args.raw_ext)

    if not orphans:
        print("无需删除：所有 RAW 文件都有对应的 JPG。")
        return 0

    action = "[预览]" if args.dry_run else "[删除]"
    deleted, failed = 0, 0
    for f in orphans:
        if args.dry_run:
            print(f"{action} {f}")
            continue
        try:
            f.unlink()
            print(f"{action} {f}")
            deleted += 1
        except OSError as e:
            print(f"[失败] {f} -> {e}", file=sys.stderr)
            failed += 1

    if args.dry_run:
        print(f"\n共发现 {len(orphans)} 个孤立 RAW 文件 (未实际删除)。")
    else:
        print(f"\n已删除 {deleted} 个文件，失败 {failed} 个。")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
