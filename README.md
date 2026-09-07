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

git도 터미널도 처음이어도 됩니다. `gitsim learn` 을 실행하면 터미널이 뭔지,
git이 뭔지부터 설명해줍니다.

```bash
gitsim learn
```

각 단계는 먼저 지금 있어야 할 작업 폴더(`cd ~/.gitsim/current`)를 다시 알려준
뒤, 두 가지 방식 중 하나로 명령을 안내합니다.

- **바로 실행 가능한 단계** (`git init`, `merge`, `pull` 등 정해진 값이 없는 단계):
  그대로 입력하면 되는 완성된 명령을 보여줍니다. 예를 들어 첫 단계는 이렇게
  나옵니다.

  ```bash
  git init -b main
  ```

- **직접 채워야 하는 단계** (이름/이메일, 커밋 메시지, 브랜치 이름 등): 일부러
  완성된 명령을 주지 않습니다. 그대로 복사하면 기억에 남지 않기 때문입니다.
  명령의 형태와 예시 문구만 보여주고, 학습자가 실제 값으로 바꿔서 직접 입력해야
  통과됩니다 — 예시 문구를 그대로 실행하면 `gitsim learn check` 가 실패하고
  다시 시도하라고 안내합니다.

명령을 다 입력했다면 `gitsim learn check` 를 따로 실행해서 통과 여부를
확인합니다 (구형 Windows PowerShell은 `&&` 로 명령을 이어붙이는 걸 지원하지
않기 때문에, 일부러 한 줄로 합치지 않았습니다).

`~/.gitsim/current` 는 지금 연습 중인 워크스페이스를 가리키는 고정 경로입니다.
Windows에서 관리자 권한 없이 이 바로가기를 만들 수 없는 경우, gitsim은 자동으로
디렉터리 접합점(junction)으로 다시 시도합니다. 그래도 안 되면 각 단계 안내에
함께 표시되는 실제 경로(예: `C:\Users\...\workspaces\tutorial-...\repo`)로
직접 이동하면 됩니다.

`init` → 커밋 작성자 정보 설정(`git config`) → 첫 커밋 → 브랜치 생성/이동 →
브랜치에서 커밋 → main으로 merge → 원격(origin) 연결 및 push → 동료가 올린
변경사항 pull 받기, 총 8단계로 구성되어 있습니다. `gitsim learn reset` 으로
언제든 처음부터 다시 시작하거나, `gitsim learn intro` 로 처음 설명을 다시 볼
수 있습니다.

### 2) 실무 시나리오 훈련

```bash
gitsim list                       # 연습 가능한 시나리오 목록
gitsim start merge-conflict       # 워크스페이스 생성 + 상황(임무) 브리핑 출력
cd ~/.gitsim/current              # 항상 이 고정 경로로 이동하면 됩니다
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
디렉터리를 만듭니다 (`--base-dir` 로 변경 가능). 매번 만들어질 때마다
`~/.gitsim/current` 심볼릭 링크가 그 워크스페이스의 `repo/` 를 가리키도록 갱신되므로,
실제로는 항상 `cd ~/.gitsim/current` 한 줄만 기억하면 됩니다.

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
