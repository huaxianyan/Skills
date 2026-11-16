#!/usr/bin/env python3
"""公开前的脱敏体检：把私有笔记往公开仓库搬之前跑一遍。

「本机项目」的笔记本来就含主机名、内网地址、服务器绝对路径、设备序列号这类事实，
放在私有档案仓库里没问题。一旦要搬进公开仓库，这些就是泄漏。本脚本按已知形态扫一遍，
列出每一处命中，交给人逐条判定：替换成占位符、改写成通用描述，还是删掉。

用法：
    python check_publish.py <目录> [<目录> ...]
    python check_publish.py <目录> --config <仓库>/.publishcheck.json

配置（可选，放在待公开仓库根）只用来补规则，不是用来放过真实敏感值的：

    {
      "extra_terms": ["我的域名.example", "某台主机名"],
      "allow_lines": ["192\\.0\\.2\\.", "198\\.51\\.100\\."]
    }

退出码 0 表示没命中，1 表示有命中。**没命中不代表可以公开**：判据是内容里的人、机器、
位置能不能反推到具体实体，脚本只覆盖已知形态。

只用标准库。
"""

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".ini", ".conf", ".sh",
    ".ps1", ".py", ".js", ".mjs", ".ts", ".vue", ".html", ".css", ".sql", ".env",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

# 规则：(名字, 正则, 说明)。正则只写在有真实形态的地方，宁可少报也不用宽泛规则刷屏。
RULES = [
    (
        "内网地址",
        re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"),
        "内网 IP，换成 RFC 5737 文档段（192.0.2.0/24 等）",
    ),
    (
        "公网地址",
        re.compile(r"\b(?!(?:127|0|255)\.)(?!(?:192\.0\.2|198\.51\.100|203\.0\.113)\.)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        "真实公网 IP，换成 203.0.113.x 这类文档段",
    ),
    (
        "主机名",
        re.compile(
            r"\b(?:shiva|ifrit|ramuh|phoenix|bahamut|ragnarok|numeron|fugusekai|"
            r"blazer|tiamat|leviathan|garuda)\b",
            re.IGNORECASE,
        ),
        "本机主机名，改成「某台服务器」或代号 A/B",
    ),
    (
        "自有域名",
        re.compile(r"\b[a-z0-9-]+\.neko7ina\.com\b|neko7ina\.com|fugusekai\.com|bao\.tv", re.IGNORECASE),
        "自有域名，换成 example.com",
    ),
    (
        "账户名",
        re.compile(r"7inaBranford|NeKo7inA|\b7ina\b", re.IGNORECASE),
        "本机用户名，换成 <user>",
    ),
    (
        "服务器绝对路径",
        re.compile(r"(?<![\w/])/srv/|/etc/caddy/|/home/[a-z][\w.-]*/|/root/"),
        "服务器路径，换成 <部署目录> 这类描述",
    ),
    (
        "Windows 绝对路径",
        re.compile(r"\b[A-Z]:[\\/](?:Users|Neko7ina|Dev|Syncthing)\b|%APPDATA%|%LOCALAPPDATA%"),
        "本机路径，换成相对路径或 <数据目录>",
    ),
    (
        "SSH 或凭据",
        re.compile(r"ssh-(?:rsa|ed25519|dss) AAAA|BEGIN [A-Z ]*PRIVATE KEY|SHA256:[A-Za-z0-9+/=]{30,}"),
        "公钥指纹或私钥，公开仓库里只留「用 SSH 密钥认证」这种描述",
    ),
    (
        "URL 内嵌口令",
        re.compile(r"://[^\s/:@]+:[^\s/@]+@"),
        "URL 里带账号口令，删掉换成占位符",
    ),
    (
        "令牌字段",
        re.compile(r"(?i)\b(?:token|secret|passwd|password|api[_-]?key|salt)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}"),
        "看起来是实值，改成占位符或删除整行",
    ),
    (
        "MAC 地址",
        re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b"),
        "设备网卡地址，改成 <mac>",
    ),
    (
        "设备序列号形态",
        re.compile(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{15,16}\b"),
        "可能是设备序列号或长 ID（须同时含数字与大写字母），确认后替换",
    ),
    (
        "隧道网段编号",
        re.compile(r"\b[0-9a-f]{16}\b"),
        "可能是 ZeroTier 网络 ID；若是提交 SHA 可不改",
    ),
]


def load_config(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"配置解析失败，按无配置继续：{exc}", file=sys.stderr)
        return {}


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        yield path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="公开前的脱敏体检")
    parser.add_argument("paths", nargs="+", help="待检查的目录")
    parser.add_argument("--config", help=".publishcheck.json 的路径")
    parser.add_argument("--max-per-file", type=int, default=20, help="每个文件最多列多少条")
    args = parser.parse_args(argv)

    cfg = load_config(Path(args.config) if args.config else None)
    allow = [re.compile(p) for p in cfg.get("allow_lines", [])]
    extra = [(term, re.compile(re.escape(term))) for term in cfg.get("extra_terms", [])]

    total = 0
    for root_arg in args.paths:
        root = Path(root_arg).resolve()
        if not root.is_dir():
            print(f"不是目录：{root}", file=sys.stderr)
            return 2
        hits_by_file: dict[Path, list[str]] = {}
        for path in iter_files(root):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            shown = path.relative_to(root).as_posix()
            for lineno, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith(("> ", "<!--")) and "占位" in line:
                    continue
                if any(p.search(line) for p in allow):
                    continue
                for name, pattern, _advice in RULES:
                    m = pattern.search(line)
                    if m:
                        hits_by_file.setdefault(path, []).append(
                            f"{shown}:{lineno} [{name}] {m.group(0)[:60]}"
                        )
                for term, pattern in extra:
                    if pattern.search(line):
                        hits_by_file.setdefault(path, []).append(
                            f"{shown}:{lineno} [自定义词] {term}"
                        )
        if not hits_by_file:
            print(f"{root.name}：未命中已知形态")
            continue
        print(f"\n== {root.name}")
        for path, hits in hits_by_file.items():
            total += len(hits)
            for hit in hits[: args.max_per_file]:
                print(f"  {hit}")
            if len(hits) > args.max_per_file:
                print(f"  …… 还有 {len(hits) - args.max_per_file} 条")

    if total:
        print(
            f"\n共 {total} 处命中。逐条判定：换成占位符、改写成通用描述，或删掉。"
            "\n凭据值本身永远不搬——只写「放在哪个文件」。"
            "\n没命中不等于可以公开，脚本只认已知形态。"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
