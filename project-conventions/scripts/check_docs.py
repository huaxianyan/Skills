#!/usr/bin/env python3
"""项目文档结构检查（project-conventions 技能的配套脚本）。

纯标准库，不依赖仓库内的任何东西。检查项来自技能正文的
「内容落点」「选形态与体量预算」「归档与形态升级」「双副本」几节。

用法：
    python check_docs.py <项目目录> [<项目目录> ...]
    python check_docs.py --archive-repo E:/Dev/AgentHistory E:/Dev/PixelFix

退出码：0 全部通过；1 有告警；2 参数错误。

配置文件（可选）：项目根目录的 .docscheck.json，字段：

    {
      "root_docs_allow": ["BRANCH_AUDIT.md"],   # docs/ 根允许的额外文件
      "max_status_lines": 500,
      "max_status_entries": 30,
      "max_agents_lines": 100,
      "skip": ["agents-budget"]                 # 跳过的检查项 id
    }
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATUS_ENTRY = re.compile(r"^##\s+(?:STATUS-)?(\d{3})\s*[：:]\s*(.*)$")
DATE_ENTRY = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})")
ARCHIVE_NAME = re.compile(
    r"^STATUS-(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2}|\d{4})\.md$"
)
SEMVER_NOTE = re.compile(r"^v\d+\.\d+\.\d+(-\S+)?\.md$")
LOCAL_PATH = re.compile(r"7inaBranford|7inaWork-Windows|E:[/\\]Dev\b|C:[/\\]Neko7ina")

ROOT_DOCS_STANDARD = {
    "STATUS.md",
    "DECISIONS.md",
    "RELEASE.md",
    "README.md",
    "COMPATIBILITY.md",
    "HANDOFF.md",
    "PLAN.md",
}

DEFAULTS = {
    "root_docs_allow": [],
    "max_status_lines": 500,
    "max_status_entries": 30,
    "max_agents_lines": 100,
    "archive_repo": None,
    "skip": [],
}


def load_config(repo: Path) -> dict:
    cfg = dict(DEFAULTS)
    path = repo / ".docscheck.json"
    if path.is_file():
        try:
            cfg.update(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            report.add(repo.name, "config", f".docscheck.json 解析失败：{exc}")
    return cfg


class Report:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, str]] = []  # (repo, check, message)

    def add(self, repo: str, check: str, message: str) -> None:
        self.items.append((repo, check, message))

    def has_problems(self) -> bool:
        return bool(self.items)

    def dump(self) -> None:
        if not self.items:
            print("全部通过。")
            return
        current = None
        for repo, check, message in self.items:
            if repo != current:
                print(f"\n== {repo}")
                current = repo
            print(f"  [{check}] {message}")


report = Report()


def rel(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_status(repo: Path, cfg: dict) -> None:
    status = repo / "docs" / "STATUS.md"
    if not status.is_file():
        handoff = repo / "docs" / "handoff"
        if handoff.is_dir() and any(handoff.glob("*.md")):
            return  # 采用「决策文件加日期流水」形态，不要求 STATUS.md
        report.add(
            repo.name,
            "status-exists",
            "既没有 docs/STATUS.md，也没有 docs/handoff/ 里的交接流水",
        )
        return

    text = read(status)
    lines = text.splitlines()

    # 1. 头部「当前主线」必须出现，且必须在第一条进度条目之前
    main_line = next((i for i, l in enumerate(lines) if "当前主线" in l), None)
    first_entry = next(
        (i for i, l in enumerate(lines) if STATUS_ENTRY.match(l) or DATE_ENTRY.match(l)),
        None,
    )
    if main_line is None:
        report.add(repo.name, "status-header", "docs/STATUS.md 里没有「当前主线」小节")
    elif first_entry is not None and main_line > first_entry:
        report.add(
            repo.name,
            "status-header",
            f"「当前主线」在第 {main_line + 1} 行，晚于第 {first_entry + 1} 行的第一条条目",
        )

    # 2. 体量预算
    if len(lines) > cfg["max_status_lines"]:
        report.add(
            repo.name,
            "status-budget",
            f"{len(lines)} 行，超过 {cfg['max_status_lines']} 行预算，需要整批归档",
        )

    entries = [(i, STATUS_ENTRY.match(l)) for i, l in enumerate(lines)]
    numbered = [(i, m.group(1), m.group(2)) for i, m in entries if m]
    dated = [i for i, l in enumerate(lines) if DATE_ENTRY.match(l)]

    if len(numbered) > cfg["max_status_entries"]:
        report.add(
            repo.name,
            "status-budget",
            f"{len(numbered)} 条编号条目，超过 {cfg['max_status_entries']} 条预算",
        )

    # 3. 编号唯一且单调递增
    if numbered:
        seen: dict[str, int] = {}
        for line_no, num, _ in numbered:
            if num in seen:
                report.add(
                    repo.name,
                    "status-numbering",
                    f"STATUS-{num} 重复出现（第 {seen[num] + 1} 行与第 {line_no + 1} 行）",
                )
            else:
                seen[num] = line_no
        order = [int(num) for _, num, _ in numbered]
        if order != sorted(order) and order != sorted(order, reverse=True):
            step = -1 if order[0] >= order[-1] else 1
            bad = next(
                (i for i in range(1, len(order)) if step * (order[i] - order[i - 1]) <= 0),
                None,
            )
            if bad is not None:
                report.add(
                    repo.name,
                    "status-order",
                    f"条目顺序不统一：STATUS-{order[bad - 1]:03d} 之后出现 STATUS-{order[bad]:03d}",
                )
        if dated:
            report.add(
                repo.name,
                "status-numbering",
                f"同时存在编号条目与 {len(dated)} 条日期条目，全项目只用一种",
            )
    elif dated and len(dated) < 3:
        report.add(
            repo.name,
            "status-numbering",
            "只有少数日期条目、也没有编号条目，确认是否漏了编号方案",
        )


def check_archive(repo: Path) -> None:
    archive = repo / "docs" / "archive"
    if not archive.is_dir():
        return
    status = read(repo / "docs" / "STATUS.md")
    for path in sorted(archive.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        if not ARCHIVE_NAME.match(path.name):
            report.add(
                repo.name,
                "archive-name",
                f"docs/archive/{path.name} 不符合 STATUS-<起始日期>_<截止日期>.md",
            )
        if path.name not in status:
            report.add(
                repo.name,
                "archive-index",
                f"docs/STATUS.md 里没有指向 docs/archive/{path.name} 的索引行",
            )


def check_handoff(repo: Path) -> None:
    handoff = repo / "docs" / "handoff"
    if not handoff.is_dir():
        return
    for path in sorted(handoff.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        if ARCHIVE_NAME.match(path.name):
            report.add(
                repo.name,
                "handoff-mix",
                f"docs/handoff/{path.name} 看起来是归档文件，归档应放 docs/archive/",
            )


def check_release_notes(repo: Path) -> None:
    docs = repo / "docs"
    flat = sorted(docs.glob("release-notes-*.md")) if docs.is_dir() else []
    for path in flat:
        report.add(
            repo.name,
            "release-notes",
            f"{rel(repo, path)} 应改为 docs/release-notes/v<版本>.md",
        )
    notes = docs / "release-notes"
    if not notes.is_dir():
        return
    for path in sorted(notes.glob("*.md")):
        if path.name.upper() in {"README.MD", "INDEX.MD"}:
            continue
        if not SEMVER_NOTE.match(path.name):
            report.add(
                repo.name,
                "release-notes",
                f"docs/release-notes/{path.name} 不符合 v<主>.<次>.<修订>.md",
            )


def check_root_docs(repo: Path, cfg: dict) -> None:
    docs = repo / "docs"
    if not docs.is_dir():
        return
    allowed = ROOT_DOCS_STANDARD | set(cfg["root_docs_allow"])
    stray = [p for p in sorted(docs.glob("*.md")) if p.name not in allowed]
    if len(stray) > 5:
        preview = "、".join(p.name for p in stray[:5])
        more = f" 等 {len(stray)} 个" if len(stray) > 5 else ""
        report.add(
            repo.name,
            "docs-root",
            f"docs/ 根有 {len(stray)} 个非标准文件：{preview}{more}，"
            "研究类文档归 docs/research/，长手册起个固定名字后加进 allow",
        )


def check_release_manual(repo: Path) -> None:
    names = [
        name
        for name in ("RELEASE.md", "RELEASING.md")
        if (repo / name).is_file() or (repo / "docs" / name).is_file()
    ]
    if len(names) > 1:
        report.add(repo.name, "release-manual", "RELEASE.md 与 RELEASING.md 并存，只留一个")


def check_local_paths(repo: Path) -> None:
    if not (repo / ".git").exists():
        return  # 纯本地目录，没有公开暴露面
    if not subprocess.run(
        ["git", "-C", str(repo), "remote"], capture_output=True, text=True
    ).stdout.strip():
        return  # 有仓库但没有远端，同样不对外
    docs = repo / "docs"
    if not docs.is_dir():
        return
    for path in sorted(docs.rglob("*.md")):
        for line_no, line in enumerate(read(path).splitlines(), 1):
            if LOCAL_PATH.search(line):
                report.add(
                    repo.name,
                    "no-local-path",
                    f"{rel(repo, path)}:{line_no} 出现本机路径或主机名，这类内容只能留在不入库的 AGENTS.md",
                )
                break


def check_agents(repo: Path, cfg: dict) -> None:
    agents = repo / "AGENTS.md"
    if not agents.is_file():
        return
    count = len(read(agents).splitlines())
    if count > cfg["max_agents_lines"]:
        report.add(
            repo.name,
            "agents-budget",
            f"AGENTS.md {count} 行，超过 {cfg['max_agents_lines']} 行；"
            "技术细节下移到 docs/，本机路径与设备信息压成摘要",
        )
    archive_repo = cfg.get("archive_repo")
    if not archive_repo:
        return
    copy = Path(archive_repo) / "projects" / repo.name / "AGENTS.md"
    if not copy.is_file():
        report.add(
            repo.name,
            "agents-copy",
            f"归档仓库没有 projects/{repo.name}/AGENTS.md，按双副本规则应存在",
        )
        return
    if read(agents) != read(copy):
        report.add(
            repo.name,
            "agents-copy",
            "本地 AGENTS.md 与归档副本不一致，按「内容更多更新的为准」对齐后两边都推",
        )


CHECKS = {
    "status": lambda repo, cfg: check_status(repo, cfg),
    "archive": lambda repo, cfg: check_archive(repo),
    "handoff": lambda repo, cfg: check_handoff(repo),
    "release-notes": lambda repo, cfg: check_release_notes(repo),
    "docs-root": lambda repo, cfg: check_root_docs(repo, cfg),
    "release-manual": lambda repo, cfg: check_release_manual(repo),
    "no-local-path": lambda repo, cfg: check_local_paths(repo),
    "agents": lambda repo, cfg: check_agents(repo, cfg),
}


def main(argv: list[str]) -> int:
    archive_repo = None
    repos: list[Path] = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--archive-repo":
            if not args:
                print("--archive-repo 需要一个路径", file=sys.stderr)
                return 2
            archive_repo = args.pop(0)
        elif arg in {"-h", "--help"}:
            print(__doc__)
            return 0
        elif arg.startswith("-"):
            print(f"未知参数：{arg}", file=sys.stderr)
            return 2
        else:
            repos.append(Path(arg).resolve())

    if not repos:
        print(__doc__)
        return 2

    for repo in repos:
        if not repo.is_dir():
            print(f"不是目录：{repo}", file=sys.stderr)
            return 2
        if not (repo / "docs").is_dir():
            report.add(repo.name, "docs-exists", "没有 docs/ 目录，不是按本规范维护的项目，已跳过")
            continue
        cfg = load_config(repo)
        cfg["archive_repo"] = archive_repo or cfg.get("archive_repo")
        skip = set(cfg.get("skip") or [])
        for name, run in CHECKS.items():
            if name in skip:
                continue
            run(repo, cfg)

    report.dump()
    return 1 if report.has_problems() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
