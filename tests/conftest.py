"""
Pytest hook wiring for three outputs:
1. CLI / pytest log-file formatting (StepLogger -> Step Start/Done blocks)
2. Plain summary file (--log-summary)
3. HTML report (--log-html)
"""

import logging
import sys

import pytest
from labgrid.logging import StepLogger

import log_html
import log_step
import log_summary


_SUMMARY_LOG_PATH = None
_HTML_REPORT_PATH = None
_TEST_EVENT_LOGS = {}
_TEST_RESULTS = {}


def pytest_addoption(parser):
    log_summary.add_pytest_options(parser)
    log_html.add_pytest_options(parser)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    StepLogger._length_limit = sys.maxsize
    logging.getLogger("StepLogger").addFilter(log_step.RunSummaryFilter(_TEST_EVENT_LOGS))

    logging_plugin = config.pluginmanager.getplugin("logging-plugin")
    if logging_plugin:
        plain = logging.Formatter("%(message)s")
        logging_plugin.log_cli_handler.setFormatter(plain)
        logging_plugin.log_file_handler.setFormatter(plain)
        logging_plugin.report_handler.setFormatter(plain)

    global _SUMMARY_LOG_PATH
    _SUMMARY_LOG_PATH = config.getoption("log_summary")

    global _HTML_REPORT_PATH
    _HTML_REPORT_PATH = config.getoption("log_html")


@pytest.hookimpl
def pytest_runtest_setup(item):
    log_step.reset_test_state(item.nodeid)


@pytest.hookimpl
def pytest_runtest_teardown(item):
    log_step.reset_test_state()


@pytest.hookimpl
def pytest_runtest_logreport(report):
    # We use only "call" phase so each test contributes exactly one result row.
    if report.when != "call":
        return

    if _SUMMARY_LOG_PATH:
        log_summary.append_summary_line(_SUMMARY_LOG_PATH, report.nodeid, report.outcome)

    if _HTML_REPORT_PATH:
        log_html.update_html_report(
            _HTML_REPORT_PATH,
            report.nodeid,
            report.outcome,
            _TEST_EVENT_LOGS,
            _TEST_RESULTS,
        )


@pytest.fixture(scope="session")
def lxshell(target):
    shell = target.get_driver("CommandProtocol")
    target.activate(shell)
    return shell
