"""`gitsim learn` (git 입문 튜토리얼)이 사용하는 모든 문구."""

MESSAGES: dict[str, str] = {
    "tutorial.intro": """처음이시군요! git도 터미널도 낯설어도 전혀 문제 없습니다. 아래 순서대로만 따라오세요.

[1] 터미널이 뭔가요?
    글자로 명령을 입력해서 컴퓨터에게 작업을 시키는 화면입니다.
    - macOS: Spotlight(Cmd+Space)에서 "터미널(Terminal)" 검색 후 실행
    - Windows: 시작 메뉴에서 "PowerShell" 검색 후 실행
    - VS Code를 쓰고 있다면: 상단 메뉴 Terminal > New Terminal

[2] git이 뭔가요?
    파일이 바뀐 역사를 기록해두었다가, 언제든 예전 상태로 되돌리거나 여러 사람의
    작업 내용을 합칠 수 있게 해주는 도구입니다. 그 기록이 저장되는 폴더를
    "저장소(repository)"라고 부릅니다.

[3] 앞으로 어떻게 진행되나요?
    단계 중 일부는 그대로 복사해서 붙여넣으면 바로 실행되는 완성된 명령을
    보여줍니다. 하지만 이름, 이메일, 커밋 메시지, 브랜치 이름처럼 "직접 정해야
    하는 값"이 필요한 단계는 일부러 빈칸/설명만 드립니다. 그대로 복사하면
    손에 남는 게 없기 때문입니다 — 명령의 형태를 보고 실제 값을 채워서 스스로
    입력해보세요. 완료했는지는 `gitsim learn check` 로 확인합니다.

[4] 시작하기 전에 딱 한 번만
    터미널을 열고, 아래 명령으로 이 프로젝트를 설치해서 `gitsim` 명령을
    바로 쓸 수 있게 해두세요. (프로젝트 폴더 안에서 한 번만 실행하면 됩니다)

      pip install -e .

    이제 아래 STEP 1부터 순서대로 진행하면 됩니다.""",
    "tutorial.placeholder.name": "본인 이름",
    "tutorial.placeholder.email": "본인 이메일",
    "tutorial.require_main": (
        "이 저장소에는 'main' 이라는 이름의 브랜치가 없습니다. (지금 있는 브랜치: {branch_list} / 현재 위치: {current})\n"
        "이 튜토리얼은 기본 브랜치 이름이 반드시 'main' 이어야 진행됩니다. 아래 중 지금 상황에 맞는 것을 실행하세요.\n\n"
        "  - 'master' 브랜치가 있고 그게 사실상 main 역할을 해야 한다면:\n"
        "      git checkout master\n"
        "      git branch -m main\n\n"
        "  - 지금 있는 브랜치({current})가 main 역할을 해야 한다면:\n"
        "      git branch -m {current} main\n\n"
        "이름을 바꾼 뒤에는 이 저장소 위에서 만들었던 다른 브랜치(예: 연습용 브랜치)들이 "
        "여전히 main을 기준으로 갈라져 있는지 `git log --oneline --graph --all` 로 확인해보세요."
    ),
    "tutorial.require_main.no_branch": "(브랜치가 하나도 없음)",
    "tutorial.require_main.unknown_position": "알 수 없음",
    "tutorial.require_main.unknown_branch": "<현재 브랜치>",
    # --- 단계별 진단(diagnose) 메시지 ---
    "tutorial.diagnose.init.not_repo": (
        "아직 이 폴더가 git 저장소로 초기화되지 않았습니다. 지금 명령을 실행한 폴더가\n"
        "  {repo_dir}\n"
        "가 맞는지 확인한 뒤 `git init -b main` 을 실행하세요."
    ),
    "tutorial.diagnose.init.wrong_branch": "저장소는 만들어졌지만 현재 브랜치 이름이 'main'이 아니라 '{branch}' 입니다. `git branch -m main` 으로 이름을 바꾸세요.",
    "tutorial.diagnose.identity.not_set": (
        "이 저장소에는 아직 이름/이메일이 설정되어 있지 않습니다 (지금 값: 이름='{name}', 이메일='{email}').\n"
        "`git config user.name`, `git config user.email` 을 이 저장소 안에서 실행했는지 확인하세요."
    ),
    "tutorial.diagnose.identity.placeholder": "예시 문구가 그대로 남아있습니다 (이름='{name}', 이메일='{email}'). 실제 본인 이름/이메일로 바꿔서 다시 입력하세요.",
    "tutorial.diagnose.identity.bad_email": "이메일에 '@' 가 없습니다 (지금 값: '{email}'). 이메일 형식으로 다시 입력하세요.",
    "tutorial.diagnose.identity.looks_ok": "현재 설정된 값은 이름='{name}', 이메일='{email}' 입니다. 정상으로 보이는데도 실패한다면 `gitsim learn check` 를 다시 실행해보세요.",
    "tutorial.diagnose.first_commit.uncommitted": (
        "아직 커밋되지 않은 변경 사항이 있습니다:\n"
        "{status}\n"
        '`git add <파일 이름>` 으로 스테이징한 뒤 `git commit -m "메시지"` 를 실행하세요.'
    ),
    "tutorial.diagnose.first_commit.none": '아직 이 저장소에 커밋이 하나도 없습니다. 파일을 만들고 `git add`, `git commit -m "메시지"` 를 실행하세요.',
    "tutorial.diagnose.branch.still_main": "아직 main 브랜치에 그대로 있습니다. `git checkout -b <원하는 브랜치 이름>` 으로 새 브랜치를 만들고 그 브랜치로 이동해야 합니다.",
    "tutorial.diagnose.branch.detached": "지금 어떤 브랜치에도 있지 않은 상태(detached HEAD)로 보입니다. `git checkout -b <원하는 브랜치 이름>` 을 다시 실행하세요.",
    "tutorial.diagnose.branch.looks_ok": "현재 브랜치는 '{branch}' 로 보이는데도 실패했습니다. `gitsim learn check` 를 다시 실행해보세요.",
    "tutorial.diagnose.branch_commit.no_remembered": "3번 단계에서 만든 브랜치 이름이 기록되어 있지 않습니다. `gitsim learn reset` 으로 처음부터 다시 시작해야 할 수 있습니다.",
    "tutorial.diagnose.branch_commit.wrong_branch": (
        "3번 단계에서 만든 브랜치는 '{remembered}' 인데, 지금 체크아웃되어 있는 브랜치는 "
        "'{current}' 입니다. `git checkout {remembered}` 로 그 브랜치로 돌아가서 커밋하세요."
    ),
    "tutorial.diagnose.branch_commit.no_new_commit": (
        '\'{remembered}\' 브랜치가 main과 똑같아서 아직 새 커밋이 없는 것으로 보입니다. '
        '파일을 수정/생성하고 `git add`, `git commit -m "메시지"` 를 실행하세요.'
    ),
    "tutorial.diagnose.branch_commit.diverged": (
        "'{remembered}' 브랜치에 커밋은 있지만, main의 최신 상태 위에 이어진 게 아니라 "
        "main과 서로 다른 방향으로 갈라져 있습니다. (브랜치를 지웠다가 main이 아닌 다른 "
        "지점에서 다시 만들었을 때 이런 상태가 됩니다.) 아래처럼 main을 기준으로 깨끗하게 "
        "다시 만들어보세요:\n"
        "  git checkout main\n"
        "  git branch -D {remembered}\n"
        "  git checkout -b {remembered}\n"
        "그런 다음 파일을 수정/생성하고 다시 커밋하세요."
    ),
    "tutorial.diagnose.branch_commit.looks_ok": "'{remembered}' 브랜치에 커밋은 있는 것 같은데도 실패했습니다. `gitsim learn check` 를 다시 실행해보세요.",
    "tutorial.diagnose.merge.not_on_main": "지금 브랜치가 'main'이 아니라 '{current}' 입니다. 먼저 `git checkout main` 을 실행하세요.",
    "tutorial.diagnose.merge.not_merged": "main이 아직 '{branch}' 브랜치를 포함하고 있지 않습니다. `git merge {branch}` 를 실행하세요.",
    "tutorial.diagnose.remote.no_origin": "'origin' 이라는 이름의 원격이 아직 등록되지 않았습니다. `git remote add origin {remote_url}` 을 실행하세요.",
    "tutorial.diagnose.remote.not_pushed": "origin은 등록되었지만 아직 {branch} 브랜치가 push되지 않았습니다. `git push -u origin main:{branch}` 를 실행하세요.",
    "tutorial.diagnose.remote.mismatch": "원격의 {branch} 브랜치가 로컬 main과 다릅니다. `git push -u origin main:{branch}` 를 다시 실행해보세요.",
    "tutorial.diagnose.remote.looks_ok": "origin 등록과 push까지는 되어 보이는데도 실패했습니다. `gitsim learn check` 를 다시 실행해보세요.",
    "tutorial.diagnose.pull.not_pulled": "아직 동료의 커밋(teammate_note.txt)을 받아오지 않은 것 같습니다. `git pull` 을 실행하세요.",
    # --- 단계 본문 ---
    "tutorial.step.init.title": "0. 저장소 만들기 (git init)",
    "tutorial.step.init.explain": (
        "git으로 무언가를 관리하려면 먼저 그 폴더를 'git 저장소'로 만들어야 합니다.\n"
        "(컴퓨터 설정에 따라 기본 브랜치 이름이 'master'가 될 수도 있어서, 이 튜토리얼에서는\n"
        "'main'으로 이름을 고정하는 옵션(-b main)을 함께 사용합니다)"
    ),
    "tutorial.step.init.command_hint": "git init -b main",
    "tutorial.step.identity.title": "1. 커밋 작성자 정보 설정하기 (git config)",
    "tutorial.step.identity.explain": (
        "모든 커밋에는 '누가 만들었는지' 기록이 남습니다. 아래는 명령의 형태만\n"
        "보여드립니다 — 따옴표 안 문구를 실제 본인 이름/이메일로 바꿔서 두 줄 모두\n"
        "직접 입력하세요. 예시 문구를 그대로 실행하면 통과되지 않습니다."
    ),
    "tutorial.step.identity.command_hint": (
        'git config user.name "{placeholder_name}"          (← 이 문구를 실제 이름으로 바꿔서 입력)\n'
        '  git config user.email "{placeholder_email}@example.com"  (← 실제 이메일로 바꿔서 입력)'
    ),
    "tutorial.step.first_commit.title": "2. 첫 커밋 만들기 (add, commit)",
    "tutorial.step.first_commit.explain": (
        "git은 파일을 '스테이징(add)'한 뒤 '커밋(commit)'해야 변경 이력으로 저장합니다.\n"
        "아무 이름으로나 텍스트 파일을 하나 직접 만들고 원하는 내용을 적어보세요.\n"
        "그 다음 아래 형태의 명령으로 스테이징하고, 커밋 메시지도 직접 지어서 커밋하세요."
    ),
    "tutorial.step.first_commit.command_hint": (
        "git add <방금 만든 파일 이름>\n"
        '  git commit -m "<자유롭게 지은 커밋 메시지>"'
    ),
    "tutorial.step.branch.title": "3. 브랜치 만들고 이동하기",
    "tutorial.step.branch.explain": (
        "브랜치는 독립된 작업 공간입니다. 실험적인 작업을 할 때 main을 건드리지 않고\n"
        "새 브랜치에서 작업할 수 있습니다. 브랜치 이름을 원하는 대로 하나 지어보세요."
    ),
    "tutorial.step.branch.command_hint": "git checkout -b <원하는 브랜치 이름>",
    "tutorial.step.branch_commit.title": "4. 브랜치에서 커밋 추가하기",
    "tutorial.step.branch_commit.explain": "지금 브랜치 위에서 파일을 수정하거나 새로 만들고, 커밋 메시지도 직접 지어서 커밋 하나를 추가하세요.",
    "tutorial.step.branch_commit.command_hint": (
        "git add <파일 이름>\n"
        '  git commit -m "<자유롭게 지은 커밋 메시지>"'
    ),
    "tutorial.step.merge.title": "5. main으로 돌아와 병합하기 (merge)",
    "tutorial.step.merge.explain": "main으로 돌아가서 방금 만든 브랜치({practice_branch})의 작업을 병합해보세요.",
    "tutorial.step.merge.command_hint": "git checkout main\n  git merge {practice_branch}",
    "tutorial.step.remote.title": "6. 원격 저장소 연결하고 업로드하기 (remote, push)",
    "tutorial.step.remote.explain": (
        "실무에서는 GitHub 같은 실제 원격 저장소에 코드를 올려 협업합니다. 이번 실습부터는\n"
        "직접 등록하신 진짜 원격 저장소를 사용합니다.\n"
        "\n"
        "    등록된 저장소: {remote_url}\n"
        "    이번 실습 전용 브랜치: {remote_branch}\n"
        "\n"
        "이 브랜치 이름은 gitsim이 실습마다 자동으로 고유하게 만들어줍니다 — 나중에 다시\n"
        "연습해도 예전 기록을 덮어쓰지 않고 계속 남아있습니다."
    ),
    "tutorial.step.remote.command_hint": "git remote add origin {remote_url}\n  git push -u origin main:{remote_branch}",
    "tutorial.step.remote.not_registered": (
        "이 단계부터는 실제 원격 저장소(GitHub 등)가 필요합니다. 아직 등록되지 않았습니다.\n\n"
        "1. GitHub 등에서 연습 전용으로 쓸 빈 저장소를 하나 만드세요. (기존에 쓰던 저장소 말고,\n"
        "   새로 만든 저장소를 권장합니다 — gitsim이 여기에 여러 연습 기록을 남깁니다)\n"
        "2. 그 저장소 주소로 아래 명령을 실행해서 gitsim에 등록하세요.\n\n"
        "     gitsim remote set <저장소 주소>\n\n"
        "3. 등록한 뒤 `gitsim learn` 을 다시 실행하면 이 단계로 돌아옵니다."
    ),
    "tutorial.step.pull.title": "7. 원격의 변경 사항 받아오기 (fetch/pull)",
    "tutorial.step.pull.explain": (
        "방금 동료가 원격 저장소의 {remote_branch} 브랜치에 teammate_note.txt 파일을 추가하고\n"
        "push 했습니다. 당신의 로컬 저장소에는 아직 이 파일이 없습니다. pull로 받아오세요.\n"
        "(바로 앞 단계에서 `push -u` 로 이미 main과 {remote_branch} 를 연결해뒀으므로,\n"
        "브랜치 이름 없이 `git pull` 만 실행해도 자동으로 어디서 받아올지 압니다)"
    ),
    "tutorial.step.pull.command_hint": "git pull",
    "tutorial.fallback_branch_label": "<앞에서 만든 브랜치>",
    # --- 단계 화면 골격 ---
    "tutorial.step_block.header": "STEP {n}/{total}: {title}",
    "tutorial.step_block.check_location_title": "[먼저 확인하세요] 지금 터미널이 연습용 폴더에 있나요?",
    "tutorial.step_block.cd_hint": "  cd ~/.gitsim/current",
    "tutorial.step_block.cd_fallback": "  (위 경로로 이동이 안 되면, 아래 실제 경로로 대신 이동하세요)",
    "tutorial.step_block.real_path": "  실제 경로: {repo_dir}",
    "tutorial.step_block.template_body": "  아래 명령을 그대로 입력하세요 (한 줄씩 따로 입력해도 됩니다):\n\n  {hint}",
    "tutorial.step_block.compose_body": (
        "  아래는 그대로 실행되는 완성된 명령이 아니라 '형태'입니다. 예시로 채워진 값이나\n"
        "  <...> 표시된 부분을 직접 정한 실제 값으로 바꿔서, 손으로 입력해보세요:\n\n  {hint}"
    ),
    "tutorial.step_block.final_hint": "다 입력했다면 이 명령으로 확인하세요: gitsim learn check",
    "tutorial.completed": (
        "모든 튜토리얼 단계를 완료했습니다! 🎉\n"
        "이제 `gitsim list` 로 실무 시나리오 목록을 확인하고 `gitsim start <시나리오id>` 로 "
        "실전 연습을 시작해보세요."
    ),
    "tutorial.check.already_done": "이미 모든 단계를 완료했습니다.",
    "tutorial.check.success": "'{title}' 단계를 완료했습니다!",
    "tutorial.check.failed": "'{title}' 단계가 아직 완료되지 않았습니다.\n\n[진단] {detail}",
    "tutorial.check.default_compose_hint": "예시 문구를 그대로 실행하지 않았는지, 실제 값으로 바꿔서 입력했는지 확인해보세요.",
    "tutorial.check.default_template_hint": "위에 안내된 명령을 실행해보세요.",
}
