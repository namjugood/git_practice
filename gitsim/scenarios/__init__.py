from __future__ import annotations

from gitsim.i18n import t as _
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.scenarios.deleted_branch import DeletedBranchScenario
from gitsim.scenarios.diverged_history import DivergedHistoryScenario
from gitsim.scenarios.force_push_incident import ForcePushIncidentScenario
from gitsim.scenarios.merge_conflict import MergeConflictScenario
from gitsim.scenarios.undo_pushed_commit import UndoPushedCommitScenario
from gitsim.scenarios.wrong_branch_commit import WrongBranchCommitScenario

_REGISTRY: dict[str, Scenario] = {
    s.id: s
    for s in (
        MergeConflictScenario(),
        DeletedBranchScenario(),
        WrongBranchCommitScenario(),
        DivergedHistoryScenario(),
        ForcePushIncidentScenario(),
        UndoPushedCommitScenario(),
    )
}

# 학습 난이도(입문 -> 고급) 순으로 노출하기 위한 순서 목록.
ORDER = [
    "merge-conflict",
    "wrong-branch-commit",
    "deleted-branch",
    "diverged-history",
    "undo-pushed-commit",
    "force-push-incident",
]


def list_scenarios() -> list[Scenario]:
    return [_REGISTRY[i] for i in ORDER]


def get_scenario(scenario_id: str) -> Scenario:
    if scenario_id not in _REGISTRY:
        available = ", ".join(ORDER)
        raise KeyError(_("common.unknown_scenario", scenario_id=scenario_id, available=available))
    return _REGISTRY[scenario_id]


__all__ = ["Scenario", "CheckResult", "list_scenarios", "get_scenario", "ORDER"]
