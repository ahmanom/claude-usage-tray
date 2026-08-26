"""Regression test for a real bug: unparented QAction objects passed to
QMenu.addAction() are garbage collected in PySide6, leaving the tray's
right-click menu empty. build_tray_menu() must create menu-owned actions."""

import gc
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from claude_usage_tray.tray_app import build_tray_menu


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_menu_actions_survive_garbage_collection(qapp):
    calls = []
    menu = build_tray_menu(
        on_open=lambda: calls.append("open"),
        on_refresh=lambda: calls.append("refresh"),
        on_close=lambda: calls.append("close"),
    )

    gc.collect()

    texts = [action.text() for action in menu.actions()]
    assert texts == ["Open", "Refresh now", "", "Close"]


def test_menu_actions_invoke_callbacks(qapp):
    calls = []
    menu = build_tray_menu(
        on_open=lambda: calls.append("open"),
        on_refresh=lambda: calls.append("refresh"),
        on_close=lambda: calls.append("close"),
    )
    gc.collect()

    actions = {action.text(): action for action in menu.actions() if action.text()}
    actions["Open"].trigger()
    actions["Close"].trigger()

    assert calls == ["open", "close"]
