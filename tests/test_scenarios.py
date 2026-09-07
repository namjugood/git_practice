import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gitsim import gitutil as g
from gitsim.scenarios import list_scenarios
from gitsim.workspace import create_workspace


@pytest.fixture(autouse=True)
def fake_registered_remote(tmp_path, monkeypatch):
    """실제 GitHub 저장소 대신, 로컬 bare 저장소를 `gitsim remote set`으로 등록한 것처럼
    `GITSIM_REMOTE_URL` 환경 변수로 꽂아 넣는다. git 입장에서는 로컬 경로든 진짜
    원격이든 동작이 동일하므로, 네트워크 없이도 real-remote 코드 경로를 그대로 검증할 수 있다."""
    remote_path = tmp_path / "fake_remote.git"
    g.init_bare(remote_path)
    monkeypatch.setenv("GITSIM_REMOTE_URL", str(remote_path))
    yield remote_path


@pytest.mark.parametrize("scenario", list_scenarios(), ids=lambda s: s.id)
def test_scenario_lifecycle(scenario, tmp_path):
    ws = create_workspace(scenario.id, base_dir=tmp_path)
    scenario.setup(ws)

    assert (ws.repo_dir / ".git").exists()
    g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
    assert g.rev_parse(ws.repo_dir, "origin/main") is not None, "practice 브랜치가 등록된 원격에 push되지 않았습니다"

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
