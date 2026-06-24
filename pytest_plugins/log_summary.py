from pathlib import Path

import pytest

from .common import SUMMARY_LOG_PATH_KEY

_SUMMARY_LOG_PATH = None


def _append_summary_line(path, nodeid, outcome):
    logfile = Path(path)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open("a", encoding="utf-8") as fh:
        fh.write(f"Test {outcome.capitalize()}: {nodeid}\n")


def pytest_addoption(parser):
    parser.addoption(
        "--log-summary",
        action="store",
        dest="log_summary",
        default=None,
        help="append one test result line per executed test to this file",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    config.stash[SUMMARY_LOG_PATH_KEY] = config.getoption("log_summary")
    global _SUMMARY_LOG_PATH
    _SUMMARY_LOG_PATH = config.stash[SUMMARY_LOG_PATH_KEY]


@pytest.hookimpl
def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    if not _SUMMARY_LOG_PATH:
        return
    _append_summary_line(_SUMMARY_LOG_PATH, report.nodeid, report.outcome)
