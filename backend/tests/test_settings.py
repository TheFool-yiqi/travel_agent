"""Settings parsing regressions."""

from __future__ import annotations

from app.settings import Settings


def test_debug_accepts_release_as_false() -> None:
    cfg = Settings(_env_file=None, DEBUG="release")
    assert cfg.debug is False


def test_debug_accepts_development_as_true() -> None:
    cfg = Settings(_env_file=None, DEBUG="development")
    assert cfg.debug is True


def test_default_app_port_matches_frontend_proxy() -> None:
    cfg = Settings(_env_file=None)
    assert cfg.app_port == 8200


def test_default_chat_planner_backend_is_runtime() -> None:
    cfg = Settings(_env_file=None)
    assert cfg.chat_planner_backend == "runtime"
