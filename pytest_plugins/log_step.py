import logging
import platform
import sys
import time

import pytest
from labgrid.logging import StepLogger

from .common import TEST_EVENT_LOGS_KEY, ensure_report_state


_COMMAND_STEP_TITLES = {"run", "run_check"}
_TEST_STATE = {
    "nodeid": None,
    "machine": platform.node(),
    "header_emitted": False,
    "step_emitted": False,
    "last_was_done": False,
}


def reset_test_state(nodeid=None):
    _TEST_STATE["nodeid"] = nodeid
    _TEST_STATE["header_emitted"] = False
    _TEST_STATE["step_emitted"] = False
    _TEST_STATE["last_was_done"] = False


class RunSummaryFilter(logging.Filter):
    """Rewrite command-related StepLogger records for CLI/log-file output."""

    def __init__(self, test_event_logs):
        super().__init__()
        self._test_event_logs = test_event_logs

    @staticmethod
    def _format_stream(value):
        if not value:
            return ""
        if isinstance(value, list):
            return "\n".join(str(v) for v in value)
        return str(value)

    @staticmethod
    def _format_header(nodeid):
        if not nodeid:
            return "Test: -"
        machine = _TEST_STATE.get("machine") or "-"
        return f"Test: {machine} ({nodeid})"

    @staticmethod
    def _format_time(record):
        return time.strftime("%H:%M:%S", time.localtime(record.created))

    def _format_result(self, step):
        result = getattr(step, "result", None)
        if step.title == "run_check":
            stdout = self._format_stream(result)
            return f"PASS\nstdout:\n{stdout}" if stdout else "PASS"

        stdout = ""
        stderr = ""
        rc = "?"
        if isinstance(result, tuple) and len(result) == 3:
            stdout = self._format_stream(result[0])
            stderr = self._format_stream(result[1])
            rc = result[2]

        status = "PASS" if rc == 0 else "FAIL"
        parts = [status]
        if stdout:
            parts.append(f"stdout:\n{stdout}")
        if stderr:
            parts.append(f"stderr:\n{stderr}")
        return "\n".join(parts)

    def filter(self, record):
        step = getattr(record, "step", None)
        if step is None or getattr(step, "title", None) not in _COMMAND_STEP_TITLES:
            return False

        state = _TEST_STATE
        nodeid = state.get("nodeid") or "-"
        is_done = getattr(step, "status", None) == "done"
        cmd = str((getattr(step, "args", None) or {}).get("cmd", ""))

        lines = []
        if state.get("step_emitted") and not is_done and state.get("last_was_done"):
            lines.append("")
        if not state.get("header_emitted"):
            lines.append(self._format_header(nodeid))
            lines.append(f"{self._format_time(record)} -------------------------------------------------------")
            state["header_emitted"] = True

        if is_done:
            lines.append(f"Step Done: {cmd} {self._format_result(step)}")
        else:
            lines.append(f"Step Start: {cmd}")

        record.levelname = ""
        record.name = ""
        record.msg = "\n".join(lines)
        record.args = ()

        node_logs = self._test_event_logs.setdefault(nodeid, [])
        for line in record.msg.splitlines():
            if line.strip():
                node_logs.append(line)

        state["step_emitted"] = True
        state["last_was_done"] = is_done
        return True


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    ensure_report_state(config)
    StepLogger._length_limit = sys.maxsize
    event_logs = config.stash[TEST_EVENT_LOGS_KEY]
    logging.getLogger("StepLogger").addFilter(RunSummaryFilter(event_logs))

    logging_plugin = config.pluginmanager.getplugin("logging-plugin")
    if logging_plugin:
        plain = logging.Formatter("%(message)s")
        logging_plugin.log_cli_handler.setFormatter(plain)
        logging_plugin.log_file_handler.setFormatter(plain)
        logging_plugin.report_handler.setFormatter(plain)


@pytest.hookimpl
def pytest_runtest_setup(item):
    reset_test_state(item.nodeid)


@pytest.hookimpl
def pytest_runtest_teardown(item):
    reset_test_state()
