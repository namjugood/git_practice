from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace

MARK_REMOTE = "원격팀원변경사항"
MARK_LOCAL = "내로컬변경사항"


class DivergedHistoryScenario(Scenario):
    id = "diverged-history"
    title = _("scenario.diverged_history.title")
    level = _("scenario.diverged_history.level")
    tags = ["fetch", "pull", "rebase", "merge"]
    summary = _("scenario.diverged_history.summary")

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "notes.md", "# 작업 노트\n\n- 시작\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, _("scenario.diverged_history.commit.base"))
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        g.clone(ws.remote_dir, ws.teammate_dir)
        g.write_file(ws.teammate_dir, "remote_change.md", f"{MARK_REMOTE}\n")
        g.add_all(ws.teammate_dir)
        remote_commit = g.commit(ws.teammate_dir, _("scenario.diverged_history.commit.remote"))
        g.run(["push", "origin", "main"], cwd=ws.teammate_dir)

        # 학습자는 fetch 하지 않은 채로 로컬에서 별도 파일에 커밋을 추가한다 (겹치는 줄이 없어 자동 병합됨).
        g.write_file(ws.repo_dir, "local_change.md", f"{MARK_LOCAL}\n")
        g.add_all(ws.repo_dir)
        local_commit = g.commit(ws.repo_dir, _("scenario.diverged_history.commit.local"))

        ws.save_meta(base_commit=base, remote_commit=remote_commit, local_commit=local_commit)

    def briefing(self, ws: Workspace) -> str:
        return _("scenario.diverged_history.briefing", repo_dir=ws.repo_dir)

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
        remote_commit = ws.get("remote_commit")

        if not remote_main:
            return CheckResult(False, _("scenario.diverged_history.check.no_remote_main"), details)

        remote_content = g.file_at_ref(ws.repo_dir, remote_main, "remote_change.md") or ""
        local_content = g.file_at_ref(ws.repo_dir, remote_main, "local_change.md") or ""
        has_remote_mark = MARK_REMOTE in remote_content
        has_local_mark = MARK_LOCAL in local_content
        details.append(_("scenario.diverged_history.check.detail_remote_mark", value=has_remote_mark))
        details.append(_("scenario.diverged_history.check.detail_local_mark", value=has_local_mark))

        includes_remote_commit = g.is_ancestor(ws.repo_dir, remote_commit, remote_main)
        details.append(_("scenario.diverged_history.check.detail_remote_commit_kept", value=includes_remote_commit))

        if not includes_remote_commit:
            return CheckResult(False, _("scenario.diverged_history.check.remote_commit_lost"), details)
        if not (has_remote_mark and has_local_mark):
            return CheckResult(False, _("scenario.diverged_history.check.not_all_reflected"), details)

        return CheckResult(True, _("scenario.diverged_history.check.success"), details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        entries = g.reflog_entries(ws.repo_dir)
        rebase_used = any("rebase" in e.action.lower() for e in entries)
        merge_used = any(e.action.lower().startswith("merge") or e.action.lower().startswith("pull") for e in entries)
        force_push_bare = "forced-update" in g.bare_reflog(ws.remote_dir)

        if force_push_bare:
            findings.append(_("scenario.diverged_history.diagnose.force_push_detected"))
        if rebase_used:
            findings.append(_("scenario.diverged_history.diagnose.rebase_used"))
        elif merge_used:
            findings.append(_("scenario.diverged_history.diagnose.merge_used"))
        else:
            findings.append(_("scenario.diverged_history.diagnose.none_detected"))
        return findings

    def model_answer(self, ws: Workspace) -> str:
        return _("scenario.diverged_history.model_answer")

    def concepts(self, ws: Workspace) -> str:
        return _("scenario.diverged_history.concepts")

    def reference_solution(self, ws: Workspace) -> None:
        g.run(["fetch", "origin"], cwd=ws.repo_dir)
        g.run(["merge", "origin/main", "--no-edit"], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
