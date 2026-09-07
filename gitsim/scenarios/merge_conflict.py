from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace, practice_branch_name, require_remote_url


class MergeConflictScenario(Scenario):
    id = "merge-conflict"
    title = _("scenario.merge_conflict.title")
    level = _("scenario.merge_conflict.level")
    tags = ["merge", "conflict", "collaboration"]
    summary = _("scenario.merge_conflict.summary")

    def setup(self, ws: Workspace) -> None:
        recipe_initial = _("scenario.merge_conflict.recipe_initial")
        original_line = _("scenario.merge_conflict.recipe_line_original")

        remote_url = require_remote_url()
        branch = practice_branch_name(ws)

        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "recipe.md", recipe_initial)
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, _("scenario.merge_conflict.commit.base"))
        g.setup_practice_remote(ws.repo_dir, branch, remote_url)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        # 동료의 작업을 시뮬레이션: 별도 클론에서 3번째 줄을 다르게 고쳐 먼저 push
        g.clone_practice_remote(remote_url, ws.teammate_dir, branch)
        teammate_recipe = recipe_initial.replace(original_line, _("scenario.merge_conflict.recipe_line_teammate"))
        g.write_file(ws.teammate_dir, "recipe.md", teammate_recipe)
        g.add_all(ws.teammate_dir)
        teammate_commit = g.commit(ws.teammate_dir, _("scenario.merge_conflict.commit.teammate"))
        g.run(["push", "origin", "main"], cwd=ws.teammate_dir)

        # 학습자는 아직 이 변경을 받지 않은 채, 로컬에서 같은 줄을 다르게 고쳐 커밋해둔다.
        my_recipe = recipe_initial.replace(original_line, _("scenario.merge_conflict.recipe_line_mine"))
        g.write_file(ws.repo_dir, "recipe.md", my_recipe)
        g.add_all(ws.repo_dir)
        my_commit = g.commit(ws.repo_dir, _("scenario.merge_conflict.commit.mine"))

        ws.save_meta(
            base_commit=base,
            teammate_commit=teammate_commit,
            my_commit=my_commit,
            file="recipe.md",
        )

    def briefing(self, ws: Workspace) -> str:
        return _("scenario.merge_conflict.briefing", repo_dir=ws.repo_dir)

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
        teammate_commit = ws.get("teammate_commit")
        my_commit = ws.get("my_commit")

        if not remote_main:
            return CheckResult(False, _("scenario.merge_conflict.check.no_remote_main"), details)

        includes_teammate = g.is_ancestor(ws.repo_dir, teammate_commit, remote_main)
        includes_mine = g.is_ancestor(ws.repo_dir, my_commit, remote_main)
        details.append(_("scenario.merge_conflict.check.detail_includes_teammate", value=includes_teammate))
        details.append(_("scenario.merge_conflict.check.detail_includes_mine", value=includes_mine))

        if not (includes_teammate and includes_mine):
            return CheckResult(False, _("scenario.merge_conflict.check.not_all_reflected"), details)

        content = g.file_at_ref(ws.repo_dir, remote_main, ws.get("file"))
        if content and ("<<<<<<<" in content or ">>>>>>>" in content or "=======" in content):
            details.append(_("scenario.merge_conflict.check.detail_conflict_markers"))
            return CheckResult(False, _("scenario.merge_conflict.check.conflict_markers_left"), details)

        if not g.is_clean(ws.repo_dir):
            details.append(_("scenario.merge_conflict.check.detail_dirty"))
            return CheckResult(False, _("scenario.merge_conflict.check.dirty"), details)

        return CheckResult(True, _("scenario.merge_conflict.check.success"), details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        entries = g.reflog_entries(ws.repo_dir)
        used_merge = any("merge" in e.action.lower() for e in entries)
        used_abort = any("merge --abort" in e.action.lower() or "abort" in e.action.lower() for e in entries)
        used_reset_hard = any(e.action.lower().startswith("reset: moving to") for e in entries)

        if used_abort:
            findings.append(_("scenario.merge_conflict.diagnose.abort_used"))
        if used_reset_hard:
            findings.append(_("scenario.merge_conflict.diagnose.reset_hard_used"))
        if used_merge:
            findings.append(_("scenario.merge_conflict.diagnose.merge_used"))
        else:
            findings.append(_("scenario.merge_conflict.diagnose.merge_not_detected"))
        return findings

    def model_answer(self, ws: Workspace) -> str:
        return _("scenario.merge_conflict.model_answer")

    def concepts(self, ws: Workspace) -> str:
        return _("scenario.merge_conflict.concepts")

    def reference_solution(self, ws: Workspace) -> None:
        g.run(["fetch", "origin"], cwd=ws.repo_dir)
        proc = g.run(["merge", "origin/main", "--no-edit"], cwd=ws.repo_dir, check=False)
        if proc.returncode != 0:
            merged = (
                "# 오늘의 레시피\n\n"
                "1. 재료를 준비한다\n"
                "2. 재료를 손질한다\n"
                "3. 강불로 5분간 겉을 익힌 뒤, 약불로 40분간 은근히 조리한다\n"
            )
            g.write_file(ws.repo_dir, "recipe.md", merged)
            g.add_all(ws.repo_dir)
            g.run(["commit", "--no-edit"], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
