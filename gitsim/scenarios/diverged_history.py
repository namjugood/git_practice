from __future__ import annotations

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace

MARK_REMOTE = "원격팀원변경사항"
MARK_LOCAL = "내로컬변경사항"


class DivergedHistoryScenario(Scenario):
    id = "diverged-history"
    title = "로컬과 원격이 서로 다른 커밋으로 갈라졌을 때"
    level = "중급"
    tags = ["fetch", "pull", "rebase", "merge"]
    summary = "push가 거부(rejected)되는 상황을 fetch + merge/rebase로 안전하게 해결한다."

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "notes.md", "# 작업 노트\n\n- 시작\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, "초기 노트")
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        g.clone(ws.remote_dir, ws.teammate_dir)
        g.write_file(ws.teammate_dir, "remote_change.md", f"{MARK_REMOTE}\n")
        g.add_all(ws.teammate_dir)
        remote_commit = g.commit(ws.teammate_dir, "팀원: 원격에 새 커밋 추가")
        g.run(["push", "origin", "main"], cwd=ws.teammate_dir)

        # 학습자는 fetch 하지 않은 채로 로컬에서 별도 파일에 커밋을 추가한다 (겹치는 줄이 없어 자동 병합됨).
        g.write_file(ws.repo_dir, "local_change.md", f"{MARK_LOCAL}\n")
        g.add_all(ws.repo_dir)
        local_commit = g.commit(ws.repo_dir, "나: 로컬에 새 커밋 추가")

        ws.save_meta(base_commit=base, remote_commit=remote_commit, local_commit=local_commit)

    def briefing(self, ws: Workspace) -> str:
        return f"""
[상황]
팀원이 당신보다 먼저 origin/main에 커밋을 push 했습니다. 그 사실을 모른 채
당신도 로컬 main에 커밋을 하나 추가했습니다. 지금 `git push` 를 하면 아마 이렇게
거부(rejected, non-fast-forward)될 것입니다.

[임무]
1. 실제로 `git push` 를 시도해서 거부되는 것을 확인해보세요.
2. 원격의 변경 사항을 안전하게 받아와서 내 커밋과 합치세요. (merge 또는 rebase 중 선택)
   - 절대로 `git push --force` 로 팀원의 커밋을 덮어쓰지 마세요.
3. 두 커밋이 모두 반영된 상태로 다시 push 하세요.

작업 위치: ~/.gitsim/current  (실제 경로: {ws.repo_dir})
""".strip()

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
        remote_commit = ws.get("remote_commit")

        if not remote_main:
            return CheckResult(False, "원격에 main 브랜치가 없습니다.", details)

        remote_content = g.file_at_ref(ws.repo_dir, remote_main, "remote_change.md") or ""
        local_content = g.file_at_ref(ws.repo_dir, remote_main, "local_change.md") or ""
        has_remote_mark = MARK_REMOTE in remote_content
        has_local_mark = MARK_LOCAL in local_content
        details.append(f"원격 최종본에 팀원 변경 사항 포함 여부: {has_remote_mark}")
        details.append(f"원격 최종본에 내 변경 사항 포함 여부: {has_local_mark}")

        includes_remote_commit = g.is_ancestor(ws.repo_dir, remote_commit, remote_main)
        details.append(f"팀원의 원래 커밋이 히스토리에 여전히 존재하는가(force-push로 지워지지 않았는가): {includes_remote_commit}")

        if not includes_remote_commit:
            return CheckResult(
                False,
                "팀원의 커밋이 히스토리에서 사라졌습니다. force-push로 덮어쓴 것으로 보입니다 — 되돌리세요.",
                details,
            )
        if not (has_remote_mark and has_local_mark):
            return CheckResult(False, "아직 두 사람의 변경 사항이 모두 원격에 반영되지 않았습니다.", details)

        return CheckResult(True, "두 커밋을 안전하게 통합해서 원격에 반영했습니다.", details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        entries = g.reflog_entries(ws.repo_dir)
        rebase_used = any("rebase" in e.action.lower() for e in entries)
        merge_used = any(e.action.lower().startswith("merge") or e.action.lower().startswith("pull") for e in entries)
        force_push_bare = "forced-update" in g.bare_reflog(ws.remote_dir)

        if force_push_bare:
            findings.append(
                "원격 저장소 reflog에 'forced-update' 기록이 있습니다. `--force` push를 사용한 것으로 보입니다. "
                "공유 브랜치에는 force push 대신 fetch 후 merge/rebase로 통합해야 합니다."
            )
        if rebase_used:
            findings.append("rebase를 사용해 커밋 히스토리를 깔끔하게(선형으로) 정리했습니다.")
        elif merge_used:
            findings.append("merge를 사용해 두 히스토리를 합쳤습니다. (병합 커밋이 하나 추가됨)")
        else:
            findings.append("merge/rebase 관련 동작이 reflog에서 뚜렷하게 확인되지 않았습니다.")
        return findings

    def model_answer(self, ws: Workspace) -> str:
        return """
1. `git push origin main`            → "Updates were rejected because the tip of your current
                                        branch is behind" 오류로 거부됨을 확인.
2. `git fetch origin`                → 원격의 최신 커밋을 받아온다 (내 브랜치는 아직 안 바뀜).
3-A. `git merge origin/main`         → 병합 커밋을 만들어 두 히스토리를 합친다. (이 예시는 서로 다른
                                        줄을 고쳤으므로 충돌 없이 자동 병합된다)
   또는
3-B. `git rebase origin/main`        → 내 커밋을 원격 커밋 뒤로 다시 쌓아 히스토리를 선형으로 유지한다.
                                        (아직 push하지 않은 로컬 전용 커밋일 때 특히 권장)
4. `git push origin main`            → 이번엔 정상적으로 반영된다.

하지 말아야 할 것: `git push --force`. 아직 내가 받지 못한 팀원의 커밋을 강제로 덮어써서
사라지게 만든다. (강제로 덮어써야 하는 게 정말 확실한 상황이라도 `--force-with-lease` 를 사용해
내가 알고 있는 상태에서만 덮어쓰도록 안전장치를 두는 것이 좋다.)
""".strip()

    def concepts(self, ws: Workspace) -> str:
        return """
- **non-fast-forward push 거부**: 내 브랜치가 원격보다 "뒤처져" 있을 때(원격에 내가 모르는 커밋이
  있을 때) git은 실수로 커밋을 덮어쓰지 않도록 push를 막는다.
- `git fetch` 는 정보만 받아오고, `git merge`/`git rebase`/`git pull`(=fetch+merge 또는 +rebase)이
  실제로 두 히스토리를 합친다.
- merge는 두 히스토리를 그대로 두고 병합 커밋으로 잇는다(사실 그대로 기록). rebase는 내 커밋을
  다시 써서 한 줄로 이어붙인다(히스토리가 깔끔). 이미 push되어 공유된 커밋은 rebase 하지 않는 것이 원칙.
- `git push --force-with-lease`: 내가 마지막으로 본 원격 상태와 실제 원격 상태가 같을 때만 강제
  push를 허용한다. 무지성 `--force` 보다 훨씬 안전하다.
""".strip()

    def reference_solution(self, ws: Workspace) -> None:
        g.run(["fetch", "origin"], cwd=ws.repo_dir)
        g.run(["merge", "origin/main", "--no-edit"], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
