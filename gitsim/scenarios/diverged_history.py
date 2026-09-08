from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace, practice_branch_name, require_remote_url

MARK_REMOTE = "원격팀원변경사항"
MARK_LOCAL = "내로컬변경사항"


class DivergedHistoryScenario(Scenario):
    id = "diverged-history"
    title = _("scenario.diverged_history.title")
    level = _("scenario.diverged_history.level")
    tags = ["fetch", "pull", "rebase", "merge"]
    summary = _("scenario.diverged_history.summary")

    def setup(self, ws: Workspace) -> None:
        remote_url = require_remote_url()
        branch = practice_branch_name(ws)

        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "notes.md", "# 작업 노트\n\n- 시작\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, _("scenario.diverged_history.commit.base"))
        g.setup_practice_remote(ws.repo_dir, branch, remote_url)

        g.clone_practice_remote(remote_url, ws.teammate_dir, branch)
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
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
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

        # 실제 원격은 bare 저장소처럼 파일로 직접 reflog를 들여다볼 수 없으므로,
        # "강제 push로 팀원의 커밋이 원격에서 사라졌는가"를 직접적인 증거(현재 origin/main의
        # 조상 여부)로 판단한다.
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
        remote_commit = ws.get("remote_commit")
        force_push_bare = bool(remote_commit) and bool(remote_main) and not g.is_ancestor(
            ws.repo_dir, remote_commit, remote_main
        )

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
