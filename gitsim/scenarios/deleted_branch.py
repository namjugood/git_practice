from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace


class DeletedBranchScenario(Scenario):
    id = "deleted-branch"
    title = _("scenario.deleted_branch.title")
    level = _("scenario.deleted_branch.level")
    tags = ["reflog", "branch", "recovery"]
    summary = _("scenario.deleted_branch.summary")

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "app.py", "def main():\n    print('hello')\n")
        g.add_all(ws.repo_dir)
        g.commit(ws.repo_dir, _("scenario.deleted_branch.commit.initial"))
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        g.run(["checkout", "-b", "feature/login"], cwd=ws.repo_dir)
        g.append_file(ws.repo_dir, "app.py", "\ndef login(user):\n    return True\n")
        g.add_all(ws.repo_dir)
        g.commit(ws.repo_dir, _("scenario.deleted_branch.commit.login"))
        g.append_file(ws.repo_dir, "app.py", "\ndef logout(user):\n    return True\n")
        g.add_all(ws.repo_dir)
        lost_commit = g.commit(ws.repo_dir, _("scenario.deleted_branch.commit.logout"))

        g.run(["checkout", "main"], cwd=ws.repo_dir)
        g.run(["branch", "-D", "feature/login"], cwd=ws.repo_dir)

        ws.save_meta(lost_commit=lost_commit, branch_name="feature/login")

    def briefing(self, ws: Workspace) -> str:
        return _("scenario.deleted_branch.briefing", repo_dir=ws.repo_dir)

    def check(self, ws: Workspace) -> CheckResult:
        lost_commit = ws.get("lost_commit")
        details = []
        if not g.object_exists(ws.repo_dir, lost_commit):
            details.append(_("scenario.deleted_branch.check.object_gone"))
            return CheckResult(False, _("scenario.deleted_branch.check.not_found"), details)

        owners = g.branches_containing(ws.repo_dir, lost_commit)
        details.append(_("scenario.deleted_branch.check.detail_owners", owners=owners or _("scenario.deleted_branch.check.none")))
        if not owners:
            return CheckResult(False, _("scenario.deleted_branch.check.no_owner"), details)

        return CheckResult(True, _("scenario.deleted_branch.check.success", owners=owners), details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        lost_commit = ws.get("lost_commit")
        # `git branch <이름> <해시>` 로 만든 새 브랜치의 "Created from" 기록은 HEAD가 아니라
        # 그 브랜치 자신의 reflog에 남으므로, 커밋을 되찾은 브랜치들의 reflog를 직접 확인한다.
        owners = g.branches_containing(ws.repo_dir, lost_commit) if lost_commit else []
        used_new_branch = any(
            e.action.lower().startswith("branch: created")
            for b in owners
            for e in g.reflog_entries(ws.repo_dir, ref=b)
        )
        if used_new_branch:
            findings.append(_("scenario.deleted_branch.diagnose.new_branch_found"))
        else:
            findings.append(_("scenario.deleted_branch.diagnose.new_branch_missing"))
        findings.append(_("scenario.deleted_branch.diagnose.habit_tip"))
        return findings

    def model_answer(self, ws: Workspace) -> str:
        lost_commit = ws.get("lost_commit", "<커밋해시>")
        return _("scenario.deleted_branch.model_answer", commit_short=lost_commit[:10])

    def concepts(self, ws: Workspace) -> str:
        return _("scenario.deleted_branch.concepts")

    def reference_solution(self, ws: Workspace) -> None:
        lost_commit = ws.get("lost_commit")
        g.run(["branch", "feature/login", lost_commit], cwd=ws.repo_dir)
