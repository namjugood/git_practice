"""시나리오: deleted-branch."""

MESSAGES: dict[str, str] = {
    "scenario.deleted_branch.title": "실수로 삭제한 브랜치 복구하기",
    "scenario.deleted_branch.level": "중급",
    "scenario.deleted_branch.summary": "커밋이 남아있는 브랜치를 실수로 삭제한 상황에서 reflog로 복구한다.",
    "scenario.deleted_branch.commit.initial": "초기 커밋",
    "scenario.deleted_branch.commit.login": "feat: 로그인 함수 추가",
    "scenario.deleted_branch.commit.logout": "feat: 로그아웃 함수 추가",
    "scenario.deleted_branch.briefing": """[상황]
어제까지 `feature/login` 브랜치에서 로그인/로그아웃 기능을 작업했습니다.
그런데 방금 실수로 아래 명령을 실행해서 브랜치를 삭제해버렸습니다.

    git branch -D feature/login

커밋 자체는 아직 git 내부 어딘가에 남아있을 가능성이 높습니다.

[임무]
1. 삭제하기 전 마지막 커밋을 찾아내세요. (`git reflog` 가 힌트를 줍니다)
2. 그 커밋을 가리키는 브랜치를 다시 만들어 작업을 복구하세요.
   (브랜치 이름은 `feature/login` 이 아니어도 되지만, 그대로 복구하는 것을 권장합니다)

작업 위치: cd ~/.gitsim/current
  (이 경로로 이동이 안 되면, 아래 실제 경로를 대신 사용하세요: {repo_dir})""",
    "scenario.deleted_branch.check.object_gone": "삭제된 커밋 오브젝트 자체를 git DB에서 더 이상 찾을 수 없습니다 (gc로 소실되었을 수 있음).",
    "scenario.deleted_branch.check.not_found": "복구할 커밋을 찾지 못했습니다.",
    "scenario.deleted_branch.check.detail_owners": "해당 커밋을 포함하는 브랜치들: {owners}",
    "scenario.deleted_branch.check.none": "없음",
    "scenario.deleted_branch.check.no_owner": "아직 어떤 브랜치도 해당 커밋을 가리키고 있지 않습니다.",
    "scenario.deleted_branch.check.success": "브랜치 {owners}가 로그인 기능 커밋을 다시 가리키도록 복구했습니다.",
    "scenario.deleted_branch.diagnose.new_branch_found": "`branch: Created from ...` reflog 기록이 확인됩니다. 브랜치를 새로 만들어 복구를 시도했습니다.",
    "scenario.deleted_branch.diagnose.new_branch_missing": "새 브랜치 생성 기록이 보이지 않습니다. `git branch <이름> <커밋 해시>` 로 브랜치를 다시 만들어야 합니다.",
    "scenario.deleted_branch.diagnose.habit_tip": "실수를 막으려면 `git branch -d`(소문자, merge 안 된 브랜치는 삭제를 거부)를 기본으로 쓰고, `-D`(강제 삭제)는 정말 필요할 때만 신중하게 사용하세요.",
    "scenario.deleted_branch.model_answer": """1. `git reflog`
   → HEAD가 거쳐온 기록이 시간 역순으로 나온다. 삭제 직전 `feature/login` 위에서
     작업하며 만든 `commit: feat: 로그아웃 함수 추가` 같은 항목을 찾는다.
     (이번 상황의 실제 커밋 해시: {commit_short})
2. `git branch feature/login {commit_short}`
   → 찾은 커밋을 가리키는 브랜치를 다시 만든다. (`git checkout -b` 로 바로 이동까지 해도 된다)
3. `git log feature/login` 로 로그인/로그아웃 커밋이 모두 돌아왔는지 확인.
4. 필요하면 `git push -u origin feature/login` 으로 원격에도 백업.

핵심: git은 브랜치를 지워도 커밋 오브젝트 자체를 즉시 지우지 않는다.
브랜치는 커밋을 가리키는 "이름표"일 뿐이라, 이름표만 다시 붙이면 복구된다.
단, 시간이 지나 `git gc` 가 실행되면 어떤 브랜치도 가리키지 않는 커밋은 정말로 삭제될 수 있으니
사고를 인지한 즉시 복구하는 것이 중요하다.""",
    "scenario.deleted_branch.concepts": """- **reflog**: HEAD와 각 브랜치가 가리켰던 커밋의 변경 이력을 로컬에 기록한 것. `git log` 와 달리
  브랜치에서 떨어져 나간(dangling) 커밋도 한동안 추적할 수 있게 해준다.
- 브랜치 삭제는 커밋을 지우는 것이 아니라 "이름표"를 떼는 것이다. 참조하는 이름표가 하나도 없는
  커밋만 나중에 `git gc` 로 정리 대상이 된다.
- `git branch -d`(안전, merge 안 되면 거부) vs `git branch -D`(강제, 미병합 커밋도 삭제) 차이를 기억하자.""",
}
