"""아주 단순한 메시지 카탈로그 로더 (다국어 지원 준비용).

화면에 보여주는 모든 문구는 코드에 직접 박혀 있지 않고 `gitsim/messages/<locale>/`
아래 파이썬 모듈들이 정의하는 `MESSAGES: dict[str, str]` 에서 가져온다. 새 언어를
추가하려면 `gitsim/messages/<locale>/` 폴더를 하나 만들고 같은 키 구조로 문구를
채우기만 하면 되고, 코드(gitsim/*.py)는 건드릴 필요가 없다.

로케일은 `GITSIM_LOCALE` 환경 변수로 고른다 (기본값 "ko"). 어떤 키가 그 로케일에
없으면 기본 로케일(ko)로 자동 대체하고, 그마저 없으면 키 이름 자체를 반환해서
최소한 화면에 아무것도 안 뜨는 사고는 나지 않게 한다.
"""

from __future__ import annotations

import importlib
import os
from typing import Any

DEFAULT_LOCALE = "ko"

_cache: dict[str, dict[str, str]] = {}


def _load(locale: str) -> dict[str, str]:
    if locale not in _cache:
        module = importlib.import_module(f"gitsim.messages.{locale}")
        _cache[locale] = module.MESSAGES
    return _cache[locale]


def current_locale() -> str:
    return os.environ.get("GITSIM_LOCALE", DEFAULT_LOCALE)


def t(key: str, **kwargs: Any) -> str:
    """`key` 에 해당하는 문구를 찾아 `kwargs` 로 채워서 돌려준다."""
    locale = current_locale()
    try:
        messages = _load(locale)
    except ModuleNotFoundError:
        messages = {}

    template = messages.get(key)
    if template is None and locale != DEFAULT_LOCALE:
        template = _load(DEFAULT_LOCALE).get(key)
    if template is None:
        template = key

    return template.format(**kwargs) if kwargs else template
