"""시나리오: merge-conflict."""

MESSAGES: dict[str, str] = {
    "scenario.merge_conflict.title": "병합 충돌(merge conflict) 해결하기",
    "scenario.merge_conflict.level": "초급",
    "scenario.merge_conflict.summary": "같은 파일의 같은 줄을 서로 다르게 고친 두 브랜치를 병합하며 충돌을 직접 해결한다.",
    "scenario.merge_conflict.recipe_initial": "# 오늘의 레시피\n\n1. 재료를 준비한다\n2. 재료를 손질한다\n3. 30분간 조리한다\n",
    "scenario.merge_conflict.recipe_line_original": "3. 30분간 조리한다\n",
    "scenario.merge_conflict.recipe_line_teammate": "3. 강불로 15분간 조리한다\n",
    "scenario.merge_conflict.recipe_line_mine": "3. 약불로 45분간 은근히 조리한다\n",
    "scenario.merge_conflict.commit.base": "초기 레시피 작성",
    "scenario.merge_conflict.commit.teammate": "팀원 B: 화력을 강불로 변경",
    "scenario.merge_conflict.commit.mine": "나: 약불로 오래 조리하도록 변경",
    "scenario.merge_conflict.briefing": """[상황]
당신과 팀원 B는 같은 저장소의 `recipe.md`를 함께 수정하고 있습니다.
팀원 B가 조금 전 3번째 줄(조리 방법)을 수정해서 원격(origin/main)에 먼저 push 했습니다.
당신도 모르고 같은 줄을 다르게 수정해서 로컬에 커밋을 만들어 두었습니다 (아직 push 전).

[임무]
1. 원격의 최신 변경 사항을 받아오세요.
2. 당신의 변경 사항과 병합(merge)하세요. 같은 줄이 겹치므로 충돌(conflict)이 발생합니다.
3. `recipe.md` 를 열어 두 사람의 의도를 모두 살리는 방향으로 충돌을 해결하세요.
   (한쪽 것만 그대로 선택하지 말고, 내용을 실제로 합치는 것을 권장합니다)
4. 충돌 해결을 완료하고 커밋한 뒤, 원격(origin/main)에 push 하세요.

작업 위치: cd ~/.gitsim/current
  (이 경로로 이동이 안 되면, 아래 실제 경로를 대신 사용하세요: {repo_dir})""",
    "scenario.merge_conflict.check.no_remote_main": "원격 저장소(origin)에 main 브랜치가 없습니다.",
    "scenario.merge_conflict.check.detail_includes_teammate": "원격 main이 팀원 B의 커밋을 포함하는가: {value}",
    "scenario.merge_conflict.check.detail_includes_mine": "원격 main이 나의 커밋을 포함하는가: {value}",
    "scenario.merge_conflict.check.not_all_reflected": "아직 두 사람의 변경 사항이 모두 원격 main에 반영되지 않았습니다.",
    "scenario.merge_conflict.check.detail_conflict_markers": "충돌 마커(<<<<<<<, =======, >>>>>>>)가 그대로 push 되었습니다.",
    "scenario.merge_conflict.check.conflict_markers_left": "충돌 마커를 지우지 않고 커밋/push 했습니다.",
    "scenario.merge_conflict.check.detail_dirty": "작업 디렉터리에 아직 커밋되지 않은 변경이 남아있습니다.",
    "scenario.merge_conflict.check.dirty": "작업 디렉터리를 정리(커밋)하지 않았습니다.",
    "scenario.merge_conflict.check.success": "두 사람의 변경 사항을 모두 살려 충돌을 해결하고 원격에 반영했습니다.",
    "scenario.merge_conflict.diagnose.abort_used": "`git merge --abort` 로 병합을 중단했던 기록이 있습니다. 다시 시도하는 것은 괜찮지만, 충돌은 피할 수 없으니 직접 해결하는 연습이 필요합니다.",
    "scenario.merge_conflict.diagnose.reset_hard_used": "`git reset --hard` 사용 기록이 있습니다. 병합 충돌 상황에서 reset --hard로 내 변경 사항을 통째로 버리면 팀원의 의견만 남고 내 작업은 사라집니다. 가능하면 내용을 합치는 방향을 먼저 시도하세요.",
    "scenario.merge_conflict.diagnose.merge_used": "`git merge` 관련 동작이 감지되었습니다.",
    "scenario.merge_conflict.diagnose.merge_not_detected": "merge 관련 reflog 동작이 감지되지 않았습니다. fetch 이후 merge(또는 pull)를 실행했는지 확인하세요.",
    "scenario.merge_conflict.model_answer": """1. `git fetch origin`                → 원격의 최신 커밋 정보를 받아온다 (아직 내 브랜치에 합치지 않음).
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

핵심: 충돌은 "누구 것을 지울까"가 아니라 "두 변경을 어떻게 합칠까"의 문제입니다.""",
    "scenario.merge_conflict.concepts": """- **merge conflict**: 두 브랜치가 같은 파일의 같은 부분을 다르게 바꿨을 때, git이 자동으로 합칠 수 없어 사람에게 판단을 맡기는 상태.
- `git fetch` 는 원격 정보를 받아오기만 하고 내 브랜치를 바꾸지 않는다. 실제로 합치려면 `merge`(또는 `rebase`, `pull`)가 필요하다.
- 충돌 마커 `<<<<<<<`, `=======`, `>>>>>>>` 는 반드시 지우고 원하는 최종 내용만 남겨야 한다.
- `git merge --abort` 는 병합 시도 이전 상태로 완전히 되돌린다 (충돌 해결이 막막할 때 안전하게 재시도 가능).""",
}
