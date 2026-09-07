"""실제 `git` 바이너리를 감싸는 얇은 래퍼.

이 모듈은 시뮬레이터가 실제 git 저장소(로컬 워킹 카피 + 로컬 bare 저장소를
"원격"으로 사용)를 만들고 검사하는 데 필요한 최소한의 기능만 제공한다.
전부 subprocess로 실제 git 명령을 호출하므로, 여기서 벌어지는 모든 일은
사용자가 터미널에서 똑같이 `git ...` 명령으로 재현할 수 있는 진짜 git 상태다.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gitsim.i18n import t as _


class GitError(RuntimeError):
    def __init__(self, args: list[str], returncode: int, stdout: str, stderr: str):
        self.args_ = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            _(
                "common.git_error",
                args=" ".join(args),
                returncode=returncode,
                detail=stderr.strip() or stdout.strip(),
            )
        )


def run(
    args: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        input=input_text,
    )
    if check and proc.returncode != 0:
        raise GitError(args, proc.returncode, proc.stdout, proc.stderr)
    return proc


def init_repo(path: Path, initial_branch: str = "main") -> None:
    path.mkdir(parents=True, exist_ok=True)
    run(["init", "-q", "-b", initial_branch], cwd=path)
    configure_identity(path)


def init_bare(path: Path, initial_branch: str = "main") -> None:
    path.mkdir(parents=True, exist_ok=True)
    run(["init", "-q", "--bare", "-b", initial_branch], cwd=path)
    # bare 저장소도 ref 변경 이력을 reflog로 남기게 해서, force-push 같은
    # 사고가 벌어졌을 때 "서버 쪽" 기록도 살펴볼 수 있게 한다.
    run(["config", "core.logAllRefUpdates", "true"], cwd=path)


def clone(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["clone", "-q", str(src), str(dest)])
    configure_identity(dest)


def configure_identity(path: Path, name: str = "GitSim 연습생", email: str = "practice@gitsim.local") -> None:
    run(["config", "user.name", name], cwd=path)
    run(["config", "user.email", email], cwd=path)
    run(["config", "commit.gpgsign", "false"], cwd=path)


def write_file(repo: Path, rel_path: str, content: str) -> Path:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def append_file(repo: Path, rel_path: str, content: str) -> Path:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(content)
    return target


def add_all(repo: Path) -> None:
    run(["add", "-A"], cwd=repo)


def commit(repo: Path, message: str, allow_empty: bool = False) -> str:
    args = ["commit", "-q", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    run(args, cwd=repo)
    return rev_parse(repo, "HEAD")


def rev_parse(repo: Path, ref: str) -> Optional[str]:
    proc = run(["rev-parse", "--verify", "-q", ref], cwd=repo, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def current_branch(repo: Path) -> Optional[str]:
    proc = run(["symbolic-ref", "--short", "-q", "HEAD"], cwd=repo, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    if not ancestor or not descendant:
        return False
    proc = run(["merge-base", "--is-ancestor", ancestor, descendant], cwd=repo, check=False)
    return proc.returncode == 0


def branches_containing(repo: Path, commit_hash: str) -> list[str]:
    proc = run(
        ["branch", "--format=%(refname:short)", "--contains", commit_hash],
        cwd=repo,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def object_exists(repo: Path, sha: str) -> bool:
    proc = run(["cat-file", "-e", sha], cwd=repo, check=False)
    return proc.returncode == 0


def file_at_ref(repo: Path, ref: str, rel_path: str) -> Optional[str]:
    proc = run(["show", f"{ref}:{rel_path}"], cwd=repo, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout


def status_porcelain(repo: Path) -> str:
    return run(["status", "--porcelain"], cwd=repo).stdout


def is_clean(repo: Path) -> bool:
    return status_porcelain(repo).strip() == ""


def has_conflict_markers(repo: Path) -> bool:
    proc = run(["diff", "--check"], cwd=repo, check=False)
    combined = proc.stdout + proc.stderr
    if "conflict marker" in combined.lower():
        return True
    proc2 = run(["diff", "--name-only", "--diff-filter=U"], cwd=repo, check=False)
    return bool(proc2.stdout.strip())


def log_graph(repo: Path, max_count: int = 30) -> str:
    proc = run(
        [
            "log",
            "--graph",
            "--oneline",
            "--decorate",
            "--all",
            f"-{max_count}",
        ],
        cwd=repo,
        check=False,
    )
    return proc.stdout


def reflog(repo: Path, ref: str = "HEAD", max_count: int = 40) -> str:
    proc = run(["reflog", "show", f"-{max_count}", ref], cwd=repo, check=False)
    return proc.stdout


@dataclass
class ReflogEntry:
    selector: str
    short_hash: str
    action: str


def reflog_entries(repo: Path, ref: str = "HEAD", max_count: int = 100) -> list[ReflogEntry]:
    proc = run(
        ["reflog", "show", f"-{max_count}", "--format=%gd\x1f%h\x1f%gs", ref],
        cwd=repo,
        check=False,
    )
    entries: list[ReflogEntry] = []
    if proc.returncode != 0:
        return entries
    for line in proc.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            entries.append(ReflogEntry(selector=parts[0], short_hash=parts[1], action=parts[2]))
    return entries


_TIMESTAMP_RE = re.compile(r"@\{(\d+)\}$")


@dataclass
class ReflogEvent:
    timestamp: int
    ref: str
    short_hash: str
    action: str


def reflog_events(repo: Path, refs: list[str], max_count: int = 100) -> list[ReflogEvent]:
    """여러 ref의 reflog를 모아 실제 발생 시각 순으로 정렬한 이벤트 목록을 반환한다.

    `git branch <이름> <해시>` 처럼 체크아웃 없이 만든 브랜치의 "Created from" 기록은
    HEAD가 아니라 그 브랜치 자신의 reflog에 남기 때문에, 여러 ref에 걸친 사건의
    선후 관계를 판단하려면 각 ref의 reflog를 실제 타임스탬프 기준으로 합쳐야 한다.
    """
    events: list[ReflogEvent] = []
    for ref in refs:
        proc = run(
            ["reflog", "show", f"-{max_count}", "--date=unix", "--format=%gd\x1f%h\x1f%gs", ref],
            cwd=repo,
            check=False,
        )
        if proc.returncode != 0:
            continue
        for line in proc.stdout.splitlines():
            parts = line.split("\x1f")
            if len(parts) != 3:
                continue
            selector, short_hash, action = parts
            match = _TIMESTAMP_RE.search(selector)
            if not match:
                continue
            events.append(ReflogEvent(timestamp=int(match.group(1)), ref=ref, short_hash=short_hash, action=action))
    events.sort(key=lambda e: e.timestamp)
    return events


def bare_ref(bare_repo: Path, ref: str) -> Optional[str]:
    return rev_parse(bare_repo, ref)


def bare_reflog(bare_repo: Path, ref: str = "refs/heads/main", max_count: int = 40) -> str:
    return reflog(bare_repo, ref=ref, max_count=max_count)
