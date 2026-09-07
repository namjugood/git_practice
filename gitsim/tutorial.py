"""git을 처음 쓰는 사람을 위한 단계별 가이드 튜토리얼.

시나리오와 달리 "사고"를 미리 만들어두지 않고, 학습자가 직접 하나씩 명령을
실행하며 진행 상황을 `gitsim learn check` 로 확인받는 방식이다.

일부 단계("compose" 모드)는 일부러 바로 실행 가능한 완성된 명령을 주지 않는다.
그대로 복사-붙여넣기만 하면 손에 남는 게 없기 때문에, 이름/이메일/커밋 메시지/
브랜치 이름처럼 의미가 있는 값은 학습자가 직접 채워 넣거나 지어내야 다음 단계로
넘어갈 수 있게 만들었다.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from gitsim import gitutil as g
from gitsim.workspace import Workspace, create_workspace, list_workspaces, point_current, resolve_workspace

TUTORIAL_ID = "tutorial"

INTRO_TEXT = """
처음이시군요! git도 터미널도 낯설어도 전혀 문제 없습니다. 아래 순서대로만 따라오세요.

[1] 터미널이 뭔가요?
    글자로 명령을 입력해서 컴퓨터에게 작업을 시키는 화면입니다.
    - macOS: Spotlight(Cmd+Space)에서 "터미널(Terminal)" 검색 후 실행
    - Windows: 시작 메뉴에서 "PowerShell" 검색 후 실행
    - VS Code를 쓰고 있다면: 상단 메뉴 Terminal > New Terminal

[2] git이 뭔가요?
    파일이 바뀐 역사를 기록해두었다가, 언제든 예전 상태로 되돌리거나 여러 사람의
    작업 내용을 합칠 수 있게 해주는 도구입니다. 그 기록이 저장되는 폴더를
    "저장소(repository)"라고 부릅니다.

[3] 앞으로 어떻게 진행되나요?
    단계 중 일부는 그대로 복사해서 붙여넣으면 바로 실행되는 완성된 명령을
    보여줍니다. 하지만 이름, 이메일, 커밋 메시지, 브랜치 이름처럼 "직접 정해야
    하는 값"이 필요한 단계는 일부러 빈칸/설명만 드립니다. 그대로 복사하면
    손에 남는 게 없기 때문입니다 — 명령의 형태를 보고 실제 값을 채워서 스스로
    입력해보세요. 완료했는지는 `gitsim learn check` 로 확인합니다.

[4] 시작하기 전에 딱 한 번만
    터미널을 열고, 아래 명령으로 이 프로젝트를 설치해서 `gitsim` 명령을
    바로 쓸 수 있게 해두세요. (프로젝트 폴더 안에서 한 번만 실행하면 됩니다)

      pip install -e .

    이제 아래 STEP 1부터 순서대로 진행하면 됩니다.
""".strip()


@dataclass
class Step:
    key: str
    title: str
    mode: str  # "template" (그대로 실행 가능한 완성 명령) / "compose" (직접 채워 넣어야 함)
    explain: str
    command_hint: str
    check: Callable[[Workspace], bool]
    on_enter: Optional[Callable[[Workspace], None]] = None
    on_success: Optional[Callable[[Workspace], None]] = None
    diagnose: Optional[Callable[[Workspace], str]] = None


PLACEHOLDER_NAME = "본인 이름"
PLACEHOLDER_EMAIL = "본인 이메일"


def _has_commit(ws: Workspace) -> bool:
    return g.rev_parse(ws.repo_dir, "HEAD") is not None


def _diagnose_init(ws: Workspace) -> str:
    if not (ws.repo_dir / ".git").exists():
        return (
            f"아직 이 폴더가 git 저장소로 초기화되지 않았습니다. 지금 명령을 실행한 폴더가\n"
            f"  {ws.repo_dir}\n"
            f"가 맞는지 확인한 뒤 `git init -b main` 을 실행하세요."
        )
    branch = g.current_branch(ws.repo_dir)
    return f"저장소는 만들어졌지만 현재 브랜치 이름이 'main'이 아니라 '{branch}' 입니다. `git branch -m main` 으로 이름을 바꾸세요."


def _identity_configured(ws: Workspace) -> bool:
    # --local 로 한정해서, 이미 컴퓨터에 전역(global) 설정이 있는 사람도 이 저장소에서는
    # 반드시 직접 한 번 입력하도록 만든다 (전역 설정을 물려받아 그냥 통과되는 것을 방지).
    name = g.run(["config", "--local", "user.name"], cwd=ws.repo_dir, check=False).stdout.strip()
    email = g.run(["config", "--local", "user.email"], cwd=ws.repo_dir, check=False).stdout.strip()
    if not name or not email:
        return False
    if PLACEHOLDER_NAME in name or PLACEHOLDER_EMAIL in email:
        return False
    return "@" in email


def _diagnose_identity(ws: Workspace) -> str:
    name = g.run(["config", "--local", "user.name"], cwd=ws.repo_dir, check=False).stdout.strip()
    email = g.run(["config", "--local", "user.email"], cwd=ws.repo_dir, check=False).stdout.strip()
    if not name or not email:
        return (
            f"이 저장소에는 아직 이름/이메일이 설정되어 있지 않습니다 (지금 값: 이름='{name}', 이메일='{email}').\n"
            "`git config user.name`, `git config user.email` 을 이 저장소 안에서 실행했는지 확인하세요."
        )
    if PLACEHOLDER_NAME in name or PLACEHOLDER_EMAIL in email:
        return f"예시 문구가 그대로 남아있습니다 (이름='{name}', 이메일='{email}'). 실제 본인 이름/이메일로 바꿔서 다시 입력하세요."
    if "@" not in email:
        return f"이메일에 '@' 가 없습니다 (지금 값: '{email}'). 이메일 형식으로 다시 입력하세요."
    return f"현재 설정된 값은 이름='{name}', 이메일='{email}' 입니다. 정상으로 보이는데도 실패한다면 `gitsim learn check` 를 다시 실행해보세요."


def _diagnose_first_commit(ws: Workspace) -> str:
    status = g.status_porcelain(ws.repo_dir)
    if status.strip():
        return (
            "아직 커밋되지 않은 변경 사항이 있습니다:\n"
            f"{status}\n"
            "`git add <파일 이름>` 으로 스테이징한 뒤 `git commit -m \"메시지\"` 를 실행하세요."
        )
    return "아직 이 저장소에 커밋이 하나도 없습니다. 파일을 만들고 `git add`, `git commit -m \"메시지\"` 를 실행하세요."


def _on_practice_branch(ws: Workspace) -> bool:
    branch = g.current_branch(ws.repo_dir)
    return bool(branch) and branch != "main"


def _diagnose_branch(ws: Workspace) -> str:
    branch = g.current_branch(ws.repo_dir)
    if branch == "main":
        return "아직 main 브랜치에 그대로 있습니다. `git checkout -b <원하는 브랜치 이름>` 으로 새 브랜치를 만들고 그 브랜치로 이동해야 합니다."
    if not branch:
        return "지금 어떤 브랜치에도 있지 않은 상태(detached HEAD)로 보입니다. `git checkout -b <원하는 브랜치 이름>` 을 다시 실행하세요."
    return f"현재 브랜치는 '{branch}' 로 보이는데도 실패했습니다. `gitsim learn check` 를 다시 실행해보세요."


def _remember_branch(ws: Workspace) -> None:
    branch = g.current_branch(ws.repo_dir)
    if branch:
        ws.save_meta(practice_branch=branch)


def _branch_ahead_of_main(ws: Workspace) -> bool:
    branch = ws.get("practice_branch")
    if not branch:
        return False
    branch_tip = g.rev_parse(ws.repo_dir, branch)
    main_tip = g.rev_parse(ws.repo_dir, "main")
    if not branch_tip or not main_tip or branch_tip == main_tip:
        return False
    return g.is_ancestor(ws.repo_dir, main_tip, branch_tip)


def _diagnose_branch_commit(ws: Workspace) -> str:
    remembered = ws.get("practice_branch")
    current = g.current_branch(ws.repo_dir)
    if not remembered:
        return "3번 단계에서 만든 브랜치 이름이 기록되어 있지 않습니다. `gitsim learn reset` 으로 처음부터 다시 시작해야 할 수 있습니다."
    if current != remembered:
        return (
            f"3번 단계에서 만든 브랜치는 '{remembered}' 인데, 지금 체크아웃되어 있는 브랜치는 "
            f"'{current}' 입니다. `git checkout {remembered}` 로 그 브랜치로 돌아가서 커밋하세요."
        )
    branch_tip = g.rev_parse(ws.repo_dir, remembered)
    main_tip = g.rev_parse(ws.repo_dir, "main")
    if branch_tip == main_tip:
        return f"'{remembered}' 브랜치가 main과 똑같아서 아직 새 커밋이 없는 것으로 보입니다. 파일을 수정/생성하고 `git add`, `git commit -m \"메시지\"` 를 실행하세요."
    return f"'{remembered}' 브랜치에 커밋은 있는 것 같은데도 실패했습니다. `gitsim learn check` 를 다시 실행해보세요."


def _merged(ws: Workspace) -> bool:
    branch = ws.get("practice_branch")
    if not branch:
        return False
    branch_tip = g.rev_parse(ws.repo_dir, branch)
    main_tip = g.rev_parse(ws.repo_dir, "main")
    if not branch_tip or not main_tip:
        return False
    return g.is_ancestor(ws.repo_dir, branch_tip, main_tip)


def _diagnose_merge(ws: Workspace) -> str:
    branch = ws.get("practice_branch") or "<앞에서 만든 브랜치>"
    current = g.current_branch(ws.repo_dir)
    if current != "main":
        return f"지금 브랜치가 'main'이 아니라 '{current}' 입니다. 먼저 `git checkout main` 을 실행하세요."
    return f"main이 아직 '{branch}' 브랜치를 포함하고 있지 않습니다. `git merge {branch}` 를 실행하세요."


def _remote_ok(ws: Workspace) -> bool:
    remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
    local_main = g.rev_parse(ws.repo_dir, "main")
    remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
    return bool(remote_main) and remote_main == local_main and "origin" in remotes


def _diagnose_remote(ws: Workspace) -> str:
    remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
    if "origin" not in remotes:
        return f"'origin' 이라는 이름의 원격이 아직 등록되지 않았습니다. `git remote add origin {ws.remote_dir}` 을 실행하세요."
    remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
    if not remote_main:
        return "origin은 등록되었지만 아직 main이 push되지 않았습니다. `git push -u origin main` 을 실행하세요."
    local_main = g.rev_parse(ws.repo_dir, "main")
    if remote_main != local_main:
        return "원격의 main이 로컬 main과 다릅니다. `git push -u origin main` 을 다시 실행해보세요."
    return "origin 등록과 push까지는 되어 보이는데도 실패했습니다. `gitsim learn check` 를 다시 실행해보세요."


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


def _diagnose_pull(ws: Workspace) -> str:
    return "아직 동료의 커밋(teammate_note.txt)을 받아오지 않은 것 같습니다. `git pull origin main` 을 실행하세요."


STEPS: list[Step] = [
    Step(
        key="init",
        title="0. 저장소 만들기 (git init)",
        mode="template",
        explain=(
            "git으로 무언가를 관리하려면 먼저 그 폴더를 'git 저장소'로 만들어야 합니다.\n"
            "(컴퓨터 설정에 따라 기본 브랜치 이름이 'master'가 될 수도 있어서, 이 튜토리얼에서는\n"
            "'main'으로 이름을 고정하는 옵션(-b main)을 함께 사용합니다)"
        ),
        command_hint="git init -b main",
        check=lambda ws: (ws.repo_dir / ".git").exists() and g.current_branch(ws.repo_dir) == "main",
        diagnose=_diagnose_init,
    ),
    Step(
        key="identity",
        title="1. 커밋 작성자 정보 설정하기 (git config)",
        mode="compose",
        explain=(
            "모든 커밋에는 '누가 만들었는지' 기록이 남습니다. 아래는 명령의 형태만\n"
            "보여드립니다 — 따옴표 안 문구를 실제 본인 이름/이메일로 바꿔서 두 줄 모두\n"
            "직접 입력하세요. 예시 문구를 그대로 실행하면 통과되지 않습니다."
        ),
        command_hint=(
            f'git config user.name "{PLACEHOLDER_NAME}"          (← 이 문구를 실제 이름으로 바꿔서 입력)\n'
            f'  git config user.email "{PLACEHOLDER_EMAIL}@example.com"  (← 실제 이메일로 바꿔서 입력)'
        ),
        check=_identity_configured,
        diagnose=_diagnose_identity,
    ),
    Step(
        key="first-commit",
        title="2. 첫 커밋 만들기 (add, commit)",
        mode="compose",
        explain=(
            "git은 파일을 '스테이징(add)'한 뒤 '커밋(commit)'해야 변경 이력으로 저장합니다.\n"
            "아무 이름으로나 텍스트 파일을 하나 직접 만들고 원하는 내용을 적어보세요.\n"
            "그 다음 아래 형태의 명령으로 스테이징하고, 커밋 메시지도 직접 지어서 커밋하세요."
        ),
        command_hint=(
            "git add <방금 만든 파일 이름>\n"
            '  git commit -m "<자유롭게 지은 커밋 메시지>"'
        ),
        check=_has_commit,
        diagnose=_diagnose_first_commit,
    ),
    Step(
        key="branch",
        title="3. 브랜치 만들고 이동하기",
        mode="compose",
        explain=(
            "브랜치는 독립된 작업 공간입니다. 실험적인 작업을 할 때 main을 건드리지 않고\n"
            "새 브랜치에서 작업할 수 있습니다. 브랜치 이름을 원하는 대로 하나 지어보세요."
        ),
        command_hint="git checkout -b <원하는 브랜치 이름>",
        check=_on_practice_branch,
        on_success=_remember_branch,
        diagnose=_diagnose_branch,
    ),
    Step(
        key="branch-commit",
        title="4. 브랜치에서 커밋 추가하기",
        mode="compose",
        explain="지금 브랜치 위에서 파일을 수정하거나 새로 만들고, 커밋 메시지도 직접 지어서 커밋 하나를 추가하세요.",
        command_hint=(
            "git add <파일 이름>\n"
            '  git commit -m "<자유롭게 지은 커밋 메시지>"'
        ),
        check=_branch_ahead_of_main,
        diagnose=_diagnose_branch_commit,
    ),
    Step(
        key="merge",
        title="5. main으로 돌아와 병합하기 (merge)",
        mode="template",
        explain="main으로 돌아가서 방금 만든 브랜치({practice_branch})의 작업을 병합해보세요.",
        command_hint="git checkout main\n  git merge {practice_branch}",
        check=_merged,
        diagnose=_diagnose_merge,
    ),
    Step(
        key="remote",
        title="6. 원격 저장소 연결하고 업로드하기 (remote, push)",
        mode="compose",
        explain=(
            "실무에서는 GitHub 같은 원격 저장소에 코드를 올려 협업합니다.\n"
            "이 튜토리얼에서는 아래 경로에 있는 로컬 저장소가 '원격 저장소' 역할을 합니다.\n"
            "\n"
            "    원격 저장소 경로: {remote_dir}\n"
            "\n"
            "이 경로를 사용해서, origin이라는 이름으로 원격을 등록하고 push 하는 명령을\n"
            "직접 작성해보세요. (형태: git remote add <이름> <경로>, 그 다음 git push -u <이름> main)"
        ),
        command_hint="git remote add origin <위에 적힌 경로를 그대로 입력>\n  git push -u origin main",
        check=_remote_ok,
        on_enter=lambda ws: g.init_bare(ws.remote_dir) if not ws.remote_dir.exists() else None,
        diagnose=_diagnose_remote,
    ),
    Step(
        key="pull",
        title="7. 원격의 변경 사항 받아오기 (fetch/pull)",
        mode="template",
        explain=(
            "방금 동료가 원격 저장소에 teammate_note.txt 파일을 추가하고 push 했습니다.\n"
            "당신의 로컬 저장소에는 아직 이 파일이 없습니다. pull로 받아오세요."
        ),
        command_hint="git pull origin main",
        check=_pulled,
        on_enter=_inject_teammate_commit,
        diagnose=_diagnose_pull,
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
    point_current(ws)
    return ws


def get_or_create(base_dir: Optional[Path] = None) -> Workspace:
    try:
        ws = resolve_workspace(None, Path.cwd())
        if ws.scenario_id == TUTORIAL_ID and not ws.get("completed"):
            point_current(ws)
            return ws
    except FileNotFoundError:
        pass
    existing = _find_active(base_dir)
    if existing:
        point_current(existing)
        return existing
    return start_new(base_dir)


def current_step_index(ws: Workspace) -> int:
    return int(ws.get("current_step", 0))


def _ensure_entered(ws: Workspace, step: Step) -> None:
    if step.on_enter and not ws.get(f"entered_{step.key}"):
        step.on_enter(ws)
        ws.save_meta(**{f"entered_{step.key}": True})


def _fill(ws: Workspace, text: str) -> str:
    return text.replace("{remote_dir}", str(ws.remote_dir)).replace(
        "{practice_branch}", ws.get("practice_branch") or "<앞에서 만든 브랜치>"
    )


def _step_block(ws: Workspace, idx: int, step: Step) -> str:
    hint = _fill(ws, step.command_hint)
    explain = _fill(ws, step.explain)
    if step.mode == "template":
        body = f"  아래 명령을 그대로 입력하세요 (한 줄씩 따로 입력해도 됩니다):\n\n  {hint}"
    else:
        body = (
            f"  아래는 그대로 실행되는 완성된 명령이 아니라 '형태'입니다. 예시로 채워진 값이나\n"
            f"  <...> 표시된 부분을 직접 정한 실제 값으로 바꿔서, 손으로 입력해보세요:\n\n  {hint}"
        )
    return f"""
STEP {idx + 1}/{len(STEPS)}: {step.title}

[먼저 확인하세요] 지금 터미널이 연습용 폴더에 있나요?
  cd ~/.gitsim/current
  (위 경로로 이동이 안 되면, 아래 실제 경로로 대신 이동하세요)
  실제 경로: {ws.repo_dir}

{explain}

{body}

다 입력했다면 이 명령으로 확인하세요: gitsim learn check
""".strip()


def describe_current_step(ws: Workspace, show_intro: bool = False) -> str:
    point_current(ws)
    idx = current_step_index(ws)
    prefix = ""
    if show_intro or (idx == 0 and not ws.get("intro_shown")):
        prefix = INTRO_TEXT + "\n\n"
        ws.save_meta(intro_shown=True)

    if idx >= len(STEPS):
        return prefix + (
            "모든 튜토리얼 단계를 완료했습니다! 🎉\n"
            "이제 `gitsim list` 로 실무 시나리오 목록을 확인하고 `gitsim start <시나리오id>` 로 "
            "실전 연습을 시작해보세요."
        )
    step = STEPS[idx]
    _ensure_entered(ws, step)
    return prefix + _step_block(ws, idx, step)


def check_current_step(ws: Workspace) -> tuple[bool, str]:
    point_current(ws)
    idx = current_step_index(ws)
    if idx >= len(STEPS):
        return True, "이미 모든 단계를 완료했습니다."
    step = STEPS[idx]
    _ensure_entered(ws, step)
    if step.check(ws):
        if step.on_success:
            step.on_success(ws)
        ws.save_meta(current_step=idx + 1)
        if idx + 1 >= len(STEPS):
            ws.save_meta(completed=True)
        return True, f"'{step.title}' 단계를 완료했습니다!"

    if step.diagnose:
        detail = step.diagnose(ws)
    elif step.mode == "compose":
        detail = "예시 문구를 그대로 실행하지 않았는지, 실제 값으로 바꿔서 입력했는지 확인해보세요."
    else:
        detail = "위에 안내된 명령을 실행해보세요."
    return False, f"'{step.title}' 단계가 아직 완료되지 않았습니다.\n\n[진단] {detail}"


def reset_tutorial(base_dir: Optional[Path] = None) -> Workspace:
    existing = _find_active(base_dir)
    if existing and existing.path.exists():
        shutil.rmtree(existing.path)
    return start_new(base_dir)
