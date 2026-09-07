from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace, practice_branch_name, require_remote_url

BUG_MARK = "BUG_하드코딩된_운영키"


class UndoPushedCommitScenario(Scenario):
    id = "undo-pushed-commit"
    title = _("scenario.undo_pushed_commit.title")
    level = _("scenario.undo_pushed_commit.level")
    tags = ["revert", "reset", "shared-history"]
    summary = _("scenario.undo_pushed_commit.summary")

    def setup(self, ws: Workspace) -> None:
        remote_url = require_remote_url()
        branch = practice_branch_name(ws)

        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "config.py", "API_URL = 'https://api.example.com'\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, _("scenario.undo_pushed_commit.commit.initial"))
        g.setup_practice_remote(ws.repo_dir, branch, remote_url)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        g.write_file(
            ws.repo_dir,
            "config.py",
            f"API_URL = 'https://api.example.com'\nAPI_KEY = '{BUG_MARK}'\n",
        )
        g.add_all(ws.repo_dir)
        bad_commit = g.commit(ws.repo_dir, _("scenario.undo_pushed_commit.commit.bad"))
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)

        # 동료가 이미 이 커밋을 pull 받아서 자기 컴퓨터에 갖고 있는 상황을 재현.
        g.clone_practice_remote(remote_url, ws.teammate_dir, branch)

        ws.save_meta(base_commit=base, bad_commit=bad_commit)

    def briefing(self, ws: Workspace) -> str:
        return _("scenario.undo_pushed_commit.briefing", bug_mark=BUG_MARK, repo_dir=ws.repo_dir)

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
        bad_commit = ws.get("bad_commit")

        if not remote_main:
            return CheckResult(False, _("scenario.undo_pushed_commit.check.no_remote_main"), details)

        content = g.file_at_ref(ws.repo_dir, remote_main, "config.py") or ""

        bug_removed = BUG_MARK not in content
        details.append(_("scenario.undo_pushed_commit.check.detail_bug_removed", value=bug_removed))

        # 실제 원격은 bare 저장소처럼 파일로 직접 reflog를 들여다볼 수 없다. 대신
        # "이력이 그대로 보존되었는가(bad_commit이 여전히 조상인가)"로 강제 push /
        # 이력 재작성 여부를 판단한다 — revert는 이력을 보존하고, reset --hard 뒤
        # force push는 이력을 지운다는 점에서 이 신호가 곧 그 구분과 같다.
        history_preserved = g.is_ancestor(ws.repo_dir, bad_commit, remote_main)
        details.append(_("scenario.undo_pushed_commit.check.detail_history_preserved", value=history_preserved))

        if not history_preserved:
            return CheckResult(False, _("scenario.undo_pushed_commit.check.rewritten"), details)
        if not bug_removed:
            return CheckResult(False, _("scenario.undo_pushed_commit.check.bug_remains"), details)

        return CheckResult(True, _("scenario.undo_pushed_commit.check.success"), details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        entries = g.reflog_entries(ws.repo_dir)
        revert_used = any("revert" in e.action.lower() for e in entries)
        reset_used = any(e.action.lower().startswith("reset:") for e in entries)

        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
        bad_commit = ws.get("bad_commit")
        history_rewritten = bool(bad_commit) and bool(remote_main) and not g.is_ancestor(
            ws.repo_dir, bad_commit, remote_main
        )

        if revert_used:
            findings.append(_("scenario.undo_pushed_commit.diagnose.revert_used"))
        if reset_used and history_rewritten:
            findings.append(_("scenario.undo_pushed_commit.diagnose.reset_force_warning"))
        if not revert_used and not (reset_used and history_rewritten):
            findings.append(_("scenario.undo_pushed_commit.diagnose.none_detected"))
        return findings

    def model_answer(self, ws: Workspace) -> str:
        bad_commit = ws.get("bad_commit", "<커밋해시>")
        base_commit = ws.get("base_commit")
        base_commit_short = base_commit[:10] if base_commit else "<이전커밋>"
        return _(
            "scenario.undo_pushed_commit.model_answer",
            bad_commit_short=bad_commit[:10],
            base_commit_short=base_commit_short,
        )

    def concepts(self, ws: Workspace) -> str:
        return _("scenario.undo_pushed_commit.concepts")

    def reference_solution(self, ws: Workspace) -> None:
        bad_commit = ws.get("bad_commit")
        g.run(["revert", "--no-edit", bad_commit], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
