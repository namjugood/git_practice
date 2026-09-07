"""연습 워크스페이스(작업 디렉터리) 생성/조회/초기화를 관리한다.

워크스페이스 구조:
    <workspace-root>/
        .gitsim.json     메타데이터 (시나리오 id, 시작 시각, 저장된 커밋 해시 등)
        repo/            학습자가 실제로 git 명령을 실행할 로컬 저장소
        remote.git/      "원격 저장소" 역할을 하는 로컬 bare 저장소 (origin)
        teammate_clone/  일부 시나리오에서 "동료의 로컬 클론" 역할
        REPORT.md        `gitsim check` 실행 후 생성되는 결과 리포트
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

DEFAULT_ROOT = Path.home() / ".gitsim" / "workspaces"
LAST_POINTER = Path.home() / ".gitsim" / "last_workspace"


@dataclass
class Workspace:
    path: Path
    scenario_id: str
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def repo_dir(self) -> Path:
        return self.path / "repo"

    @property
    def remote_dir(self) -> Path:
        return self.path / "remote.git"

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
        raise FileNotFoundError(f"{path} 는 gitsim 워크스페이스가 아닙니다 (.gitsim.json 없음)")
    data = json.loads(meta_file.read_text(encoding="utf-8"))
    scenario_id = data.pop("scenario_id")
    return Workspace(path=path, scenario_id=scenario_id, meta=data)


def _remember_last(path: Path) -> None:
    LAST_POINTER.parent.mkdir(parents=True, exist_ok=True)
    LAST_POINTER.write_text(str(path), encoding="utf-8")


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

    raise FileNotFoundError(
        "현재 위치에서 gitsim 워크스페이스를 찾을 수 없습니다. "
        "연습 중이던 repo 디렉터리 안에서 실행하거나 --dir 옵션으로 경로를 지정하세요."
    )


def list_workspaces(base_dir: Optional[Path] = None) -> list[Workspace]:
    root = base_dir or DEFAULT_ROOT
    if not root.exists():
        return []
    out = []
    for child in sorted(root.iterdir()):
        if (child / ".gitsim.json").exists():
            out.append(load_workspace(child))
    return out
