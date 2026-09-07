from __future__ import annotations

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace


class WrongBranchCommitScenario(Scenario):
    id = "wrong-branch-commit"
    title = "브랜치를 안 만들고 main에 잘못 커밋했을 때"
    level = "초급"
    tags = ["branch", "reset", "hygiene"]
    summary = "main에서 바로 작업해버린 커밋들을 되돌리고, 별도 브랜치로 옮긴다."

    def setup(self, ws: Workspace) -> None:
        g.init_bare(ws.remote_dir)
        g.init_repo(ws.repo_dir)
        g.write_file(ws.repo_dir, "app.py", "def main():\n    print('start')\n")
        g.add_all(ws.repo_dir)
        g.commit(ws.repo_dir, "초기 커밋")
        g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
        g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)
        clean_main = g.rev_parse(ws.repo_dir, "main")

        # 브랜치를 새로 만드는 걸 깜빡하고 main 위에 그대로 기능 커밋을 쌓았다고 가정.
        g.append_file(ws.repo_dir, "app.py", "\ndef signup_form():\n    return 'form'\n")
        g.add_all(ws.repo_dir)
        first = g.commit(ws.repo_dir, "feat: 회원가입 폼 추가")
        g.append_file(ws.repo_dir, "app.py", "\ndef validate(form):\n    return bool(form)\n")
        g.add_all(ws.repo_dir)
        second = g.commit(ws.repo_dir, "feat: 회원가입 유효성 검사 추가")

        ws.save_meta(clean_main=clean_main, first_commit=first, second_commit=second)

    def briefing(self, ws: Workspace) -> str:
        return f"""
[상황]
`feature/signup` 브랜치를 새로 만들고 작업할 생각이었는데, 깜빡하고 그냥 `main`에서
커밋을 2개 쌓아버렸습니다. 다행히 아직 원격(origin/main)에는 push하지 않았습니다.

    feat: 회원가입 폼 추가
    feat: 회원가입 유효성 검사 추가

[임무]
1. 이 2개의 커밋을 `feature/signup` 이라는 새 브랜치로 옮기세요. (커밋 내용은 보존)
2. `main` 브랜치는 원래 상태(원격과 동일한 상태)로 되돌리세요.

작업 위치: cd ~/.gitsim/current
  (이 경로로 이동이 안 되면, 아래 실제 경로를 대신 사용하세요: {ws.repo_dir})
""".strip()

    def check(self, ws: Workspace) -> CheckResult:
        details = []
        clean_main = ws.get("clean_main")
        first = ws.get("first_commit")
        second = ws.get("second_commit")

        main_tip = g.rev_parse(ws.repo_dir, "main")
        main_restored = main_tip == clean_main
        details.append(f"main이 원래 커밋으로 복구되었는가: {main_restored} (현재 main={main_tip})")

        owners_first = [b for b in g.branches_containing(ws.repo_dir, first) if b != "main"]
        owners_second = [b for b in g.branches_containing(ws.repo_dir, second) if b != "main"]
        details.append(f"'회원가입 폼 추가' 커밋을 담고 있는 다른 브랜치: {owners_first or '없음'}")
        details.append(f"'유효성 검사 추가' 커밋을 담고 있는 다른 브랜치: {owners_second or '없음'}")

        moved = bool(owners_first) and bool(owners_second) and any(b in owners_first for b in owners_second)

        if not main_restored:
            return CheckResult(False, "main 브랜치가 아직 원래 상태로 복구되지 않았습니다.", details)
        if not moved:
            return CheckResult(False, "기능 커밋들이 아직 별도 브랜치로 옮겨지지 않았습니다.", details)
        return CheckResult(True, "main은 원래대로, 기능 커밋은 별도 브랜치로 안전하게 분리되었습니다.", details)

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
                findings.append(
                    "경고: main을 먼저 reset 한 뒤에 브랜치를 만든 것으로 보입니다. "
                    "reset이 먼저 실행되면 커밋을 참조하는 브랜치가 없어져 유실 위험이 있습니다. "
                    "항상 '새 브랜치로 옮기기 → main reset' 순서를 지키세요."
                )
            else:
                findings.append("브랜치를 먼저 만들어 커밋을 보존한 뒤 main을 reset한 것으로 보입니다. 안전한 순서입니다.")
        elif reset_used and not branch_created:
            findings.append("reset만 실행되고 새 브랜치 생성 기록이 없습니다. 커밋이 유실되었을 수 있습니다.")
        else:
            findings.append("아직 reset 또는 새 브랜치 생성 동작이 감지되지 않았습니다.")
        return findings

    def model_answer(self, ws: Workspace) -> str:
        clean_main = ws.get("clean_main", "<원래main해시>")
        return f"""
1. `git branch feature/signup`
   → 지금 HEAD(마지막 기능 커밋)를 가리키는 새 브랜치를 만든다. 아직 checkout은 안 해도 된다.
   (커밋을 먼저 안전하게 "이름표"로 보존하는 것이 핵심 — 순서가 중요하다!)
2. `git checkout main`
3. `git reset --hard {clean_main[:10]}`  (또는 `git reset --hard origin/main`)
   → main을 원격과 같은 원래 상태로 되돌린다. 이 커밋들은 브랜치에 이미 보존되어 있으므로 안전하다.
4. `git checkout feature/signup` → 계속 작업 이어가기.

주의: `git reset --hard` 는 아직 아무도 pull 하지 않은, 즉 push 되지 않은 로컬 브랜치에서만
이렇게 자유롭게 사용해야 한다. 이미 원격에 push되어 팀원이 받아간 브랜치를 reset --hard 하면
협업이 깨진다 (다른 시나리오 `undo-pushed-commit` 참고).
""".strip()

    def concepts(self, ws: Workspace) -> str:
        return """
- 브랜치는 커밋을 가리키는 포인터일 뿐이므로, 같은 커밋을 여러 브랜치가 동시에 가리킬 수 있다.
  이 성질 덕분에 "커밋 유실 걱정 없이" 브랜치를 만들어 작업을 다른 이름으로 옮길 수 있다.
- `git reset --hard <커밋>` 은 브랜치 포인터를 그 커밋으로 옮기고 워킹 디렉터리도 그 상태로 되돌린다.
  아직 어떤 브랜치도 참조하지 않게 된 커밋은 reflog로만 되찾을 수 있으므로,
  되돌리기 전에 필요한 커밋을 가리키는 브랜치를 먼저 만들어 두는 습관이 안전하다.
- 작업 시작 전 `git status` 로 지금 어느 브랜치에 있는지 확인하는 습관이 이런 실수를 예방한다.
""".strip()

    def reference_solution(self, ws: Workspace) -> None:
        clean_main = ws.get("clean_main")
        g.run(["branch", "feature/signup"], cwd=ws.repo_dir)
        g.run(["checkout", "main"], cwd=ws.repo_dir)
        g.run(["reset", "--hard", clean_main], cwd=ws.repo_dir)
