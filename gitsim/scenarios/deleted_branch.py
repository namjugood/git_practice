from __future__ import annotations

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace


class DeletedBranchScenario(Scenario):
    id = "deleted-branch"
    title = "실수로 삭제한 브랜치 복구하기"
    level = "중급"
    tags = ["reflog", "branch", "recovery"]
    summary = "커밋이 남아있는 브랜치를 실수로 삭제한 상황에서 reflog로 복구한다."

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "app.py", "def main():\n    print('hello')\n")
        g.add_all(ws.repo_dir)
        g.commit(ws.repo_dir, "초기 커밋")
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)

        g.run(["checkout", "-b", "feature/login"], cwd=ws.repo_dir)
        g.append_file(ws.repo_dir, "app.py", "\ndef login(user):\n    return True\n")
        g.add_all(ws.repo_dir)
        g.commit(ws.repo_dir, "feat: 로그인 함수 추가")
        g.append_file(ws.repo_dir, "app.py", "\ndef logout(user):\n    return True\n")
        g.add_all(ws.repo_dir)
        lost_commit = g.commit(ws.repo_dir, "feat: 로그아웃 함수 추가")

        g.run(["checkout", "main"], cwd=ws.repo_dir)
        g.run(["branch", "-D", "feature/login"], cwd=ws.repo_dir)

        ws.save_meta(lost_commit=lost_commit, branch_name="feature/login")

    def briefing(self, ws: Workspace) -> str:
        return f"""
[상황]
어제까지 `feature/login` 브랜치에서 로그인/로그아웃 기능을 작업했습니다.
그런데 방금 실수로 아래 명령을 실행해서 브랜치를 삭제해버렸습니다.

    git branch -D feature/login

커밋 자체는 아직 git 내부 어딘가에 남아있을 가능성이 높습니다.

[임무]
1. 삭제하기 전 마지막 커밋을 찾아내세요. (`git reflog` 가 힌트를 줍니다)
2. 그 커밋을 가리키는 브랜치를 다시 만들어 작업을 복구하세요.
   (브랜치 이름은 `feature/login` 이 아니어도 되지만, 그대로 복구하는 것을 권장합니다)

작업 위치: cd ~/.gitsim/current
  (이 경로로 이동이 안 되면, 아래 실제 경로를 대신 사용하세요: {ws.repo_dir})
""".strip()

    def check(self, ws: Workspace) -> CheckResult:
        lost_commit = ws.get("lost_commit")
        details = []
        if not g.object_exists(ws.repo_dir, lost_commit):
            details.append("삭제된 커밋 오브젝트 자체를 git DB에서 더 이상 찾을 수 없습니다 (gc로 소실되었을 수 있음).")
            return CheckResult(False, "복구할 커밋을 찾지 못했습니다.", details)

        owners = g.branches_containing(ws.repo_dir, lost_commit)
        details.append(f"해당 커밋을 포함하는 브랜치들: {owners or '없음'}")
        if not owners:
            return CheckResult(False, "아직 어떤 브랜치도 해당 커밋을 가리키고 있지 않습니다.", details)

        return CheckResult(True, f"브랜치 {owners}가 로그인 기능 커밋을 다시 가리키도록 복구했습니다.", details)

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
            findings.append("`branch: Created from ...` reflog 기록이 확인됩니다. 브랜치를 새로 만들어 복구를 시도했습니다.")
        else:
            findings.append("새 브랜치 생성 기록이 보이지 않습니다. `git branch <이름> <커밋 해시>` 로 브랜치를 다시 만들어야 합니다.")
        findings.append(
            "실수를 막으려면 `git branch -d`(소문자, merge 안 된 브랜치는 삭제를 거부)를 기본으로 쓰고, "
            "`-D`(강제 삭제)는 정말 필요할 때만 신중하게 사용하세요."
        )
        return findings

    def model_answer(self, ws: Workspace) -> str:
        lost_commit = ws.get("lost_commit", "<커밋해시>")
        return f"""
1. `git reflog`
   → HEAD가 거쳐온 기록이 시간 역순으로 나온다. 삭제 직전 `feature/login` 위에서
     작업하며 만든 `commit: feat: 로그아웃 함수 추가` 같은 항목을 찾는다.
     (이번 상황의 실제 커밋 해시: {lost_commit[:10]})
2. `git branch feature/login {lost_commit[:10]}`
   → 찾은 커밋을 가리키는 브랜치를 다시 만든다. (`git checkout -b` 로 바로 이동까지 해도 된다)
3. `git log feature/login` 로 로그인/로그아웃 커밋이 모두 돌아왔는지 확인.
4. 필요하면 `git push -u origin feature/login` 으로 원격에도 백업.

핵심: git은 브랜치를 지워도 커밋 오브젝트 자체를 즉시 지우지 않는다.
브랜치는 커밋을 가리키는 "이름표"일 뿐이라, 이름표만 다시 붙이면 복구된다.
단, 시간이 지나 `git gc` 가 실행되면 어떤 브랜치도 가리키지 않는 커밋은 정말로 삭제될 수 있으니
사고를 인지한 즉시 복구하는 것이 중요하다.
""".strip()

    def concepts(self, ws: Workspace) -> str:
        return """
- **reflog**: HEAD와 각 브랜치가 가리켰던 커밋의 변경 이력을 로컬에 기록한 것. `git log` 와 달리
  브랜치에서 떨어져 나간(dangling) 커밋도 한동안 추적할 수 있게 해준다.
- 브랜치 삭제는 커밋을 지우는 것이 아니라 "이름표"를 떼는 것이다. 참조하는 이름표가 하나도 없는
  커밋만 나중에 `git gc` 로 정리 대상이 된다.
- `git branch -d`(안전, merge 안 되면 거부) vs `git branch -D`(강제, 미병합 커밋도 삭제) 차이를 기억하자.
""".strip()

    def reference_solution(self, ws: Workspace) -> None:
        lost_commit = ws.get("lost_commit")
        g.run(["branch", "feature/login", lost_commit], cwd=ws.repo_dir)
