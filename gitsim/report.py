"""`gitsim check` 결과를 실제 git 산출물과 함께 markdown 리포트로 정리한다."""

from __future__ import annotations

import time

from gitsim import gitutil as g
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace


def build_report(scenario: Scenario, ws: Workspace, result: CheckResult, diagnosis: list[str]) -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status_line = "✅ 성공" if result.success else "❌ 아직 미완료"
    log_graph = g.log_graph(ws.repo_dir) or "(로그 없음)"
    reflog_text = g.reflog(ws.repo_dir) or "(reflog 없음)"
    remote_log = ""
    if ws.remote_dir.exists():
        remote_log = g.log_graph(ws.remote_dir) or "(원격 로그 없음)"

    details_block = "\n".join(f"- {d}" for d in result.details) or "- (세부 정보 없음)"
    diagnosis_block = "\n".join(f"- {d}" for d in diagnosis) or "- (진단할 내용 없음)"

    return f"""# GitSim 리포트 — {scenario.title}

- 시나리오 ID: `{scenario.id}`
- 난이도: {scenario.level}
- 생성 시각: {timestamp}
- 워크스페이스: `{ws.path}`

## 결과

**{status_line}** — {result.summary}

### 검사 세부 내역
{details_block}

## 상황 설명 (이번에 주어졌던 임무)

{scenario.briefing(ws)}

## 당신의 Git 히스토리 (실제 `git log --graph --oneline --all` 산출물)

```
{log_graph}
```

## Reflog — 당신이 실행한 ref 변경 명령의 실제 기록

```
{reflog_text}
```

## 원격 저장소(origin) 히스토리

```
{remote_log}
```

## 진단 결과 (잘한 점 / 놓친 점)

{diagnosis_block}

## 모범 답안

{scenario.model_answer(ws)}

## 핵심 개념 정리

{scenario.concepts(ws)}
"""


def write_report(scenario: Scenario, ws: Workspace, result: CheckResult, diagnosis: list[str]) -> None:
    ws.report_file.write_text(build_report(scenario, ws, result, diagnosis), encoding="utf-8")
