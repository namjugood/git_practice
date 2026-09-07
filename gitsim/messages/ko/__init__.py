"""한국어 메시지 카탈로그. 도메인별 하위 모듈의 MESSAGES를 한데 모은다.

새 로케일(예: en)을 추가하려면 이 폴더 구조를 그대로 복사해서 `gitsim/messages/en/`
을 만들고, 각 모듈의 MESSAGES 딕셔너리 값을 번역하면 된다. 키 이름은 절대 바꾸면
안 된다 (코드가 키로 참조한다).
"""

from __future__ import annotations

from gitsim.messages.ko import cli, common, report, tutorial
from gitsim.messages.ko.scenarios import (
    deleted_branch,
    diverged_history,
    force_push_incident,
    merge_conflict,
    undo_pushed_commit,
    wrong_branch_commit,
)

MESSAGES: dict[str, str] = {}
for _module in (
    common,
    cli,
    tutorial,
    report,
    merge_conflict,
    deleted_branch,
    wrong_branch_commit,
    diverged_history,
    undo_pushed_commit,
    force_push_incident,
):
    MESSAGES.update(_module.MESSAGES)
