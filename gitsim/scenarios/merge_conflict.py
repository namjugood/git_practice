from __future__ import annotations

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace

RECIPE_INITIAL = "# 오늘의 레시피\n\n1. 재료를 준비한다\n2. 재료를 손질한다\n3. 30분간 조리한다\n"


class MergeConflictScenario(Scenario):
    id = "merge-conflict"
    title = "병합 충돌(merge conflict) 해결하기"
    level = "초급"
    tags = ["merge", "conflict", "collaboration"]
    summary = "같은 파일의 같은 줄을 서로 다르게 고친 두 브랜치를 병합하며 충돌을 직접 해결한다."

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "recipe.md", RECIPE_INITIAL)
        g.add_all(ws.repo_dir)
        base = g.commit(ws.repo_dir, "초기 레시피 작성")
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        # 동료의 작업을 시뮬레이션: 별도 클론에서 3번째 줄을 다르게 고쳐 먼저 push
        g.clone(ws.remote_dir, ws.teammate_dir)
        teammate_recipe = RECIPE_INITIAL.replace(
            "3. 30분간 조리한다\n", "3. 강불로 15분간 조리한다\n"
        )
        g.write_file(ws.teammate_dir, "recipe.md", teammate_recipe)
        g.add_all(ws.teammate_dir)
        teammate_commit = g.commit(ws.teammate_dir, "팀원 B: 화력을 강불로 변경")
        g.run(["push", "origin", "main"], cwd=ws.teammate_dir)

        # 학습자는 아직 이 변경을 받지 않은 채, 로컬에서 같은 줄을 다르게 고쳐 커밋해둔다.
        my_recipe = RECIPE_INITIAL.replace(
            "3. 30분간 조리한다\n", "3. 약불로 45분간 은근히 조리한다\n"
        )
        g.write_file(ws.repo_dir, "recipe.md", my_recipe)
        g.add_all(ws.repo_dir)
        my_commit = g.commit(ws.repo_dir, "나: 약불로 오래 조리하도록 변경")

        ws.save_meta(
            base_commit=base,
            teammate_commit=teammate_commit,
            my_commit=my_commit,
            file="recipe.md",
        )

    def briefing(self, ws: Workspace) -> str:
        return f"""
[상황]
당신과 팀원 B는 같은 저장소의 `recipe.md`를 함께 수정하고 있습니다.
팀원 B가 조금 전 3번째 줄(조리 방법)을 수정해서 원격(origin/main)에 먼저 push 했습니다.
당신도 모르고 같은 줄을 다르게 수정해서 로컬에 커밋을 만들어 두었습니다 (아직 push 전).

[임무]
1. 원격의 최신 변경 사항을 받아오세요.
2. 당신의 변경 사항과 병합(merge)하세요. 같은 줄이 겹치므로 충돌(conflict)이 발생합니다.
3. `recipe.md` 를 열어 두 사람의 의도를 모두 살리는 방향으로 충돌을 해결하세요.
   (한쪽 것만 그대로 선택하지 말고, 내용을 실제로 합치는 것을 권장합니다)
4. 충돌 해결을 완료하고 커밋한 뒤, 원격(origin/main)에 push 하세요.

작업 위치: {ws.repo_dir}
""".strip()

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        remote_main = g.bare_ref(ws.remote_dir, "refs/heads/main")
        base = ws.get("base_commit")
        teammate_commit = ws.get("teammate_commit")
        my_commit = ws.get("my_commit")

        if not remote_main:
            return CheckResult(False, "원격 저장소(origin)에 main 브랜치가 없습니다.", details)

        includes_teammate = g.is_ancestor(ws.repo_dir, teammate_commit, remote_main)
        includes_mine = g.is_ancestor(ws.repo_dir, my_commit, remote_main)
        details.append(f"원격 main이 팀원 B의 커밋을 포함하는가: {includes_teammate}")
        details.append(f"원격 main이 나의 커밋을 포함하는가: {includes_mine}")

        if not (includes_teammate and includes_mine):
            return CheckResult(
                False,
                "아직 두 사람의 변경 사항이 모두 원격 main에 반영되지 않았습니다.",
                details,
            )

        content = g.file_at_ref(ws.repo_dir, remote_main, ws.get("file"))
        if content and ("<<<<<<<" in content or ">>>>>>>" in content or "=======" in content):
            details.append("충돌 마커(<<<<<<<, =======, >>>>>>>)가 그대로 push 되었습니다.")
            return CheckResult(False, "충돌 마커를 지우지 않고 커밋/push 했습니다.", details)

        if not g.is_clean(ws.repo_dir):
            details.append("작업 디렉터리에 아직 커밋되지 않은 변경이 남아있습니다.")
            return CheckResult(False, "작업 디렉터리를 정리(커밋)하지 않았습니다.", details)

        return CheckResult(True, "두 사람의 변경 사항을 모두 살려 충돌을 해결하고 원격에 반영했습니다.", details)

    def diagnose(self, ws: Workspace) -> list[str]:
        findings = []
        entries = g.reflog_entries(ws.repo_dir)
        used_merge = any("merge" in e.action.lower() for e in entries)
        used_abort = any("merge --abort" in e.action.lower() or "abort" in e.action.lower() for e in entries)
        used_reset_hard = any(e.action.lower().startswith("reset: moving to") for e in entries)

        if used_abort:
            findings.append("`git merge --abort` 로 병합을 중단했던 기록이 있습니다. 다시 시도하는 것은 괜찮지만, 충돌은 피할 수 없으니 직접 해결하는 연습이 필요합니다.")
        if used_reset_hard:
            findings.append("`git reset --hard` 사용 기록이 있습니다. 병합 충돌 상황에서 reset --hard로 내 변경 사항을 통째로 버리면 팀원의 의견만 남고 내 작업은 사라집니다. 가능하면 내용을 합치는 방향을 먼저 시도하세요.")
        if used_merge:
            findings.append("`git merge` 관련 동작이 감지되었습니다.")
        else:
            findings.append("merge 관련 reflog 동작이 감지되지 않았습니다. fetch 이후 merge(또는 pull)를 실행했는지 확인하세요.")
        return findings

    def model_answer(self, ws: Workspace) -> str:
        return """
1. `git fetch origin`                → 원격의 최신 커밋 정보를 받아온다 (아직 내 브랜치에 합치지 않음).
2. `git merge origin/main`           → 팀원 B의 커밋을 내 작업에 병합 시도 → 같은 줄이라 충돌 발생.
3. `git status`                      → 충돌난 파일 목록 확인 (recipe.md, Unmerged paths).
4. `recipe.md` 를 열어서 아래 마커를 직접 정리한다.
   ```
   <<<<<<< HEAD
   3. 약불로 45분간 은근히 조리한다
   =======
   3. 강불로 15분간 조리한다
   >>>>>>> origin/main
   ```
   → 두 의견을 모두 반영: 예) `3. 강불로 5분간 겉을 익힌 뒤, 약불로 40분간 은근히 조리한다`
5. `git add recipe.md`               → 충돌 해결 완료 표시.
6. `git commit`                      → 병합 커밋 생성 (기본 메시지 그대로 사용해도 됨).
7. `git push origin main`            → 병합 결과를 원격에 반영.

핵심: 충돌은 "누구 것을 지울까"가 아니라 "두 변경을 어떻게 합칠까"의 문제입니다.
""".strip()

    def concepts(self, ws: Workspace) -> str:
        return """
- **merge conflict**: 두 브랜치가 같은 파일의 같은 부분을 다르게 바꿨을 때, git이 자동으로 합칠 수 없어 사람에게 판단을 맡기는 상태.
- `git fetch` 는 원격 정보를 받아오기만 하고 내 브랜치를 바꾸지 않는다. 실제로 합치려면 `merge`(또는 `rebase`, `pull`)가 필요하다.
- 충돌 마커 `<<<<<<<`, `=======`, `>>>>>>>` 는 반드시 지우고 원하는 최종 내용만 남겨야 한다.
- `git merge --abort` 는 병합 시도 이전 상태로 완전히 되돌린다 (충돌 해결이 막막할 때 안전하게 재시도 가능).
""".strip()

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
