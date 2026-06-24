"""Test fixtures and plugin registration."""

import sys
from pathlib import Path

import pytest

# Ensure project root is importable so root-level pytest_plugins package loads.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


pytest_plugins = [
    "pytest_plugins.log_step",
    "pytest_plugins.log_summary",
    "pytest_plugins.log_html",
]


@pytest.fixture(scope="session")
def lxshell(target):
    shell = target.get_driver("CommandProtocol")
    target.activate(shell)
    return shell
