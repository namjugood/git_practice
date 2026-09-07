"""외부 의존성 없이 터미널에 최소한의 색을 입히기 위한 헬퍼."""

import os
import sys

from gitsim.i18n import t


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("GITSIM_FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


COLOR_ENABLED = _supports_color()


def _wrap(text: str, code: str) -> str:
    if not COLOR_ENABLED:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return _wrap(text, "1")


def dim(text: str) -> str:
    return _wrap(text, "2")


def red(text: str) -> str:
    return _wrap(text, "31")


def green(text: str) -> str:
    return _wrap(text, "32")


def yellow(text: str) -> str:
    return _wrap(text, "33")


def blue(text: str) -> str:
    return _wrap(text, "34")


def cyan(text: str) -> str:
    return _wrap(text, "36")


def heading(text: str) -> str:
    line = "=" * max(len(text), 4)
    return f"\n{bold(cyan(line))}\n{bold(cyan(text))}\n{bold(cyan(line))}\n"


def sub(text: str) -> str:
    return bold(yellow(f"\n-- {text} --"))


def ok(text: str) -> str:
    return green(f"[{t('common.ok_label')}] {text}")


def fail(text: str) -> str:
    return red(f"[{t('common.fail_label')}] {text}")


def warn(text: str) -> str:
    return yellow(f"[{t('common.warn_label')}] {text}")
