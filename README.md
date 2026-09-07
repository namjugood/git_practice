# gitsim — 실무 Git 상황 훈련 시뮬레이터

`gitsim`은 실제 `git` 바이너리와, 로컬에 만든 진짜 bare 저장소("원격 저장소" 역할)를 이용해
merge conflict, 브랜치 삭제, 강제 푸시 사고 같은 실무에서 자주 벌어지는 상황을 **직접
겪어보고 스스로 해결**하도록 만든 CLI 시뮬레이터입니다. 가짜로 흉내만 내는 것이 아니라,
정말로 `git init`, `git clone`, `git push`, `git merge` 등을 실행해서 만든 저장소 위에서
학습자가 실제 `git` 명령으로 문제를 해결합니다.

풀어야 할 임무를 완료하면 `gitsim check` 가 실제 git 로그·reflog를 근거로 성공 여부를
판정하고, **무엇을 잘했고 무엇을 놓쳤는지 진단**과 **모범 답안**을 함께 담은 리포트
(`REPORT.md`)를 만들어줍니다.

## 왜 이런 구조인가

1. **git을 처음 쓰는 사람도 따라올 수 있어야 한다** → `gitsim learn` 단계별 튜토리얼
2. **실무 사고 상황을 재현하고, 사후 분석(무엇을 잘못했고 어떻게 했어야 하는지)까지
   제공해야 한다** → 각 시나리오의 `gitsim check` / `gitsim answer` / `REPORT.md`

## 설치

Python 3.9 이상과 `git` 이 설치되어 있으면 됩니다. 외부 의존성은 없습니다.

```bash
pip install -e .
gitsim --help
```

또는 설치 없이 바로 실행:

```bash
python3 -m gitsim --help
```

## 빠른 시작

### 1) git이 처음이라면 — 입문 튜토리얼

```bash
gitsim learn            # 현재 단계 안내 (워크스페이스가 없으면 새로 만듦)
cd ~/.gitsim/workspaces/tutorial-*/repo
git init                # 안내대로 명령을 하나씩 따라 하기
gitsim learn check      # 이번 단계를 완료했는지 검사, 통과하면 다음 단계 안내
```

`init` → 첫 커밋 → 브랜치 생성/이동 → 브랜치에서 커밋 → main으로 merge →
원격(origin) 연결 및 push → 동료가 올린 변경사항 pull 받기, 총 7단계로 구성되어
있습니다. `gitsim learn reset` 으로 언제든 처음부터 다시 시작할 수 있습니다.

### 2) 실무 시나리오 훈련

```bash
gitsim list                       # 연습 가능한 시나리오 목록
gitsim start merge-conflict       # 워크스페이스 생성 + 상황(임무) 브리핑 출력
cd <출력된 repo 경로>
# ... 실제 git 명령으로 문제 해결 ...
gitsim check                      # 성공 여부 판정 + REPORT.md 생성
gitsim answer                     # (필요하면) 모범 답안 + 핵심 개념 보기
gitsim status                     # 현재 git 로그/상태 보기
gitsim reset                      # 시나리오를 처음 상태로 재구성
```

`gitsim check` 는 실행 위치(현재 디렉터리)에서 워크스페이스를 자동으로 찾습니다.
다른 위치에서 실행하려면 `--dir <워크스페이스 경로>` 를 사용하세요.

## 제공하는 시나리오

| id | 난이도 | 상황 |
|---|---|---|
| `merge-conflict` | 초급 | 같은 파일의 같은 줄을 서로 다르게 고친 두 브랜치를 병합하며 충돌을 직접 해결 |
| `wrong-branch-commit` | 초급 | 브랜치를 만들지 않고 main에 바로 쌓아버린 커밋을 올바른 브랜치로 옮기고 main 복구 |
| `deleted-branch` | 중급 | `git branch -D` 로 실수로 지운 브랜치를 reflog로 복구 |
| `diverged-history` | 중급 | push가 거부(non-fast-forward)되는 상황을 fetch + merge/rebase로 해결 |
| `undo-pushed-commit` | 중급 | 이미 push되어 동료가 pull 받은 버그 커밋을 히스토리 재작성 없이 `revert` |
| `force-push-incident` | 고급 | 실수로 `--force` push해서 사라진 동료의 커밋을 동료 로컬 클론으로 복구 |

각 시나리오는 다음을 함께 제공합니다.

- **briefing**: 무슨 일이 있었는지 + 지금 해야 할 임무 (정답은 알려주지 않음)
- **check**: 실제 git 오브젝트/ref 상태를 근거로 한 성공 판정 (fetch, ancestor 검사,
  파일 내용 검사, reflog 분석 등)
- **diagnose**: reflog 등 git이 실제로 남긴 기록을 근거로 "무엇을 잘했고 무엇이 위험했는지"
  진단 (예: 공유 브랜치에 강제 push를 했는지, reset을 먼저 해서 커밋을 위험하게 만들진
  않았는지 등)
- **model_answer / concepts**: 모범 답안 명령어와 그 이유, 관련 핵심 개념 정리

## 워크스페이스 구조

`gitsim start`/`gitsim learn` 은 기본적으로 `~/.gitsim/workspaces/` 아래에 시나리오별
디렉터리를 만듭니다 (`--base-dir` 로 변경 가능).

```
<workspace>/
├── .gitsim.json      # 메타데이터 (시나리오 id, 진행 상태, 저장된 커밋 해시 등)
├── repo/              # 학습자가 실제로 git 명령을 실행하는 로컬 저장소
├── remote.git/        # "원격 저장소" 역할을 하는 로컬 bare 저장소 (origin)
├── teammate_clone/    # 일부 시나리오에서 "동료의 로컬 클론" 역할
└── REPORT.md          # `gitsim check` 실행 후 생성되는 결과 리포트
```

`remote.git` 은 실제 bare git 저장소이므로, GitHub 대신 로컬 파일 경로를 origin으로
쓴다는 점만 다를 뿐 fetch/push/clone 등 모든 동작이 진짜 git 프로토콜로 동작합니다.

## 리포트(REPORT.md) 예시 구성

`gitsim check` 를 실행하면 아래 내용을 담은 markdown 리포트가 워크스페이스에 저장됩니다.

- 결과 (성공/미완료) 및 검사 세부 내역
- 이번 시나리오의 상황 설명
- 실제 `git log --graph --oneline --all` 출력
- 실제 `git reflog` 출력 (학습자가 실행한 ref 변경 명령의 기록)
- 원격 저장소 히스토리
- 진단 결과 (잘한 점 / 놓친 점)
- 모범 답안
- 핵심 개념 정리

## 시나리오 추가하기

새 실무 상황을 추가하려면 `gitsim/scenarios/base.py` 의 `Scenario` 를 상속해
`setup`, `briefing`, `check`, `diagnose`, `model_answer`, `concepts`,
`reference_solution` 을 구현한 뒤 `gitsim/scenarios/__init__.py` 의 레지스트리에
등록하면 됩니다. `reference_solution` 은 테스트에서 "정답대로 하면 실제로
`check()` 가 성공을 인식하는지" 자동 검증하는 데 사용됩니다.

## 테스트

```bash
pip install pytest
pytest -q
```

모든 시나리오에 대해 (1) 초기 상태에서는 실패로 판정되는지, (2) `reference_solution` 을
실행하면 성공으로 판정되는지를 자동으로 검증합니다. 튜토리얼도 전체 7단계를 순서대로
수행하는 통합 테스트가 있습니다.
