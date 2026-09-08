"""실제 `git` 바이너리를 감싸는 얇은 래퍼.

이 모듈은 시뮬레이터가 실제 git 저장소(로컬 워킹 카피 + 로컬 bare 저장소를
"원격"으로 사용)를 만들고 검사하는 데 필요한 최소한의 기능만 제공한다.
전부 subprocess로 실제 git 명령을 호출하므로, 여기서 벌어지는 모든 일은
사용자가 터미널에서 똑같이 `git ...` 명령으로 재현할 수 있는 진짜 git 상태다.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gitsim.i18n import t as _


def _clear_readonly_and_retry(func, target_path, exc) -> None:
    # git은 .git/objects/ 안의 오브젝트 파일을 읽기 전용으로 만들어 실수로 내용이
    # 바뀌는 것을 막는다. Windows에서는 파일 자체가 읽기 전용이면 그 파일이 든
    # 폴더 권한과 무관하게 삭제가 거부되므로, 지우기 전에 속성을 먼저 풀어줘야 한다.
    try:
        os.chmod(target_path, stat.S_IWRITE)
        func(target_path)
    except OSError:
        pass  # 워크스페이스 정리는 최선을 다하는 수준이면 충분하다.


def force_rmtree(path: Path) -> None:
    """git 저장소가 들어있는 디렉터리를 안전하게(읽기 전용 오브젝트 포함) 지운다."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_readonly_and_retry)
    else:
        shutil.rmtree(path, onerror=lambda func, p, exc_info: _clear_readonly_and_retry(func, p, exc_info[1]))


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
    # git은 커밋 메시지/reflog 등을 항상 UTF-8로 저장하고 그대로 stdout에 내보낸다.
    # `text=True`만 쓰면 파이썬이 OS 기본 코드페이지로 디코딩하는데, 한국어 Windows는
    # 기본이 cp949라서 한글이 든 출력에서 UnicodeDecodeError가 난다. 인코딩을 명시해서
    # 항상 UTF-8로 디코딩하고, 혹시 깨진 바이트가 있어도 죽지 않도록 대체 문자로 넘어간다.
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
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


def clone(src: "Path | str", dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["clone", "-q", str(src), str(dest)])
    configure_identity(dest)


def clone_and_checkout(src: "Path | str", dest: Path, branch: str) -> None:
    """`src` 를 클론한 뒤, 로컬 브랜치 `branch` 를 원격의 같은 브랜치로 맞춰 체크아웃한다.

    `git clone` 은 기본 브랜치만 체크아웃하므로, 연습 전용 브랜치(`practice/...`)로
    바로 이동하려면 이 함수를 쓴다. `tutorial.py` 처럼 refspec을 재매핑하지 *않은*
    저장소(즉 원격의 실제 브랜치 이름을 그대로 쓰는 저장소)에서만 사용한다 — refspec을
    재매핑한 시나리오 저장소의 클론에는 대신 `clone_practice_remote()` 를 쓴다.
    """
    clone(src, dest)
    run(["checkout", "-B", branch, f"origin/{branch}"], cwd=dest)


def remote_branch_tip(repo: Path, branch: str) -> Optional[str]:
    """`origin` 에서 `branch` 를 fetch 한 뒤, 그 원격 브랜치의 현재 커밋 해시를 돌려준다.

    실제 원격(예: GitHub)은 로컬 파일 시스템으로 직접 들여다볼 수 없으므로, bare
    저장소 파일을 직접 읽던 예전 방식 대신 항상 fetch 로 최신 상태를 받아온 뒤
    로컬에 생긴 원격 추적 브랜치(`origin/<branch>`)를 확인한다.

    주의: `setup_practice_remote`/`clone_practice_remote` 로 fetch refspec을
    `+refs/heads/<branch>:refs/remotes/origin/main` 으로 재매핑해둔 저장소에는 쓸 수
    없다 — 그런 저장소에서는 `branch` 의 내용이 `origin/<branch>` 가 아니라 항상
    `origin/main` 에 들어오므로 이 함수는 항상 None을 반환한다. 그런 저장소에서는
    대신 `run(["fetch", "origin"], ...)` 뒤 `rev_parse(repo, "origin/main")` 을 쓴다
    (6개 시나리오의 check()/diagnose() 가 이렇게 한다). 이 함수는 refspec을 그대로 둔
    저장소(현재는 tutorial.py)에서만 쓰도록 한다.
    """
    run(["fetch", "origin", branch], cwd=repo, check=False)
    return rev_parse(repo, f"origin/{branch}")


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


def setup_practice_remote(repo_dir: Path, branch: str, remote_url: str) -> None:
    """`repo_dir`에 실제 원격을 `origin`으로 등록하고(로컬 `main`이 실제로는 원격의
    `branch`(예: `practice/<워크스페이스>`)를 가리키도록 refspec을 다시 매핑한 뒤), 지금까지
    쌓인 커밋을 그 브랜치로 push한다.

    이렇게 하면 시나리오 코드와 안내 문구에 그대로 남아 있는 `git push origin main`,
    `origin/main` 같은 표현이 실제로는 이 워크스페이스 전용 브랜치에서 동작하게 되어,
    여러 시나리오/여러 번의 시도가 같은 원격 저장소를 공유해도 서로 덮어쓰지 않는다.

    refspec을 등록하기 전에 push하면 그냥 로컬 `main` 이름 그대로 원격에 올라가 버리므로,
    두 단계는 항상 이 순서로 함께 일어나야 한다 — 그래서 호출자가 순서를 따로 신경 쓰지
    않도록 이 함수 안에서 최초 push까지 함께 처리한다.
    """
    run(["remote", "add", "origin", remote_url], cwd=repo_dir)
    run(["config", "remote.origin.fetch", f"+refs/heads/{branch}:refs/remotes/origin/main"], cwd=repo_dir)
    run(["config", "remote.origin.push", f"refs/heads/main:refs/heads/{branch}"], cwd=repo_dir)
    run(["push", "-u", "origin", "main"], cwd=repo_dir)


def clone_practice_remote(remote_url: str, dest: Path, branch: str) -> None:
    """"동료의 로컬 클론"이 원격의 연습 전용 브랜치를 `main`으로 체크아웃하도록 만든다.

    등록된 원격 저장소에는 이전에 연습했던 다른 워크스페이스들의 `practice/*` 브랜치도
    계속 쌓여 있을 수 있으므로(실수까지 포함해 이력을 절대 지우지 않는 설계), 전체
    저장소를 그대로 clone하면 매번 그 무관한 히스토리를 전부 내려받게 된다.
    `--single-branch --branch <branch>` 로 이번 워크스페이스가 쓰는 브랜치만 받는다.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["clone", "-q", "--single-branch", "--branch", branch, remote_url, str(dest)])
    configure_identity(dest)
    run(["config", "remote.origin.fetch", f"+refs/heads/{branch}:refs/remotes/origin/main"], cwd=dest)
    run(["config", "remote.origin.push", f"refs/heads/main:refs/heads/{branch}"], cwd=dest)
    run(["fetch", "origin"], cwd=dest, check=False)
    run(["checkout", "-B", "main", "origin/main"], cwd=dest, check=False)
