"""연습 워크스페이스(작업 디렉터리) 생성/조회/초기화를 관리한다.

워크스페이스 구조:
    <workspace-root>/
        .gitsim.json     메타데이터 (시나리오 id, 시작 시각, 저장된 커밋 해시 등)
        repo/            학습자가 실제로 git 명령을 실행할 로컬 저장소
        teammate_clone/  일부 시나리오에서 "동료의 로컬 클론" 역할
        REPORT.md        `gitsim check` 실행 후 생성되는 결과 리포트

`origin` 은 이제 로컬 bare 저장소가 아니라 학습자가 `gitsim remote set <주소>` 로
등록한 실제 원격 저장소(예: GitHub)다. 워크스페이스마다 `practice_branch_name()`
이 만들어주는 고유한 브랜치에서만 작업하므로, 여러 시나리오/여러 번의 재시도가
같은 원격 저장소를 공유해도 서로의 기록을 덮어쓰지 않는다.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from gitsim.i18n import t as _

DEFAULT_ROOT = Path.home() / ".gitsim" / "workspaces"
LAST_POINTER = Path.home() / ".gitsim" / "last_workspace"
CURRENT_LINK = Path.home() / ".gitsim" / "current"
CONFIG_FILE = Path.home() / ".gitsim" / "config.json"


@dataclass
class Workspace:
    path: Path
    scenario_id: str
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def repo_dir(self) -> Path:
        return self.path / "repo"

    @property
    def teammate_dir(self) -> Path:
        return self.path / "teammate_clone"

    @property
    def meta_file(self) -> Path:
        return self.path / ".gitsim.json"

    @property
    def report_file(self) -> Path:
        return self.path / "REPORT.md"

    def save_meta(self, **updates: Any) -> None:
        self.meta.update(updates)
        payload = {"scenario_id": self.scenario_id, **self.meta}
        self.meta_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self.meta.get(key, default)


def _slugify_timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def create_workspace(scenario_id: str, base_dir: Optional[Path] = None) -> Workspace:
    root = base_dir or DEFAULT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    ws_path = root / f"{scenario_id}-{_slugify_timestamp()}"
    ws_path.mkdir(parents=True, exist_ok=False)
    ws = Workspace(path=ws_path, scenario_id=scenario_id, meta={})
    ws.save_meta(created_at=time.time())
    _remember_last(ws_path)
    return ws


def load_workspace(path: Path) -> Workspace:
    meta_file = path / ".gitsim.json"
    if not meta_file.exists():
        raise FileNotFoundError(_("common.workspace_invalid", path=path))
    data = json.loads(meta_file.read_text(encoding="utf-8"))
    scenario_id = data.pop("scenario_id")
    return Workspace(path=path, scenario_id=scenario_id, meta=data)


def _remember_last(path: Path) -> None:
    LAST_POINTER.parent.mkdir(parents=True, exist_ok=True)
    LAST_POINTER.write_text(str(path), encoding="utf-8")


def _load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config(data: dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_remote_url() -> Optional[str]:
    """학습자가 등록한 실제 원격 저장소(예: GitHub) 주소를 돌려준다.

    `GITSIM_REMOTE_URL` 환경 변수가 있으면 그것을 우선한다 — 자동화 테스트에서
    로컬 bare 저장소를 "가짜 원격"으로 꽂아 넣을 때, 또는 특정 실행에서만 다른
    원격을 잠깐 쓰고 싶을 때 설정 파일을 건드리지 않고 오버라이드할 수 있다.
    """
    env_override = os.environ.get("GITSIM_REMOTE_URL")
    if env_override:
        return env_override
    return _load_config().get("remote_url")


def set_remote_url(url: str) -> None:
    data = _load_config()
    data["remote_url"] = url
    _save_config(data)


def require_remote_url() -> str:
    url = get_remote_url()
    if not url:
        raise RuntimeError(_("common.remote_not_registered"))
    return url


def practice_branch_name(ws: "Workspace") -> str:
    """이 워크스페이스(=이번 한 번의 시도) 전용 원격 브랜치 이름.

    워크스페이스 폴더 이름 자체가 이미 `<시나리오id>-<타임스탬프>` 형태로 유일하므로,
    재시도할 때마다 항상 새 브랜치가 생긴다. gitsim은 이 브랜치를 절대 강제로
    덮어쓰거나 지우지 않는다 — 실수를 포함한 학습 이력을 전부 남기기 위해서다.
    """
    return f"practice/{ws.path.name}"


def _clear_current_link() -> None:
    if CURRENT_LINK.is_symlink():
        CURRENT_LINK.unlink()
    elif CURRENT_LINK.exists():
        # Windows 디렉터리 접합점(junction)은 심볼릭 링크로 보고되지 않고, 일반 unlink()로
        # 지울 수 없다 — 빈 디렉터리를 지우는 rmdir()로 접합점 자체만 제거해야 한다
        # (대상 폴더 내용은 건드리지 않는다).
        try:
            CURRENT_LINK.rmdir()
        except OSError:
            pass


def point_current(ws: "Workspace") -> Optional[Path]:
    """`~/.gitsim/current` 가 항상 지금 연습 중인 repo/ 를 가리키도록 갱신한다.

    매번 타임스탬프가 붙은 워크스페이스 경로를 찾아 들어갈 필요 없이,
    학습자가 항상 같은 경로(`cd ~/.gitsim/current`)로 이동할 수 있게 해준다.

    일반 심볼릭 링크는 관리자 권한/개발자 모드 없이는 Windows에서 만들 수 없는 경우가
    많다. 그런 경우 관리자 권한이 필요 없는 NTFS 디렉터리 접합점(junction, `mklink /J`)
    으로 대신 시도한다. 둘 다 실패하면 None을 반환하니, 호출 쪽에서 실제 경로를 함께
    안내해야 한다.
    """
    try:
        CURRENT_LINK.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None

    _clear_current_link()

    try:
        CURRENT_LINK.symlink_to(ws.repo_dir, target_is_directory=True)
        return CURRENT_LINK
    except OSError:
        pass

    if os.name == "nt":
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(CURRENT_LINK), str(ws.repo_dir)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return CURRENT_LINK

    return None


def find_enclosing_workspace(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".gitsim.json").exists():
            return candidate
    return None


def resolve_workspace(explicit_dir: Optional[str], cwd: Path) -> Workspace:
    if explicit_dir:
        path = Path(explicit_dir).resolve()
        return load_workspace(path)

    enclosing = find_enclosing_workspace(cwd)
    if enclosing:
        ws = load_workspace(enclosing)
        _remember_last(enclosing)
        return ws

    if LAST_POINTER.exists():
        path = Path(LAST_POINTER.read_text(encoding="utf-8").strip())
        if (path / ".gitsim.json").exists():
            return load_workspace(path)

    raise FileNotFoundError(_("common.workspace_not_found"))


def list_workspaces(base_dir: Optional[Path] = None) -> list[Workspace]:
    root = base_dir or DEFAULT_ROOT
    if not root.exists():
        return []
    out = []
    for child in sorted(root.iterdir()):
        if (child / ".gitsim.json").exists():
            out.append(load_workspace(child))
    return out
