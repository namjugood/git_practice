"""여러 모듈에서 공통으로 쓰는 짧은 라벨."""

MESSAGES: dict[str, str] = {
    "common.ok_label": "성공",
    "common.fail_label": "미완료",
    "common.warn_label": "주의",
    "common.git_error": "git {args} 실패 (exit={returncode}): {detail}",
    "common.workspace_not_found": (
        "현재 위치에서 gitsim 워크스페이스를 찾을 수 없습니다. "
        "연습 중이던 repo 디렉터리 안에서 실행하거나 --dir 옵션으로 경로를 지정하세요."
    ),
    "common.workspace_invalid": "{path} 는 gitsim 워크스페이스가 아닙니다 (.gitsim.json 없음)",
    "common.unknown_scenario": "알 수 없는 시나리오 id '{scenario_id}'. 사용 가능한 목록: {available}",
    "common.remote_not_registered": (
        "아직 실제 원격 저장소가 등록되지 않았습니다. 먼저 다음을 실행하세요:\n"
        "  gitsim remote set <GitHub 저장소 주소>"
    ),
}
