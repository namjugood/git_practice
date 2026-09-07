import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gitsim.scenarios import list_scenarios
from gitsim.workspace import create_workspace


@pytest.mark.parametrize("scenario", list_scenarios(), ids=lambda s: s.id)
def test_scenario_lifecycle(scenario, tmp_path):
    ws = create_workspace(scenario.id, base_dir=tmp_path)
    scenario.setup(ws)

    assert (ws.repo_dir / ".git").exists()
    assert ws.remote_dir.exists()

    briefing = scenario.briefing(ws)
    assert isinstance(briefing, str) and briefing.strip()

    before = scenario.check(ws)
    assert before.success is False, f"{scenario.id}: 시작 상태에서 이미 성공으로 판정됨 (초기 상태 설계 오류)"

    scenario.reference_solution(ws)

    after = scenario.check(ws)
    assert after.success is True, f"{scenario.id}: 정답 명령을 실행했는데도 실패로 판정됨 -> {after.summary}\n{after.details}"

    diagnosis = scenario.diagnose(ws)
    assert isinstance(diagnosis, list)

    answer = scenario.model_answer(ws)
    concepts = scenario.concepts(ws)
    assert isinstance(answer, str) and answer.strip()
    assert isinstance(concepts, str) and concepts.strip()

    shutil.rmtree(ws.path, ignore_errors=True)


def test_scenario_ids_unique():
    ids = [s.id for s in list_scenarios()]
    assert len(ids) == len(set(ids))
