from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace


class WrongBranchCommitScenario(Scenario):
    id = "wrong-branch-commit"
    title = _("scenario.wrong_branch_commit.title")
    level = _("scenario.wrong_branch_commit.level")
    tags = ["branch", "reset", "hygiene"]
    summary = _("scenario.wrong_branch_commit.summary")

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "app.py", "def main():\n    print('start')\n")
        g.add_all(ws.repo_dir)
        g.commit(ws.repo_dir, _("scenario.wrong_branch_commit.commit.initial"))
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)
        clean_main = g.rev_parse(ws.repo_dir, "main")

        # 브랜치를 새로 만드는 걸 깜빡하고 main 위에 그대로 기능 커밋을 쌓았다고 가정.
        g.append_file(ws.repo_dir, "app.py", "\ndef signup_form():\n    return 'form'\n")
        g.add_all(ws.repo_dir)
        first = g.commit(ws.repo_dir, _("scenario.wrong_branch_commit.commit.first"))
        g.append_file(ws.repo_dir, "app.py", "\ndef validate(form):\n    return bool(form)\n")
        g.add_all(ws.repo_dir)
        second = g.commit(ws.repo_dir, _("scenario.wrong_branch_commit.commit.second"))

        ws.save_meta(clean_main=clean_main, first_commit=first, second_commit=second)

    def briefing(self, ws: Workspace) -> str:
        return _("scenario.wrong_branch_commit.briefing", repo_dir=ws.repo_dir)

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        clean_main = ws.get("clean_main")
        first = ws.get("first_commit")
        second = ws.get("second_commit")

        main_tip = g.rev_parse(ws.repo_dir, "main")
        main_restored = main_tip == clean_main
        details.append(_("scenario.wrong_branch_commit.check.detail_main_restored", restored=main_restored, main_tip=main_tip))

        none_label = _("scenario.wrong_branch_commit.check.none")
        owners_first = [b for b in g.branches_containing(ws.repo_dir, first) if b != "main"]
        owners_second = [b for b in g.branches_containing(ws.repo_dir, second) if b != "main"]
        details.append(_("scenario.wrong_branch_commit.check.detail_owners_first", owners=owners_first or none_label))
        details.append(_("scenario.wrong_branch_commit.check.detail_owners_second", owners=owners_second or none_label))

        moved = bool(owners_first) and bool(owners_second) and any(b in owners_first for b in owners_second)

        if not main_restored:
            return CheckResult(False, _("scenario.wrong_branch_commit.check.main_not_restored"), details)
        if not moved:
            return CheckResult(False, _("scenario.wrong_branch_commit.check.not_moved"), details)
        return CheckResult(True, _("scenario.wrong_branch_commit.check.success"), details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        first = ws.get("first_commit")
        # `git branch <이름>` (체크아웃 없이 만들 때)의 "Created from" 기록은 HEAD가 아니라
        # 그 브랜치 자신의 reflog에 남으므로, 커밋을 담고 있는 브랜치들의 reflog까지 함께
        # 모아서 실제 발생 시각 순으로 비교해야 선후 관계를 정확히 판단할 수 있다.
        owners = {b for b in g.branches_containing(ws.repo_dir, first) if b != "main"} if first else set()
        events = g.reflog_events(ws.repo_dir, refs=["HEAD", "main", *owners])
        reset_events = [e for e in events if e.action.lower().startswith("reset:")]
        branch_events = [e for e in events if e.action.lower().startswith("branch: created")]
        reset_used = bool(reset_events)
        branch_created = bool(branch_events)
        if branch_created and reset_used:
            if branch_events[0].timestamp > reset_events[0].timestamp:
                findings.append(_("scenario.wrong_branch_commit.diagnose.reset_after_branch"))
            else:
                findings.append(_("scenario.wrong_branch_commit.diagnose.safe_order"))
        elif reset_used and not branch_created:
            findings.append(_("scenario.wrong_branch_commit.diagnose.reset_only"))
        else:
            findings.append(_("scenario.wrong_branch_commit.diagnose.none_detected"))
        return findings

    def model_answer(self, ws: Workspace) -> str:
        clean_main = ws.get("clean_main", "<원래main해시>")
        return _("scenario.wrong_branch_commit.model_answer", clean_main_short=clean_main[:10])

    def concepts(self, ws: Workspace) -> str:
        return _("scenario.wrong_branch_commit.concepts")

    def reference_solution(self, ws: Workspace) -> None:
        clean_main = ws.get("clean_main")
        g.run(["branch", "feature/signup"], cwd=ws.repo_dir)
        g.run(["checkout", "main"], cwd=ws.repo_dir)
        g.run(["reset", "--hard", clean_main], cwd=ws.repo_dir)
