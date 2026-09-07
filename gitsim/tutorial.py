"""git을 처음 쓰는 사람을 위한 단계별 가이드 튜토리얼.

시나리오와 달리 "사고"를 미리 만들어두지 않고, 학습자가 직접 하나씩 명령을
실행하며 진행 상황을 `gitsim learn check` 로 확인받는 방식이다.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from gitsim import gitutil as g
from gitsim.workspace import Workspace, create_workspace, list_workspaces, resolve_workspace

TUTORIAL_ID = "tutorial"


@dataclass
class Step:
    key: str
    title: str
    explain: str
    command_hint: str
    check: Callable[[Workspace], bool]
    on_enter: Optional[Callable[[Workspace], None]] = None


def _has_commit(ws: Workspace) -> bool:
    return g.rev_parse(ws.repo_dir, "HEAD") is not None


def _branch_ahead_of_main(ws: Workspace) -> bool:
    branch_tip = g.rev_parse(ws.repo_dir, "practice-branch")
    main_tip = g.rev_parse(ws.repo_dir, "main")
    if not branch_tip or not main_tip or branch_tip == main_tip:
        return False
    return g.is_ancestor(ws.repo_dir, main_tip, branch_tip)


def _on_branch(ws: Workspace) -> bool:
    return g.current_branch(ws.repo_dir) == "practice-branch"


def _merged(ws: Workspace) -> bool:
    branch_tip = g.rev_parse(ws.repo_dir, "practice-branch")
    main_tip = g.rev_parse(ws.repo_dir, "main")
    if not branch_tip or not main_tip:
        return False
    return g.is_ancestor(ws.repo_dir, branch_tip, main_tip)


def _remote_ok(ws: Workspace) -> bool:
    remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
    local_main = g.rev_parse(ws.repo_dir, "main")
    remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
    return bool(remote_main) and remote_main == local_main and "origin" in remotes


def _inject_teammate_commit(ws: Workspace) -> None:
    if ws.get("teammate_marker_commit"):
        return
    tmp_clone = ws.path / "_tutorial_teammate_tmp"
    if tmp_clone.exists():
        shutil.rmtree(tmp_clone)
    g.clone(ws.remote_dir, tmp_clone)
    g.write_file(tmp_clone, "teammate_note.txt", "동료가 원격에 추가한 파일입니다.\n")
    g.add_all(tmp_clone)
    marker_commit = g.commit(tmp_clone, "동료: teammate_note.txt 추가")
    g.run(["push", "origin", "main"], cwd=tmp_clone)
    shutil.rmtree(tmp_clone)
    ws.save_meta(teammate_marker_commit=marker_commit)


def _pulled(ws: Workspace) -> bool:
    marker_commit = ws.get("teammate_marker_commit")
    if not marker_commit:
        return False
    local_main = g.rev_parse(ws.repo_dir, "main")
    return bool(local_main) and g.is_ancestor(ws.repo_dir, marker_commit, local_main)


STEPS: list[Step] = [
    Step(
        key="init",
        title="0. 저장소 만들기 (git init)",
        explain=(
            "git으로 무언가를 관리하려면 먼저 그 폴더를 'git 저장소'로 만들어야 합니다.\n"
            "이 워크스페이스의 repo/ 폴더로 이동해서 저장소를 초기화하세요."
        ),
        command_hint="git init",
        check=lambda ws: (ws.repo_dir / ".git").exists(),
    ),
    Step(
        key="first-commit",
        title="1. 첫 커밋 만들기 (add, commit)",
        explain=(
            "git은 파일을 '스테이징(add)'한 뒤 '커밋(commit)'해야 변경 이력으로 저장합니다.\n"
            "아무 파일이나 하나 만들고, 내용을 적은 뒤 커밋해보세요."
        ),
        command_hint='echo "hello git" > hello.txt && git add hello.txt && git commit -m "첫 커밋"',
        check=_has_commit,
    ),
    Step(
        key="branch",
        title="2. 브랜치 만들고 이동하기",
        explain=(
            "브랜치는 독립된 작업 공간입니다. 실험적인 작업을 할 때 main을 건드리지 않고\n"
            "새 브랜치에서 작업할 수 있습니다."
        ),
        command_hint="git checkout -b practice-branch",
        check=_on_branch,
    ),
    Step(
        key="branch-commit",
        title="3. 브랜치에서 커밋 추가하기",
        explain="practice-branch 위에서 파일을 수정하거나 새로 만들고 커밋하세요.",
        command_hint='echo "branch work" >> hello.txt && git add -A && git commit -m "브랜치에서 작업"',
        check=_branch_ahead_of_main,
    ),
    Step(
        key="merge",
        title="4. main으로 돌아와 병합하기 (merge)",
        explain="main으로 돌아가서 practice-branch의 작업을 병합해보세요.",
        command_hint="git checkout main && git merge practice-branch",
        check=_merged,
    ),
    Step(
        key="remote",
        title="5. 원격 저장소 연결하고 업로드하기 (remote, push)",
        explain=(
            "실무에서는 GitHub 같은 원격 저장소에 코드를 올려 협업합니다.\n"
            "이 튜토리얼에서는 워크스페이스 안의 remote.git 폴더가 '원격 저장소' 역할을 합니다.\n"
            f"아래 경로를 origin으로 등록하고 push 해보세요.\n  {{remote_dir}}"
        ),
        command_hint="git remote add origin <위 경로> && git push -u origin main",
        check=_remote_ok,
        on_enter=lambda ws: g.init_bare(ws.remote_dir) if not ws.remote_dir.exists() else None,
    ),
    Step(
        key="pull",
        title="6. 원격의 변경 사항 받아오기 (fetch/pull)",
        explain=(
            "방금 동료가 원격 저장소에 teammate_note.txt 파일을 추가하고 push 했습니다.\n"
            "당신의 로컬 저장소에는 아직 이 파일이 없습니다. pull로 받아오세요."
        ),
        command_hint="git pull origin main",
        check=_pulled,
        on_enter=_inject_teammate_commit,
    ),
]


def _tutorial_dirs_ready(ws: Workspace) -> None:
    ws.repo_dir.mkdir(parents=True, exist_ok=True)


def _find_active(base_dir: Optional[Path] = None) -> Optional[Workspace]:
    for ws in list_workspaces(base_dir):
        if ws.scenario_id == TUTORIAL_ID and not ws.get("completed"):
            return ws
    return None


def start_new(base_dir: Optional[Path] = None) -> Workspace:
    ws = create_workspace(TUTORIAL_ID, base_dir=base_dir)
    _tutorial_dirs_ready(ws)
    ws.save_meta(current_step=0)
    return ws


def get_or_create(base_dir: Optional[Path] = None) -> Workspace:
    try:
        ws = resolve_workspace(None, Path.cwd())
        if ws.scenario_id == TUTORIAL_ID and not ws.get("completed"):
            return ws
    except FileNotFoundError:
        pass
    existing = _find_active(base_dir)
    if existing:
        return existing
    return start_new(base_dir)


def current_step_index(ws: Workspace) -> int:
    return int(ws.get("current_step", 0))


def _ensure_entered(ws: Workspace, step: Step) -> None:
    if step.on_enter and not ws.get(f"entered_{step.key}"):
        step.on_enter(ws)
        ws.save_meta(**{f"entered_{step.key}": True})


def describe_current_step(ws: Workspace) -> str:
    idx = current_step_index(ws)
    if idx >= len(STEPS):
        return (
            "\n모든 튜토리얼 단계를 완료했습니다! 🎉\n"
            "이제 `gitsim list` 로 실무 시나리오 목록을 확인하고 `gitsim start <시나리오id>` 로 "
            "실전 연습을 시작해보세요."
        )
    step = STEPS[idx]
    _ensure_entered(ws, step)
    hint = step.command_hint.replace("{remote_dir}", str(ws.remote_dir))
    explain = step.explain.replace("{remote_dir}", str(ws.remote_dir))
    return f"""
STEP {idx + 1}/{len(STEPS)}: {step.title}

{explain}

  예시 명령: {hint}

작업 위치: {ws.repo_dir}

완료했다면 `gitsim learn check` 로 확인하세요.
""".strip()


def check_current_step(ws: Workspace) -> tuple[bool, str]:
    idx = current_step_index(ws)
    if idx >= len(STEPS):
        return True, "이미 모든 단계를 완료했습니다."
    step = STEPS[idx]
    _ensure_entered(ws, step)
    if step.check(ws):
        ws.save_meta(current_step=idx + 1)
        if idx + 1 >= len(STEPS):
            ws.save_meta(completed=True)
        return True, f"'{step.title}' 단계를 완료했습니다!"
    return False, f"'{step.title}' 단계가 아직 완료되지 않았습니다. 안내된 명령을 실행해보세요."


def reset_tutorial(base_dir: Optional[Path] = None) -> Workspace:
    existing = _find_active(base_dir)
    if existing and existing.path.exists():
        shutil.rmtree(existing.path)
    return start_new(base_dir)
