"""모든 훈련 시나리오가 구현해야 하는 공통 인터페이스."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gitsim.workspace import Workspace


@dataclass
class CheckResult:
    success: bool
    summary: str
    details: list[str] = field(default_factory=list)


class Scenario:
    id: str = ""
    title: str = ""
    level: str = ""  # 입문 / 초급 / 중급 / 고급
    tags: list[str] = []
    summary: str = ""

    def setup(self, ws: "Workspace") -> None:
        """워크스페이스에 실제 git 저장소/원격/사고 상황을 구성한다."""
        raise NotImplementedError

    def briefing(self, ws: "Workspace") -> str:
        """학습자에게 보여줄 상황 설명 + 임무 (정답은 포함하지 않음)."""
        raise NotImplementedError

    def check(self, ws: "Workspace") -> CheckResult:
        """현재 워크스페이스 상태가 시나리오 목표를 만족하는지 검사한다."""
        raise NotImplementedError

    def diagnose(self, ws: "Workspace") -> list[str]:
        """reflog 등 git 산출물을 근거로 학습자의 행동을 진단한다."""
        return []

    def model_answer(self, ws: "Workspace") -> str:
        """모범 답안 + 이유 설명 (markdown 텍스트)."""
        raise NotImplementedError

    def concepts(self, ws: "Workspace") -> str:
        """이 시나리오와 관련된 핵심 git 개념 정리."""
        return ""

    def reference_solution(self, ws: "Workspace") -> None:
        """테스트 전용: check()가 성공을 인식하도록 실제로 정답 명령을 수행한다."""
        raise NotImplementedError
