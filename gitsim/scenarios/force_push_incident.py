from __future__ import annotations

from gitsim import gitutil as g
from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace, practice_branch_name, require_remote_url

MARK_TEAMMATE = "팀원B의분석내용"
MARK_MINE = "내실수로덮어쓴내용"


class ForcePushIncidentScenario(Scenario):
    id = "force-push-incident"
    title = _("scenario.force_push_incident.title")
    level = _("scenario.force_push_incident.level")
    tags = ["force-push", "recovery", "collaboration"]
    summary = _("scenario.force_push_incident.summary")

    def setup(self, ws: Workspace) -> None:
        remote_url = require_remote_url()
        branch = practice_branch_name(ws)

        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "report.md", "# 분기 보고서\n\n## 개요\n기초 내용\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, _("scenario.force_push_incident.commit.initial"))
        g.setup_practice_remote(ws.repo_dir, branch, remote_url)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        # 팀원 B가 클론해서 분석 내용을 새 파일로 추가하고 push (origin main = B)
        g.clone_practice_remote(remote_url, ws.teammate_dir, branch)
        g.write_file(ws.teammate_dir, "analysis.md", f"## 분석\n{MARK_TEAMMATE}\n")
        g.add_all(ws.teammate_dir)
        teammate_commit = g.commit(ws.teammate_dir, _("scenario.force_push_incident.commit.teammate"))
        g.run(["push", "origin", "main"], cwd=ws.teammate_dir)

        # 학습자의 로컬 저장소(repo_dir)는 아직 base 상태 -> fetch 없이 강제로 사고를 낸다.
        g.write_file(ws.repo_dir, "conclusion.md", f"## 결론\n{MARK_MINE}\n")
        g.add_all(ws.repo_dir)
        my_commit = g.commit(ws.repo_dir, _("scenario.force_push_incident.commit.mine"))
        g.run(["push", "--force", "origin", "main"], cwd=ws.repo_dir)
        remote_tip_after_incident = g.rev_parse(ws.repo_dir, "main")

        ws.save_meta(
            base_commit=base,
            teammate_commit=teammate_commit,
            my_commit=my_commit,
            # 실제 원격은 bare 저장소처럼 reflog를 파일로 직접 볼 수 없으므로, `gitsim check`가
            # 호출될 때마다 원격 tip을 기록해두고 다음 호출 때와 비교해서 강제 push가 몇 번
            # 더 일어났는지(비-fast-forward 전이 횟수) 추적한다. setup()에서 이미 사고성
            # force push를 한 번 냈으므로 1부터 시작한다.
            known_remote_tip=remote_tip_after_incident,
            force_push_count=1,
        )

    def briefing(self, ws: Workspace) -> str:
        return _("scenario.force_push_incident.briefing", teammate_dir=ws.teammate_dir, repo_dir=ws.repo_dir)

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
        if not remote_main:
            return CheckResult(False, _("scenario.force_push_incident.check.no_remote_main"), details)

        analysis_content = g.file_at_ref(ws.repo_dir, remote_main, "analysis.md") or ""
        conclusion_content = g.file_at_ref(ws.repo_dir, remote_main, "conclusion.md") or ""

        has_teammate = MARK_TEAMMATE in analysis_content
        has_mine = MARK_MINE in conclusion_content
        details.append(_("scenario.force_push_incident.check.detail_teammate", value=has_teammate))
        details.append(_("scenario.force_push_incident.check.detail_mine", value=has_mine))

        teammate_commit = ws.get("teammate_commit")
        history_has_teammate_commit = g.is_ancestor(ws.repo_dir, teammate_commit, remote_main)
        details.append(_("scenario.force_push_incident.check.detail_history_kept", value=history_has_teammate_commit))

        if not (has_teammate and has_mine):
            return CheckResult(False, _("scenario.force_push_incident.check.not_all_recovered"), details)

        return CheckResult(True, _("scenario.force_push_incident.check.success"), details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        # 실제 원격은 bare 저장소처럼 reflog를 파일로 직접 볼 수 없다. 대신 이전에 기록해둔
        # 원격 tip과 지금 tip을 비교해서, 그 사이 전이가 fast-forward가 아니었다면(강제로
        # 덮어쓴 것이라면) 카운트를 늘리는 방식으로 "몇 번 더 force push가 있었는지" 추적한다.
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.rev_parse(ws.repo_dir, "origin/main")
        known_tip = ws.get("known_remote_tip")
        force_count = ws.get("force_push_count", 1)
        if remote_main and known_tip and remote_main != known_tip:
            if not g.is_ancestor(ws.repo_dir, known_tip, remote_main):
                force_count += 1
            ws.save_meta(known_remote_tip=remote_main, force_push_count=force_count)
        findings.append(_("scenario.force_push_incident.diagnose.detail_force_count", count=force_count))
        if force_count >= 2:
            findings.append(_("scenario.force_push_incident.diagnose.force_used_again"))
        elif force_count == 1:
            findings.append(_("scenario.force_push_incident.diagnose.force_used_once"))

        remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
        if "teammate" in remotes or any("teammate" in r for r in remotes):
            findings.append(_("scenario.force_push_incident.diagnose.teammate_remote_found"))
        else:
            findings.append(_("scenario.force_push_incident.diagnose.teammate_remote_missing"))
        return findings

    def model_answer(self, ws: Workspace) -> str:
        return _("scenario.force_push_incident.model_answer", teammate_dir=ws.teammate_dir)

    def concepts(self, ws: Workspace) -> str:
        return _("scenario.force_push_incident.concepts")

    def reference_solution(self, ws: Workspace) -> None:
        g.run(["remote", "add", "teammate", str(ws.teammate_dir)], cwd=ws.repo_dir, check=False)
        g.run(["fetch", "teammate"], cwd=ws.repo_dir)
        g.run(["merge", "teammate/main", "--no-edit"], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
