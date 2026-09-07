from __future__ import annotations

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace

BUG_MARK = "BUG_하드코딩된_운영키"


class UndoPushedCommitScenario(Scenario):
    id = "undo-pushed-commit"
    title = "이미 공유된 잘못된 커밋 되돌리기 (revert vs reset)"
    level = "중급"
    tags = ["revert", "reset", "shared-history"]
    summary = "이미 push되어 동료가 pull 받은 버그 커밋을, 히스토리를 깨지 않고 되돌린다."

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "config.py", "API_URL = 'https://api.example.com'\n")
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, "초기 설정 파일 작성")
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        g.write_file(
            ws.repo_dir,
            "config.py",
            f"API_URL = 'https://api.example.com'\nAPI_KEY = '{BUG_MARK}'\n",
        )
        g.add_all(ws.repo_dir)
        bad_commit = g.commit(ws.repo_dir, "hotfix: API 키 임시 하드코딩 (실수)")
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)

        # 동료가 이미 이 커밋을 pull 받아서 자기 컴퓨터에 갖고 있는 상황을 재현.
        g.clone(ws.remote_dir, ws.teammate_dir)

        ws.save_meta(base_commit=base, bad_commit=bad_commit)

    def briefing(self, ws: Workspace) -> str:
        return f"""
[상황]
방금 올린 커밋 "hotfix: API 키 임시 하드코딩 (실수)" 에 운영 키가 그대로 하드코딩되어
들어가 버렸습니다. 이 커밋은 이미 origin/main에 push되었고, 동료도 이미 pull을 받아서
자신의 로컬 저장소(`teammate_clone/`)에 이 커밋을 갖고 있습니다.

[임무]
1. 하드코딩된 키({BUG_MARK})를 config.py에서 제거하세요.
2. 이미 공유(push)된 커밋이므로, 히스토리를 재작성(rewrite)하지 않는 방법으로 되돌리세요.
   즉, `git reset` + `push --force` 조합은 사용하지 마세요. 동료의 히스토리와 어긋나게 됩니다.
3. 되돌린 결과를 원격(origin/main)에 반영하세요.

작업 위치: {ws.repo_dir}
""".strip()

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
        bad_commit = ws.get("bad_commit")

        if not remote_main:
            return CheckResult(False, "원격에 main 브랜치가 없습니다.", details)

        content = g.file_at_ref(ws.repo_dir, remote_main, "config.py")
        if content is None:
            g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
            content = g.file_at_ref(ws.repo_dir, remote_main, "config.py") or ""

        bug_removed = BUG_MARK not in content
        details.append(f"원격 최종본에서 버그 라인이 제거되었는가: {bug_removed}")

        history_preserved = g.is_ancestor(ws.repo_dir, bad_commit, remote_main)
        details.append(f"문제의 커밋이 히스토리에서 지워지지 않고 조상으로 남아있는가: {history_preserved}")

        force_used = "forced-update" in g.bare_reflog(ws.remote_dir)
        details.append(f"원격에 강제 push 흔적이 있는가: {force_used}")

        if force_used or not history_preserved:
            return CheckResult(
                False,
                "히스토리를 재작성(reset + force push)해서 되돌린 것으로 보입니다. "
                "이미 공유된 커밋은 revert로 되돌려야 합니다.",
                details,
            )
        if not bug_removed:
            return CheckResult(False, "아직 버그가 원격 main에서 제거되지 않았습니다.", details)

        return CheckResult(True, "히스토리를 보존한 채 revert로 안전하게 버그를 되돌렸습니다.", details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        entries = g.reflog_entries(ws.repo_dir)
        revert_used = any("revert" in e.action.lower() for e in entries)
        reset_used = any(e.action.lower().startswith("reset:") for e in entries)
        force_used = "forced-update" in g.bare_reflog(ws.remote_dir)

        if revert_used:
            findings.append("`git revert` 사용 기록이 확인됩니다. 이미 공유된 커밋을 되돌리는 올바른 방법입니다.")
        if reset_used and force_used:
            findings.append(
                "경고: reset 이후 force push를 사용한 것으로 보입니다. 동료는 이미 문제의 커밋을 "
                "pull 받았기 때문에, 다음에 동료가 pull/push할 때 히스토리 충돌이 발생합니다."
            )
        if not revert_used and not (reset_used and force_used):
            findings.append("revert도 reset+force push도 뚜렷하게 감지되지 않았습니다. 아직 되돌리기가 진행되지 않은 것 같습니다.")
        return findings

    def model_answer(self, ws: Workspace) -> str:
        bad_commit = ws.get("bad_commit", "<커밋해시>")
        return f"""
1. `git log --oneline`                     → 되돌릴 커밋 해시 확인 ({bad_commit[:10]}).
2. `git revert {bad_commit[:10]}`            → 그 커밋의 변경 내용을 "반대로 적용"하는 새 커밋을 만든다.
   (편집기가 열리면 기본 메시지를 그대로 두고 저장/종료하면 된다. 충돌이 나면 직접 해결 후
   `git add` → `git revert --continue`)
3. `git push origin main`                  → 새 revert 커밋을 push. 히스토리에는 실수했던 커밋도,
                                              그것을 되돌린 커밋도 그대로 남는다 (기록이 정직하게 보존됨).

이렇게 하면 안 되는 이유 (`git reset --hard {ws.get("base_commit", "")[:10] if ws.get("base_commit") else "<이전커밋>"}` + `git push --force`):
동료가 이미 문제의 커밋을 pull 받아 자기 브랜치 위에 작업을 이어가고 있을 수 있다.
내가 강제로 히스토리를 되감아버리면, 동료의 로컬 히스토리와 원격이 어긋나서 다음 push/pull 때
정체불명의 충돌과 "사라졌던 커밋이 되살아나는" 혼란이 발생한다.

참고: 만약 운영 키처럼 민감한 값이 실제로 새어나갔다면, revert로 코드상에서 제거하는 것과
별개로 **그 키 자체를 즉시 폐기(rotate)** 해야 한다. 커밋을 되돌려도 이미 push된 히스토리
어딘가에는 값이 남아있을 수 있기 때문이다.
""".strip()

    def concepts(self, ws: Workspace) -> str:
        return """
- **reset**: 브랜치 포인터를 과거로 옮겨 특정 커밋이 "없었던 것"처럼 만든다. 히스토리를 재작성한다.
- **revert**: 특정 커밋의 변경 내용을 취소하는 **새 커밋**을 추가한다. 히스토리는 그대로 보존된다.
- 이미 push되어 다른 사람이 pull 받았을 가능성이 있는 커밋은 원칙적으로 reset/rebase로
  재작성하지 않는다 ("Don't rewrite public history"). 되돌리고 싶다면 revert를 쓴다.
- 아직 아무도 pull 하지 않은, 나만 갖고 있는 로컬 커밋이라면 reset이나 rebase로 자유롭게
  정리해도 안전하다 (`wrong-branch-commit` 시나리오 참고).
""".strip()

    def reference_solution(self, ws: Workspace) -> None:
        bad_commit = ws.get("bad_commit")
        g.run(["revert", "--no-edit", bad_commit], cwd=ws.repo_dir)
        g.run(["push", "origin", "main"], cwd=ws.repo_dir)
