"""시나리오: wrong-branch-commit."""

MESSAGES: dict[str, str] = {
    "scenario.wrong_branch_commit.title": "브랜치를 안 만들고 main에 잘못 커밋했을 때",
    "scenario.wrong_branch_commit.level": "초급",
    "scenario.wrong_branch_commit.summary": "main에서 바로 작업해버린 커밋들을 되돌리고, 별도 브랜치로 옮긴다.",
    "scenario.wrong_branch_commit.commit.initial": "초기 커밋",
    "scenario.wrong_branch_commit.commit.first": "feat: 회원가입 폼 추가",
    "scenario.wrong_branch_commit.commit.second": "feat: 회원가입 유효성 검사 추가",
    "scenario.wrong_branch_commit.briefing": """[상황]
`feature/signup` 브랜치를 새로 만들고 작업할 생각이었는데, 깜빡하고 그냥 `main`에서
커밋을 2개 쌓아버렸습니다. 다행히 아직 원격(origin/main)에는 push하지 않았습니다.

    feat: 회원가입 폼 추가
    feat: 회원가입 유효성 검사 추가

[임무]
1. 이 2개의 커밋을 `feature/signup` 이라는 새 브랜치로 옮기세요. (커밋 내용은 보존)
2. `main` 브랜치는 원래 상태(원격과 동일한 상태)로 되돌리세요.

작업 위치: cd ~/.gitsim/current
  (이 경로로 이동이 안 되면, 아래 실제 경로를 대신 사용하세요: {repo_dir})""",
    "scenario.wrong_branch_commit.check.detail_main_restored": "main이 원래 커밋으로 복구되었는가: {restored} (현재 main={main_tip})",
    "scenario.wrong_branch_commit.check.detail_owners_first": "'회원가입 폼 추가' 커밋을 담고 있는 다른 브랜치: {owners}",
    "scenario.wrong_branch_commit.check.detail_owners_second": "'유효성 검사 추가' 커밋을 담고 있는 다른 브랜치: {owners}",
    "scenario.wrong_branch_commit.check.none": "없음",
    "scenario.wrong_branch_commit.check.main_not_restored": "main 브랜치가 아직 원래 상태로 복구되지 않았습니다.",
    "scenario.wrong_branch_commit.check.not_moved": "기능 커밋들이 아직 별도 브랜치로 옮겨지지 않았습니다.",
    "scenario.wrong_branch_commit.check.success": "main은 원래대로, 기능 커밋은 별도 브랜치로 안전하게 분리되었습니다.",
    "scenario.wrong_branch_commit.diagnose.reset_after_branch": "경고: main을 먼저 reset 한 뒤에 브랜치를 만든 것으로 보입니다. reset이 먼저 실행되면 커밋을 참조하는 브랜치가 없어져 유실 위험이 있습니다. 항상 '새 브랜치로 옮기기 → main reset' 순서를 지키세요.",
    "scenario.wrong_branch_commit.diagnose.safe_order": "브랜치를 먼저 만들어 커밋을 보존한 뒤 main을 reset한 것으로 보입니다. 안전한 순서입니다.",
    "scenario.wrong_branch_commit.diagnose.reset_only": "reset만 실행되고 새 브랜치 생성 기록이 없습니다. 커밋이 유실되었을 수 있습니다.",
    "scenario.wrong_branch_commit.diagnose.none_detected": "아직 reset 또는 새 브랜치 생성 동작이 감지되지 않았습니다.",
    "scenario.wrong_branch_commit.model_answer": """1. `git branch feature/signup`
   → 지금 HEAD(마지막 기능 커밋)를 가리키는 새 브랜치를 만든다. 아직 checkout은 안 해도 된다.
   (커밋을 먼저 안전하게 "이름표"로 보존하는 것이 핵심 — 순서가 중요하다!)
2. `git checkout main`
3. `git reset --hard {clean_main_short}`  (또는 `git reset --hard origin/main`)
   → main을 원격과 같은 원래 상태로 되돌린다. 이 커밋들은 브랜치에 이미 보존되어 있으므로 안전하다.
4. `git checkout feature/signup` → 계속 작업 이어가기.

주의: `git reset --hard` 는 아직 아무도 pull 하지 않은, 즉 push 되지 않은 로컬 브랜치에서만
이렇게 자유롭게 사용해야 한다. 이미 원격에 push되어 팀원이 받아간 브랜치를 reset --hard 하면
협업이 깨진다 (다른 시나리오 `undo-pushed-commit` 참고).""",
    "scenario.wrong_branch_commit.concepts": """- 브랜치는 커밋을 가리키는 포인터일 뿐이므로, 같은 커밋을 여러 브랜치가 동시에 가리킬 수 있다.
  이 성질 덕분에 "커밋 유실 걱정 없이" 브랜치를 만들어 작업을 다른 이름으로 옮길 수 있다.
- `git reset --hard <커밋>` 은 브랜치 포인터를 그 커밋으로 옮기고 워킹 디렉터리도 그 상태로 되돌린다.
  아직 어떤 브랜치도 참조하지 않게 된 커밋은 reflog로만 되찾을 수 있으므로,
  되돌리기 전에 필요한 커밋을 가리키는 브랜치를 먼저 만들어 두는 습관이 안전하다.
- 작업 시작 전 `git status` 로 지금 어느 브랜치에 있는지 확인하는 습관이 이런 실수를 예방한다.""",
}
