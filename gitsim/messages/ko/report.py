"""`gitsim check` 가 생성하는 REPORT.md 의 고정 틀(제목/구획 이름 등)."""

MESSAGES: dict[str, str] = {
    "report.status.success": "✅ 성공",
    "report.status.pending": "❌ 아직 미완료",
    "report.no_log": "(로그 없음)",
    "report.no_reflog": "(reflog 없음)",
    "report.no_remote_log": "(원격 로그 없음)",
    "report.no_details": "(세부 정보 없음)",
    "report.no_diagnosis": "(진단할 내용 없음)",
    "report.body": """# GitSim 리포트 — {title}

- 시나리오 ID: `{scenario_id}`
- 난이도: {level}
- 생성 시각: {timestamp}
- 워크스페이스: `{workspace_path}`

## 결과

**{status_line}** — {summary}

### 검사 세부 내역
{details_block}

## 상황 설명 (이번에 주어졌던 임무)

{briefing}

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

{model_answer}

## 핵심 개념 정리

{concepts}
""",
}
