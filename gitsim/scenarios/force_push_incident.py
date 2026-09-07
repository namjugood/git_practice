from __future__ import annotations

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace

MARK_TEAMMATE = "팀원B의분석내용"
MARK_MINE = "내실수로덮어쓴내용"


class ForcePushIncidentScenario(Scenario):
    id = "force-push-incident"
    title = "강제 푸시(force push)로 원격 커밋이 사라졌을 때 복구"
    level = "고급"
    tags = ["force-push", "recovery", "collaboration"]
    summary = "실수로 force push해서 사라진 팀원의 커밋을, 팀원 로컬 클론을 이용해 복구한다."

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "report.md", "# 분기 보고서\n\n## 개요\n기초 내용\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, "초기 보고서")
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        # 팀원 B가 클론해서 분석 내용을 새 파일로 추가하고 push (origin main = B)
        g.clone(ws.remote_dir, ws.teammate_dir)
        g.write_file(ws.teammate_dir, "analysis.md", f"## 분석\n{MARK_TEAMMATE}\n")
        g.add_all(ws.teammate_dir)
        teammate_commit = g.commit(ws.teammate_dir, "팀원 B: 분석 내용 추가")
        g.run(["push", "origin", "main"], cwd=ws.teammate_dir)

        # 학습자의 로컬 저장소(repo_dir)는 아직 base 상태 -> fetch 없이 강제로 사고를 낸다.
        g.write_file(ws.repo_dir, "conclusion.md", f"## 결론\n{MARK_MINE}\n")
        g.add_all(ws.repo_dir)
        my_commit = g.commit(ws.repo_dir, "사고: 확인 없이 강제로 덮어씀")
        g.run(["push", "--force", "origin", "main"], cwd=ws.repo_dir)

        ws.save_meta(
            base_commit=base,
            teammate_commit=teammate_commit,
            my_commit=my_commit,
        )

    def briefing(self, ws: Workspace) -> str:
        return f"""
[상황]
방금 아래 명령을 실행해서 사고를 냈습니다.

    git push --force origin main

이 때문에 팀원 B가 먼저 push 했던 "분석 내용 추가" 커밋이 원격(origin/main)에서
사라지고, 당신의 커밋만 남았습니다. 다행히 팀원 B의 로컬 저장소에는 아직 그 커밋이
그대로 남아있습니다. (워크스페이스 안의 `teammate_clone/` 디렉터리가 팀원 B의 PC라고 생각하세요)

    팀원 B의 클론 위치: {ws.teammate_dir}

[임무]
1. 팀원 B의 로컬 저장소에서 사라진 커밋을 다시 가져오세요.
   (예: `git remote add teammate ../teammate_clone` 후 `git fetch teammate`)
2. 팀원 B의 변경 사항과 당신의 변경 사항을 모두 살려서 통합하세요.
3. force push 없이, 정상적인 push로 원격을 복구하세요.

작업 위치: ~/.gitsim/current  (실제 경로: {ws.repo_dir})
""".strip()

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
        if not remote_main:
            return CheckResult(False, "원격에 main 브랜치가 없습니다.", details)

        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        analysis_content = g.file_at_ref(ws.repo_dir, remote_main, "analysis.md") or ""
        conclusion_content = g.file_at_ref(ws.repo_dir, remote_main, "conclusion.md") or ""

        has_teammate = MARK_TEAMMATE in analysis_content
        has_mine = MARK_MINE in conclusion_content
        details.append(f"원격 최종본에 팀원 B 내용(analysis.md) 포함: {has_teammate}")
        details.append(f"원격 최종본에 내 내용(conclusion.md) 포함: {has_mine}")

        teammate_commit = ws.get("teammate_commit")
        history_has_teammate_commit = g.is_ancestor(ws.repo_dir, teammate_commit, remote_main)
        details.append(f"팀원 B의 원본 커밋이 히스토리에 조상으로 남아있는가: {history_has_teammate_commit}")

        if not (has_teammate and has_mine):
            return CheckResult(False, "아직 두 사람의 내용이 모두 원격에 복구되지 않았습니다.", details)

        return CheckResult(
            True,
            "팀원 B의 사라진 커밋을 복구하고 내 변경 사항과 함께 원격에 안전하게 반영했습니다.",
            details,
        )

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        remote_reflog = g.bare_reflog(ws.remote_dir)
        force_count = remote_reflog.lower().count("forced-update")
        details_msg = f"원격 저장소 reflog에서 감지된 강제 업데이트 횟수: {force_count}"
        findings.append(details_msg)
        if force_count >= 2:
            findings.append(
                "복구 과정에서도 force push를 다시 사용한 것으로 보입니다. 복구할 때는 "
                "팀원의 커밋을 fetch 후 merge하여 정상적인(fast-forward) push로 해결하는 것이 안전합니다."
            )
        elif force_count == 1:
            findings.append("사고 당시의 강제 업데이트 1회만 감지되었습니다. 복구는 강제 push 없이 진행한 것으로 보입니다. 좋은 습관입니다.")

        remotes = g.run(["remote"], cwd=ws.repo_dir, check=False).stdout.split()
        if "teammate" in remotes or any("teammate" in r for r in remotes):
            findings.append("팀원 B의 클론을 remote로 등록해서 fetch한 흔적이 있습니다.")
        else:
            findings.append("팀원 B의 클론(teammate_clone)을 remote로 등록한 흔적이 보이지 않습니다. 직접 경로를 지정해 fetch 했을 수도 있습니다.")
        return findings

    def model_answer(self, ws: Workspace) -> str:
        return f"""
1. `git remote add teammate {ws.teammate_dir}`
   → 팀원 B의 로컬 클론을 remote로 등록한다. (실무에서는 팀원이 자기 브랜치를 새 브랜치명으로
      직접 push해주는 방법도 많이 쓴다: `git push origin main:recovery/report`)
2. `git fetch teammate`
   → 팀원 B의 저장소에서 사라진 커밋 정보를 가져온다. (`teammate/main` 으로 참조 가능)
3. `git merge teammate/main --no-edit`
   → 팀원 B의 분석 내용과 내 결론 내용을 하나로 합친다. (겹치는 줄이 없다면 자동 병합됨)
4. `git push origin main`
   → force 없이 정상 push. 이제 원격에는 팀원 B의 커밋과 내 커밋이 모두 안전하게 남는다.

재발 방지책:
- 공유 브랜치에는 `git push --force` 대신 `git push --force-with-lease` 를 쓴다.
- push 전에는 항상 `git fetch && git log --oneline --graph origin/main..HEAD` 등으로
  내가 놓치고 있는 커밋이 없는지 확인한다.
- 가능하면 GitHub 등에서 main 브랜치에 "강제 push 금지(branch protection)" 규칙을 설정한다.
""".strip()

    def concepts(self, ws: Workspace) -> str:
        return """
- `git push --force` 는 원격 브랜치의 포인터를 조건 없이 내가 지정한 커밋으로 옮긴다.
  원격에만 있고 내 로컬에는 없는 커밋이 있다면, 그 커밋은 어떤 브랜치도 가리키지 않게 되어
  사실상 유실 위험에 놓인다 (서버가 곧바로 gc를 돌리지 않는 한).
- 이런 사고의 실질적인 복구 수단은 "그 커밋을 여전히 가지고 있는 다른 클론"이다.
  분산 버전 관리 시스템의 장점: 모든 클론이 히스토리 전체의 사본을 갖고 있다.
- `--force-with-lease` 는 "내가 마지막으로 알고 있던 원격 상태와 실제 원격이 같을 때만" 강제
  업데이트를 허용해서, 나도 모르는 사이에 팀원의 새 커밋을 지워버리는 사고를 막아준다.
""".strip()

    def reference_solution(self, ws: Workspace) -> None:
        g.run(["remote", "add", "teammate", str(ws.teammate_dir)], cwd=ws.repo_dir, check=False)
        g.run(["fetch", "teammate"], cwd=ws.repo_dir)
        g.run(["merge", "teammate/main", "--no-edit"], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
