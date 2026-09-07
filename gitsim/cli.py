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
from gitsim.i18n import t as _
from gitsim.scenarios import get_scenario, list_scenarios
from gitsim.workspace import DEFAULT_ROOT, create_workspace, point_current, resolve_workspace


def cmd_list(args: argparse.Namespace) -> int:
    print(t.heading(_("cli.list.header")))
    for s in list_scenarios():
        print(f"{t.bold(s.id):30} [{s.level}]  {s.title}")
        print(f"{'':30} {t.dim(s.summary)}")
        print()
    print(t.dim(_("cli.list.footer")))
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
    print(t.dim(_("cli.start.workspace_label", path=ws.path)))
    print(t.dim(_("cli.start.hint_cd")))
    print(t.dim(_("cli.start.hint_answer")))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    if ws.scenario_id == tutorial.TUTORIAL_ID:
        print(t.warn(_("cli.tutorial_redirect.check")))
        return 1
    scenario = get_scenario(ws.scenario_id)
    result = scenario.check(ws)
    diagnosis = scenario.diagnose(ws)

    print(t.heading(_("cli.check.header", title=scenario.title)))
    print(t.ok(result.summary) if result.success else t.fail(result.summary))
    print()
    print(t.sub(_("cli.check.details_label")))
    for d in result.details:
        print(f"  - {d}")

    print(t.sub(_("cli.check.diagnosis_label")))
    for d in diagnosis:
        print(f"  - {d}")

    report_mod.write_report(scenario, ws, result, diagnosis)
    print()
    print(t.dim(_("cli.check.report_saved", path=ws.report_file)))
    if not result.success:
        print(t.dim(_("cli.check.see_answer_hint")))
    return 0 if result.success else 1


def cmd_answer(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    if ws.scenario_id == tutorial.TUTORIAL_ID:
        print(t.warn(_("cli.tutorial_redirect.answer")))
        return 1
    scenario = get_scenario(ws.scenario_id)
    print(t.heading(_("cli.answer.header", title=scenario.title)))
    print(scenario.model_answer(ws))
    print()
    print(t.sub(_("cli.answer.concepts_label")))
    print(scenario.concepts(ws))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    print(t.heading(_("cli.status.header", scenario_id=ws.scenario_id)))
    print(_("cli.status.path_label", path=ws.path))
    if ws.repo_dir.exists() and (ws.repo_dir / ".git").exists():
        print(t.sub(_("cli.status.log_label")))
        print(g.log_graph(ws.repo_dir) or _("cli.status.no_log"))
        print(t.sub(_("cli.status.status_label")))
        print(g.status_porcelain(ws.repo_dir) or _("cli.status.clean"))
    else:
        print(t.dim(_("cli.status.not_initialized")))
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.dir, Path.cwd())
    if ws.scenario_id == tutorial.TUTORIAL_ID:
        new_ws = tutorial.reset_tutorial()
        print(t.ok(_("cli.reset.tutorial_done", path=new_ws.path)))
        return 0
    scenario = get_scenario(ws.scenario_id)
    shutil.rmtree(ws.path)
    new_ws = create_workspace(scenario.id, base_dir=ws.path.parent)
    scenario.setup(new_ws)
    point_current(new_ws)
    print(t.ok(_("cli.reset.scenario_done", path=new_ws.path)))
    print(scenario.briefing(new_ws))
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    base_dir = Path(args.base_dir) if getattr(args, "base_dir", None) else None
    sub = getattr(args, "learn_action", None) or "show"

    if sub == "reset":
        ws = tutorial.reset_tutorial(base_dir)
        print(t.ok(_("cli.learn.reset_done", path=ws.path)))
        print(tutorial.describe_current_step(ws, show_intro=True))
        return 0

    ws = tutorial.get_or_create(base_dir)

    if sub == "intro":
        print(t.heading(_("cli.learn.header")))
        print(tutorial.describe_current_step(ws, show_intro=True))
        return 0

    if sub == "check":
        success, message = tutorial.check_current_step(ws)
        print(t.ok(message) if success else t.fail(message))
        print()
        print(tutorial.describe_current_step(ws))
        return 0 if success else 1

    print(t.heading(_("cli.learn.header")))
    print(tutorial.describe_current_step(ws))
    return 0


def cmd_workspaces(args: argparse.Namespace) -> int:
    from gitsim.workspace import list_workspaces

    base_dir = Path(args.base_dir) if args.base_dir else None
    items = list_workspaces(base_dir)
    if not items:
        print(t.dim(_("cli.workspaces.empty")))
        return 0
    print(t.heading(_("cli.workspaces.header")))
    for ws in items:
        marker = "✅" if ws.get("completed") else "  "
        print(f"{marker} {ws.scenario_id:22} {ws.path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitsim",
        description=_("cli.parser.description"),
    )
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help=_("cli.help.list"))
    p_list.set_defaults(func=cmd_list)

    p_start = sub.add_parser("start", help=_("cli.help.start"))
    p_start.add_argument("scenario_id")
    p_start.add_argument("--base-dir", default=None, help=_("cli.help.start.base_dir", default_root=DEFAULT_ROOT))
    p_start.set_defaults(func=cmd_start)

    p_check = sub.add_parser("check", help=_("cli.help.check"))
    p_check.add_argument("--dir", default=None, help=_("cli.help.check.dir"))
    p_check.set_defaults(func=cmd_check)

    p_answer = sub.add_parser("answer", help=_("cli.help.answer"))
    p_answer.add_argument("--dir", default=None)
    p_answer.set_defaults(func=cmd_answer)

    p_status = sub.add_parser("status", help=_("cli.help.status"))
    p_status.add_argument("--dir", default=None)
    p_status.set_defaults(func=cmd_status)

    p_reset = sub.add_parser("reset", help=_("cli.help.reset"))
    p_reset.add_argument("--dir", default=None)
    p_reset.set_defaults(func=cmd_reset)

    p_learn = sub.add_parser("learn", help=_("cli.help.learn"))
    p_learn.add_argument("learn_action", nargs="?", choices=["show", "check", "reset", "intro"], default="show")
    p_learn.add_argument("--base-dir", default=None)
    p_learn.set_defaults(func=cmd_learn)

    p_ws = sub.add_parser("workspaces", help=_("cli.help.workspaces"))
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
