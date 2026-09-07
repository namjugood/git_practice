"""git을 처음 쓰는 사람을 위한 단계별 가이드 튜토리얼.

시나리오와 달리 "사고"를 미리 만들어두지 않고, 학습자가 직접 하나씩 명령을
실행하며 진행 상황을 `gitsim learn check` 로 확인받는 방식이다.

일부 단계("compose" 모드)는 일부러 바로 실행 가능한 완성된 명령을 주지 않는다.
그대로 복사-붙여넣기만 하면 손에 남는 게 없기 때문에, 이름/이메일/커밋 메시지/
브랜치 이름처럼 의미가 있는 값은 학습자가 직접 채워 넣거나 지어내야 다음 단계로
넘어갈 수 있게 만들었다.

화면에 보이는 모든 문구는 `gitsim/messages/ko/tutorial.py` 에 있고, 이 파일은
그 키를 참조만 한다 (다국어 지원을 위해 문구와 로직을 분리했다).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.workspace import Workspace, create_workspace, list_workspaces, point_current, resolve_workspace

TUTORIAL_ID = "tutorial"

PLACEHOLDER_NAME = _("tutorial.placeholder.name")
PLACEHOLDER_EMAIL = _("tutorial.placeholder.email")


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
    requires_main: bool = True


def _list_branches(ws: Workspace) -> list[str]:
    proc = g.run(["branch", "--format=%(refname:short)"], cwd=ws.repo_dir, check=False)
    return [b.strip() for b in proc.stdout.splitlines() if b.strip()]


def _require_main(ws: Workspace) -> Optional[str]:
    """'main' 브랜치가 존재하는지 확인한다.

    main이 없으면 이후 단계 대부분이 원인 불명으로 실패하기 때문에, 이 확인은
    (각 단계의 개별 진단이 아니라) `check_current_step` 이 모든 단계에 대해 공통
    선행 조건으로 딱 한 번 검사한다 — main이 사라진 문제는 그 사실을 발견한
    바로 다음 `gitsim learn check` 에서 즉시 드러나야지, 한참 뒤(예: merge/remote
    단계)에 가서야 알아채면 안 되기 때문이다.
    """
    if g.rev_parse(ws.repo_dir, "main") is not None:
        return None
    if g.current_branch(ws.repo_dir) == "main":
        # 아직 커밋이 하나도 없는 "unborn" 브랜치 상태다 (예: git init 직후).
        # main이라는 이름 자체는 맞게 잡혀 있으므로 문제가 아니다 — 커밋이
        # 없다는 사실 자체는 각 단계의 개별 check가 걸러낸다.
        return None
    branches = _list_branches(ws)
    current = g.current_branch(ws.repo_dir)
    branch_list = ", ".join(branches) if branches else _("tutorial.require_main.no_branch")
    return _(
        "tutorial.require_main",
        branch_list=branch_list,
        current=current or _("tutorial.require_main.unknown_position"),
    )


def _has_commit(ws: Workspace) -> bool:
    return g.rev_parse(ws.repo_dir, "HEAD") is not None


def _diagnose_init(ws: Workspace) -> str:
    if not (ws.repo_dir / ".git").exists():
        return _("tutorial.diagnose.init.not_repo", repo_dir=ws.repo_dir)
    branch = g.current_branch(ws.repo_dir)
    return _("tutorial.diagnose.init.wrong_branch", branch=branch)


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
        return _("tutorial.diagnose.identity.not_set", name=name, email=email)
    if PLACEHOLDER_NAME in name or PLACEHOLDER_EMAIL in email:
        return _("tutorial.diagnose.identity.placeholder", name=name, email=email)
    if "@" not in email:
        return _("tutorial.diagnose.identity.bad_email", email=email)
    return _("tutorial.diagnose.identity.looks_ok", name=name, email=email)


def _diagnose_first_commit(ws: Workspace) -> str:
    status = g.status_porcelain(ws.repo_dir)
    if status.strip():
        return _("tutorial.diagnose.first_commit.uncommitted", status=status)
    return _("tutorial.diagnose.first_commit.none")


def _on_practice_branch(ws: Workspace) -> bool:
    branch = g.current_branch(ws.repo_dir)
    return bool(branch) and branch != "main"


def _diagnose_branch(ws: Workspace) -> str:
    branch = g.current_branch(ws.repo_dir)
    if branch == "main":
        return _("tutorial.diagnose.branch.still_main")
    if not branch:
        return _("tutorial.diagnose.branch.detached")
    return _("tutorial.diagnose.branch.looks_ok", branch=branch)


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
        return _("tutorial.diagnose.branch_commit.no_remembered")
    if current != remembered:
        return _("tutorial.diagnose.branch_commit.wrong_branch", remembered=remembered, current=current)
    branch_tip = g.rev_parse(ws.repo_dir, remembered)
    main_tip = g.rev_parse(ws.repo_dir, "main")
    if branch_tip == main_tip:
        return _("tutorial.diagnose.branch_commit.no_new_commit", remembered=remembered)
    if not g.is_ancestor(ws.repo_dir, main_tip, branch_tip):
        return _("tutorial.diagnose.branch_commit.diverged", remembered=remembered)
    return _("tutorial.diagnose.branch_commit.looks_ok", remembered=remembered)


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
    branch = ws.get("practice_branch") or _("tutorial.fallback_branch_label")
    current = g.current_branch(ws.repo_dir)
    if current != "main":
        return _("tutorial.diagnose.merge.not_on_main", current=current)
    return _("tutorial.diagnose.merge.not_merged", branch=branch)


def _remote_ok(ws: Workspace) -> bool:
    remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
    local_main = g.rev_parse(ws.repo_dir, "main")
    remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
    return bool(remote_main) and remote_main == local_main and "origin" in remotes


def _diagnose_remote(ws: Workspace) -> str:
    remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
    if "origin" not in remotes:
        return _("tutorial.diagnose.remote.no_origin", remote_dir=ws.remote_dir)
    remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
    if not remote_main:
        return _("tutorial.diagnose.remote.not_pushed")
    local_main = g.rev_parse(ws.repo_dir, "main")
    if remote_main != local_main:
        return _("tutorial.diagnose.remote.mismatch")
    return _("tutorial.diagnose.remote.looks_ok")


def _inject_teammate_commit(ws: Workspace) -> None:
    if ws.get("teammate_marker_commit"):
        return
    tmp_clone = ws.path / "_tutorial_teammate_tmp"
    if tmp_clone.exists():
        g.force_rmtree(tmp_clone)
    g.clone(ws.remote_dir, tmp_clone)
    g.write_file(tmp_clone, "teammate_note.txt", "동료가 원격에 추가한 파일입니다.\n")
    g.add_all(tmp_clone)
    marker_commit = g.commit(tmp_clone, "동료: teammate_note.txt 추가")
    g.run(["push", "origin", "main"], cwd=tmp_clone)
    g.force_rmtree(tmp_clone)
    ws.save_meta(teammate_marker_commit=marker_commit)


def _pulled(ws: Workspace) -> bool:
    marker_commit = ws.get("teammate_marker_commit")
    if not marker_commit:
        return False
    local_main = g.rev_parse(ws.repo_dir, "main")
    return bool(local_main) and g.is_ancestor(ws.repo_dir, marker_commit, local_main)


def _diagnose_pull(ws: Workspace) -> str:
    return _("tutorial.diagnose.pull.not_pulled")


def _build_steps() -> list[Step]:
    return [
        Step(
            key="init",
            title=_("tutorial.step.init.title"),
            mode="template",
            explain=_("tutorial.step.init.explain"),
            command_hint=_("tutorial.step.init.command_hint"),
            check=lambda ws: (ws.repo_dir / ".git").exists() and g.current_branch(ws.repo_dir) == "main",
            diagnose=_diagnose_init,
            requires_main=False,  # main이 아직 만들어지기 전 단계이므로 선행 조건에서 제외
        ),
        Step(
            key="identity",
            title=_("tutorial.step.identity.title"),
            mode="compose",
            explain=_("tutorial.step.identity.explain"),
            command_hint=_(
                "tutorial.step.identity.command_hint",
                placeholder_name=PLACEHOLDER_NAME,
                placeholder_email=PLACEHOLDER_EMAIL,
            ),
            check=_identity_configured,
            diagnose=_diagnose_identity,
        ),
        Step(
            key="first-commit",
            title=_("tutorial.step.first_commit.title"),
            mode="compose",
            explain=_("tutorial.step.first_commit.explain"),
            command_hint=_("tutorial.step.first_commit.command_hint"),
            check=_has_commit,
            diagnose=_diagnose_first_commit,
        ),
        Step(
            key="branch",
            title=_("tutorial.step.branch.title"),
            mode="compose",
            explain=_("tutorial.step.branch.explain"),
            command_hint=_("tutorial.step.branch.command_hint"),
            check=_on_practice_branch,
            on_success=_remember_branch,
            diagnose=_diagnose_branch,
        ),
        Step(
            key="branch-commit",
            title=_("tutorial.step.branch_commit.title"),
            mode="compose",
            explain=_("tutorial.step.branch_commit.explain"),
            command_hint=_("tutorial.step.branch_commit.command_hint"),
            check=_branch_ahead_of_main,
            diagnose=_diagnose_branch_commit,
        ),
        Step(
            key="merge",
            title=_("tutorial.step.merge.title"),
            mode="template",
            explain=_("tutorial.step.merge.explain"),
            command_hint=_("tutorial.step.merge.command_hint"),
            check=_merged,
            diagnose=_diagnose_merge,
        ),
        Step(
            key="remote",
            title=_("tutorial.step.remote.title"),
            mode="compose",
            explain=_("tutorial.step.remote.explain"),
            command_hint=_("tutorial.step.remote.command_hint"),
            check=_remote_ok,
            on_enter=lambda ws: g.init_bare(ws.remote_dir) if not ws.remote_dir.exists() else None,
            diagnose=_diagnose_remote,
        ),
        Step(
            key="pull",
            title=_("tutorial.step.pull.title"),
            mode="template",
            explain=_("tutorial.step.pull.explain"),
            command_hint=_("tutorial.step.pull.command_hint"),
            check=_pulled,
            on_enter=_inject_teammate_commit,
            diagnose=_diagnose_pull,
        ),
    ]


STEPS: list[Step] = _build_steps()


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
        "{practice_branch}", ws.get("practice_branch") or _("tutorial.fallback_branch_label")
    )


def _step_block(ws: Workspace, idx: int, step: Step) -> str:
    hint = _fill(ws, step.command_hint)
    explain = _fill(ws, step.explain)
    if step.mode == "template":
        body = _("tutorial.step_block.template_body", hint=hint)
    else:
        body = _("tutorial.step_block.compose_body", hint=hint)
    return "\n".join(
        [
            _("tutorial.step_block.header", n=idx + 1, total=len(STEPS), title=step.title),
            "",
            _("tutorial.step_block.check_location_title"),
            _("tutorial.step_block.cd_hint"),
            _("tutorial.step_block.cd_fallback"),
            _("tutorial.step_block.real_path", repo_dir=ws.repo_dir),
            "",
            explain,
            "",
            body,
            "",
            _("tutorial.step_block.final_hint"),
        ]
    )


def describe_current_step(ws: Workspace, show_intro: bool = False) -> str:
    point_current(ws)
    idx = current_step_index(ws)
    prefix = ""
    if show_intro or (idx == 0 and not ws.get("intro_shown")):
        prefix = _("tutorial.intro") + "\n\n"
        ws.save_meta(intro_shown=True)

    if idx >= len(STEPS):
        return prefix + _("tutorial.completed")
    step = STEPS[idx]
    _ensure_entered(ws, step)
    return prefix + _step_block(ws, idx, step)


def check_current_step(ws: Workspace) -> tuple[bool, str]:
    point_current(ws)
    idx = current_step_index(ws)
    if idx >= len(STEPS):
        return True, _("tutorial.check.already_done")
    step = STEPS[idx]
    _ensure_entered(ws, step)

    if step.requires_main:
        main_issue = _require_main(ws)
        if main_issue:
            return False, _("tutorial.check.failed", title=step.title, detail=main_issue)

    if step.check(ws):
        if step.on_success:
            step.on_success(ws)
        ws.save_meta(current_step=idx + 1)
        if idx + 1 >= len(STEPS):
            ws.save_meta(completed=True)
        return True, _("tutorial.check.success", title=step.title)

    if step.diagnose:
        detail = step.diagnose(ws)
    elif step.mode == "compose":
        detail = _("tutorial.check.default_compose_hint")
    else:
        detail = _("tutorial.check.default_template_hint")
    return False, _("tutorial.check.failed", title=step.title, detail=detail)


def reset_tutorial(base_dir: Optional[Path] = None) -> Workspace:
    existing = _find_active(base_dir)
    if existing and existing.path.exists():
        g.force_rmtree(existing.path)
    return start_new(base_dir)
