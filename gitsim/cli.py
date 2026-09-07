from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from gitsim import gitutil as g
from gitsim import report as report_mod
from gitsim import termcolor as t
from gitsim import tutorial
from gitsim.scenarios import get_scenario, list_scenarios
from gitsim.workspace import DEFAULT_ROOT, create_workspace, point_current, resolve_workspace


def cmd_list(args: argparse.Namespace) -> int:
    print(t.heading("연습 가능한 시나리오 목록"))
    for s in list_scenarios():
        print(f"{t.bold(s.id):30} [{s.level}]  {s.title}")
        print(f"{'':30} {t.dim(s.summary)}")
        print()
    print(t.dim("gitsim start <시나리오id> 로 시작하세요. 처음이라면 `gitsim learn` 부터 시작하는 것을 추천합니다."))
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    scenario = get_scenario(args.scenario_id)
    base_dir = Path(args.base_dir) if args.base_dir else None
    ws = create_workspace(scenario.id, base_dir=base_dir)
    scenario.setup(ws)
    point_current(ws)
    print(t.heading(f"[{scenario.level}] {scenario.title}"))
    print(scenario.briefing(ws))
    print()
    print(t.dim(f"워크스페이스: {ws.path}"))
    print(t.dim("cd ~/.gitsim/current 로 이동해서 작업하세요. 완료했다면 `gitsim check` 를 실행하세요."))
    print(t.dim("막히면 `gitsim answer` 로 모범 답안을 볼 수 있습니다 (먼저 스스로 시도해보길 권장)."))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    if ws.scenario_id == tutorial.TUTORIAL_ID:
        print(t.warn("이것은 튜토리얼 워크스페이스입니다. `gitsim learn check` 를 사용하세요."))
        return 1
    scenario = get_scenario(ws.scenario_id)
    result = scenario.check(ws)
    diagnosis = scenario.diagnose(ws)

    print(t.heading(f"검사 결과: {scenario.title}"))
    print(t.ok(result.summary) if result.success else t.fail(result.summary))
    print()
    print(t.sub("세부 내역"))
    for d in result.details:
        print(f"  - {d}")

    print(t.sub("진단"))
    for d in diagnosis:
        print(f"  - {d}")

    report_mod.write_report(scenario, ws, result, diagnosis)
    print()
    print(t.dim(f"자세한 리포트가 저장되었습니다: {ws.report_file}"))
    if not result.success:
        print(t.dim("`gitsim answer` 로 모범 답안을 확인할 수 있습니다."))
    return 0 if result.success else 1


def cmd_answer(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    if ws.scenario_id == tutorial.TUTORIAL_ID:
        print(t.warn("이것은 튜토리얼 워크스페이스입니다. 튜토리얼에는 단계별 힌트가 `gitsim learn` 에 포함되어 있습니다."))
        return 1
    scenario = get_scenario(ws.scenario_id)
    print(t.heading(f"모범 답안: {scenario.title}"))
    print(scenario.model_answer(ws))
    print()
    print(t.sub("핵심 개념"))
    print(scenario.concepts(ws))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    print(t.heading(f"워크스페이스 상태: {ws.scenario_id}"))
    print(f"경로: {ws.path}")
    if ws.repo_dir.exists() and (ws.repo_dir / ".git").exists():
        print(t.sub("git log --graph --oneline --all"))
        print(g.log_graph(ws.repo_dir) or "(로그 없음)")
        print(t.sub("git status"))
        print(g.status_porcelain(ws.repo_dir) or "(clean)")
    else:
        print(t.dim("아직 repo/ 에 git 저장소가 초기화되지 않았습니다."))
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    if ws.scenario_id == tutorial.TUTORIAL_ID:
        new_ws = tutorial.reset_tutorial()
        print(t.ok(f"튜토리얼을 초기화했습니다: {new_ws.path}"))
        return 0
    scenario = get_scenario(ws.scenario_id)
    shutil.rmtree(ws.path)
    new_ws = create_workspace(scenario.id, base_dir=ws.path.parent)
    scenario.setup(new_ws)
    point_current(new_ws)
    print(t.ok(f"시나리오를 초기 상태로 다시 만들었습니다: {new_ws.path}"))
    print(scenario.briefing(new_ws))
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    base_dir = Path(args.base_dir) if getattr(args, "base_dir", None) else None
    sub = getattr(args, "learn_action", None) or "show"

    if sub == "reset":
        ws = tutorial.reset_tutorial(base_dir)
        print(t.ok(f"튜토리얼을 처음부터 다시 시작합니다: {ws.path}"))
        print(tutorial.describe_current_step(ws, show_intro=True))
        return 0

    ws = tutorial.get_or_create(base_dir)

    if sub == "intro":
        print(t.heading("Git 입문 튜토리얼"))
        print(tutorial.describe_current_step(ws, show_intro=True))
        return 0

    if sub == "check":
        success, message = tutorial.check_current_step(ws)
        print(t.ok(message) if success else t.fail(message))
        print()
        print(tutorial.describe_current_step(ws))
        return 0 if success else 1

    print(t.heading("Git 입문 튜토리얼"))
    print(tutorial.describe_current_step(ws))
    return 0


def cmd_workspaces(args: argparse.Namespace) -> int:
    from gitsim.workspace import list_workspaces

    base_dir = Path(args.base_dir) if args.base_dir else None
    items = list_workspaces(base_dir)
    if not items:
        print(t.dim("아직 생성된 워크스페이스가 없습니다. `gitsim start <시나리오id>` 로 시작하세요."))
        return 0
    print(t.heading("워크스페이스 목록"))
    for ws in items:
        marker = "✅" if ws.get("completed") else "  "
        print(f"{marker} {ws.scenario_id:22} {ws.path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitsim",
        description="실제 git과 로컬 원격 저장소로 실무 git 상황을 훈련하는 시뮬레이터",
    )
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="연습 가능한 시나리오 목록 보기")
    p_list.set_defaults(func=cmd_list)

    p_start = sub.add_parser("start", help="새 시나리오 워크스페이스 시작")
    p_start.add_argument("scenario_id")
    p_start.add_argument("--base-dir", default=None, help=f"워크스페이스 저장 위치 (기본: {DEFAULT_ROOT})")
    p_start.set_defaults(func=cmd_start)

    p_check = sub.add_parser("check", help="현재 워크스페이스에서 임무 완료 여부 검사")
    p_check.add_argument("--dir", default=None, help="워크스페이스 경로 (생략 시 현재 위치에서 자동 탐지)")
    p_check.set_defaults(func=cmd_check)

    p_answer = sub.add_parser("answer", help="모범 답안과 핵심 개념 보기")
    p_answer.add_argument("--dir", default=None)
    p_answer.set_defaults(func=cmd_answer)

    p_status = sub.add_parser("status", help="현재 워크스페이스의 git 로그/상태 보기")
    p_status.add_argument("--dir", default=None)
    p_status.set_defaults(func=cmd_status)

    p_reset = sub.add_parser("reset", help="시나리오를 처음 상태로 재구성")
    p_reset.add_argument("--dir", default=None)
    p_reset.set_defaults(func=cmd_reset)

    p_learn = sub.add_parser("learn", help="git 입문자를 위한 단계별 튜토리얼")
    p_learn.add_argument("learn_action", nargs="?", choices=["show", "check", "reset", "intro"], default="show")
    p_learn.add_argument("--base-dir", default=None)
    p_learn.set_defaults(func=cmd_learn)

    p_ws = sub.add_parser("workspaces", help="지금까지 만든 워크스페이스 목록")
    p_ws.add_argument("--base-dir", default=None)
    p_ws.set_defaults(func=cmd_workspaces)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except (FileNotFoundError, KeyError) as e:
        print(t.fail(str(e)))
        return 1
    except g.GitError as e:
        print(t.fail(str(e)))
        return 1
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
