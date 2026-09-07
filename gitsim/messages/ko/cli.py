"""`gitsim` CLI 명령들이 출력하는 고정 문구."""

MESSAGES: dict[str, str] = {
    "cli.list.header": "연습 가능한 시나리오 목록",
    "cli.list.footer": "gitsim start <시나리오id> 로 시작하세요. 처음이라면 `gitsim learn` 부터 시작하는 것을 추천합니다.",
    "cli.start.workspace_label": "워크스페이스: {path}",
    "cli.start.hint_cd": "cd ~/.gitsim/current 로 이동해서 작업하세요. 완료했다면 `gitsim check` 를 실행하세요.",
    "cli.start.hint_answer": "막히면 `gitsim answer` 로 모범 답안을 볼 수 있습니다 (먼저 스스로 시도해보길 권장).",
    "cli.tutorial_redirect.check": "이것은 튜토리얼 워크스페이스입니다. `gitsim learn check` 를 사용하세요.",
    "cli.tutorial_redirect.answer": "이것은 튜토리얼 워크스페이스입니다. 튜토리얼에는 단계별 힌트가 `gitsim learn` 에 포함되어 있습니다.",
    "cli.check.header": "검사 결과: {title}",
    "cli.check.details_label": "세부 내역",
    "cli.check.diagnosis_label": "진단",
    "cli.check.report_saved": "자세한 리포트가 저장되었습니다: {path}",
    "cli.check.report_pushed": (
        "연습 결과가 등록된 원격 저장소의 '{branch}' 브랜치에 README.md로 push되었습니다. "
        "그 브랜치를 열어보면 포트폴리오처럼 다른 사람과 공유할 수 있습니다."
    ),
    "cli.check.see_answer_hint": "`gitsim answer` 로 모범 답안을 확인할 수 있습니다.",
    "cli.answer.header": "모범 답안: {title}",
    "cli.answer.concepts_label": "핵심 개념",
    "cli.status.header": "워크스페이스 상태: {scenario_id}",
    "cli.status.path_label": "경로: {path}",
    "cli.status.log_label": "git log --graph --oneline --all",
    "cli.status.status_label": "git status",
    "cli.status.no_log": "(로그 없음)",
    "cli.status.clean": "(clean)",
    "cli.status.not_initialized": "아직 repo/ 에 git 저장소가 초기화되지 않았습니다.",
    "cli.reset.tutorial_done": "튜토리얼을 초기화했습니다: {path}",
    "cli.reset.scenario_done": "시나리오를 초기 상태로 다시 만들었습니다: {path}",
    "cli.learn.header": "Git 입문 튜토리얼",
    "cli.learn.reset_done": "튜토리얼을 처음부터 다시 시작합니다: {path}",
    "cli.workspaces.header": "워크스페이스 목록",
    "cli.workspaces.empty": "아직 생성된 워크스페이스가 없습니다. `gitsim start <시나리오id>` 로 시작하세요.",
    "cli.help.list": "연습 가능한 시나리오 목록 보기",
    "cli.help.start": "새 시나리오 워크스페이스 시작",
    "cli.help.start.base_dir": "워크스페이스 저장 위치 (기본: {default_root})",
    "cli.help.check": "현재 워크스페이스에서 임무 완료 여부 검사",
    "cli.help.check.dir": "워크스페이스 경로 (생략 시 현재 위치에서 자동 탐지)",
    "cli.help.answer": "모범 답안과 핵심 개념 보기",
    "cli.help.status": "현재 워크스페이스의 git 로그/상태 보기",
    "cli.help.reset": "시나리오를 처음 상태로 재구성",
    "cli.help.learn": "git 입문자를 위한 단계별 튜토리얼",
    "cli.help.workspaces": "지금까지 만든 워크스페이스 목록",
    "cli.help.remote": "연습에 사용할 실제 원격 저장소 등록/확인",
    "cli.parser.description": "실제 git과 진짜 원격 저장소로 실무 git 상황을 훈련하는 시뮬레이터",
    "cli.remote.current": "등록된 원격 저장소: {url}",
    "cli.remote.none": "아직 등록된 원격 저장소가 없습니다. `gitsim remote set <주소>` 로 등록하세요.",
    "cli.remote.url_required": "저장소 주소를 입력하세요: gitsim remote set <주소>",
    "cli.remote.unreachable": "저장소에 접근할 수 없습니다: {url}\n{detail}",
    "cli.remote.saved": "원격 저장소를 등록했습니다: {url}",
    "cli.remote.safety_notice": (
        "gitsim은 이 저장소의 'practice/*' 브랜치만 만들고 사용합니다. 기존에 있던 다른 "
        "브랜치(main, master 등)는 절대 건드리지 않습니다. 그래도 실제로 협업 중인 저장소가 "
        "아니라, 연습 전용으로 만든 저장소를 등록하는 것을 권장합니다."
    ),
    "cli.remote.existing_branches": "이 저장소에 이미 있는 브랜치: {branches} (gitsim은 건드리지 않습니다)",
}
