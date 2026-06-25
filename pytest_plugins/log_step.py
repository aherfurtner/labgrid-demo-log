import logging
import platform
import re
import sys
import time
from pathlib import Path

import pytest
from labgrid.logging import StepLogger

from .common import TEST_EVENT_LOGS_KEY, ensure_report_state


_COMMAND_STEP_TITLES = {"run", "run_check"}
_STEP_START_RE = re.compile(r"^Step Start: (?P<origin>[a-z0-9_-]+)\$\s")
_HEADER_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\s-+")
_TEST_STATE = {
    "nodeid": None,
    "machine": platform.node(),
    "header_emitted": False,
    "step_emitted": False,
    "last_was_done": False,
}
_STEPLOG_BASE_DIR = None
_TEST_EVENT_LOGS = None


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

    @staticmethod
    def _format_command(step):
        cmd = str((getattr(step, "args", None) or {}).get("cmd", ""))
        source = getattr(step, "source", None)
        source_name = source.__class__.__name__ if source is not None else ""
        if source_name == "LocalShellDriver":
            host = "local"
        elif source_name in {"ShellDriver", "FakeShellDriver"}:
            host = "dut"
        else:
            host = "cmd"
        return f"{host}$ {cmd}" if cmd else f"{host}$"

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
        cmd = self._format_command(step)

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


def _resolve_steplog_base_dir(config):
    lg_log = config.getoption("lg_log", default=None)
    if lg_log:
        return Path(lg_log).parent

    for option in ("log_file", "log_html", "log_summary"):
        value = config.getoption(option, default=None)
        if value:
            return Path(value).parent
    return None


def _nodeid_to_paths(nodeid):
    file_part, _, test_part = nodeid.partition("::")
    file_stem = Path(file_part).stem or "unknown"
    test_name = test_part or "unknown"
    safe_test_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", test_name)
    return file_stem, safe_test_name


def _collect_origin_step_blocks(lines):
    blocks = {"dut": [], "local": []}
    header = [line for line in lines if line.startswith("Test: ") or _HEADER_TIME_RE.match(line)]
    current_origin = None
    current_block = []

    def flush():
        nonlocal current_block, current_origin
        if current_origin in blocks and current_block:
            blocks[current_origin].extend(current_block)
            blocks[current_origin].append("")
        current_block = []

    for line in lines:
        match = _STEP_START_RE.match(line)
        if match:
            flush()
            current_origin = match.group("origin")
            current_block = [line]
            continue

        if current_origin is not None:
            current_block.append(line)

    flush()

    for origin, content in blocks.items():
        while content and content[-1] == "":
            content.pop()
        if content and header:
            blocks[origin] = header + [""] + content
    return blocks


def _write_per_test_steplogs(base_dir, nodeid, lines):
    file_stem, test_name = _nodeid_to_paths(nodeid)
    origin_blocks = _collect_origin_step_blocks(lines)
    test_dir = base_dir / file_stem
    test_dir.mkdir(parents=True, exist_ok=True)

    for origin in ("dut", "local"):
        path = test_dir / f"{test_name}.{origin}"
        path.unlink(missing_ok=True)
        content = origin_blocks[origin]
        if content:
            path.write_text("\n".join(content) + "\n", encoding="utf-8")


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    ensure_report_state(config)
    StepLogger._length_limit = sys.maxsize
    event_logs = config.stash[TEST_EVENT_LOGS_KEY]
    logging.getLogger("StepLogger").addFilter(RunSummaryFilter(event_logs))
    global _STEPLOG_BASE_DIR, _TEST_EVENT_LOGS
    _STEPLOG_BASE_DIR = _resolve_steplog_base_dir(config)
    _TEST_EVENT_LOGS = event_logs

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


@pytest.hookimpl
def pytest_runtest_logreport(report):
    if report.when != "call" or _STEPLOG_BASE_DIR is None:
        return
    logs = (_TEST_EVENT_LOGS or {}).get(report.nodeid, [])
    _write_per_test_steplogs(_STEPLOG_BASE_DIR, report.nodeid, logs)
