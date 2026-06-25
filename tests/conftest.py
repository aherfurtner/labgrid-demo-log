"""Test fixtures and plugin registration."""

import sys
from pathlib import Path

import pytest
from labgrid.exceptions import NoDriverFoundError

# Ensure project root is importable so root-level pytest_plugins package loads.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


pytest_plugins = [
    "pytest_plugins.log_step",
    "pytest_plugins.log_summary",
    "pytest_plugins.log_html",
    "pytest_plugins.log_archive",
]


@pytest.fixture(scope="session")
def lxshell(target):
    try:
        shell = target.get_driver("FakeShellDriver")
    except NoDriverFoundError:
        shell = target.get_driver("ShellDriver")
    target.activate(shell)
    return shell


@pytest.fixture(scope="session")
def hostshell(target):
    shell = target.get_driver("LocalShellDriver")
    target.activate(shell)
    return shell
