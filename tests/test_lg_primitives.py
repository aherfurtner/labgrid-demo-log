"""Coverage for the labgrid ``CommandProtocol`` primitives used in this suite.

Expected API shape (as exercised here):
- run(cmd: str, timeout: float = 30.0, ...) -> tuple[list[str], list[str], int]
  Returns ``(stdout, stderr, returncode)`` and does not raise on non-zero exit.

- run_check(cmd: str, timeout: float = 30.0, ...) -> list[str]
  Returns ``stdout`` for successful commands, raises ``ExecutionError`` otherwise.

- wait_for(cmd: str, pattern: str, timeout: float = 30.0, sleepduration: float = 1)
  Re-runs ``cmd`` until ``pattern`` is found; returns ``None`` on success and
  raises ``ExecutionError("Wait timeout expired")`` on timeout.

- poll_until_success(cmd: str, tries: int | None = None, timeout: float = 30.0,
  sleepduration: float = 1) -> bool
  Returns ``True`` once the command succeeds, ``False`` if it does not.

- get_status() -> int
  Returns the driver's active status indicator.
"""

import pytest
from labgrid.driver.exception import ExecutionError

def test_run_success_returns_stdout_stderr_and_returncode(lxshell):
    # Standard run API: returns (stdout, stderr, returncode) without raising.
    stdout, stderr, returncode = lxshell.run('echo "hello"')
    assert stdout == ["hello"]
    assert stderr == []
    assert returncode == 0

def test_run_check_success_returns_stdout(lxshell):
    # Happy-path: run_check returns parsed stdout for a successful command.
    stdout = lxshell.run_check('echo "hello"')
    assert stdout == ["hello"]


def test_run_check_raises_on_nonzero_exit_expected(lxshell):
    # Expected-failure variant: non-zero exit is mapped to ExecutionError.
    with pytest.raises(ExecutionError):
        lxshell.run_check("false")


def test_run_check_raises_on_nonzero_exit(lxshell):
    # Demonstration variant: same command without pytest.raises should fail.
    lxshell.run_check("false")


def test_wait_for_succeeds_when_pattern_is_present(lxshell):
    # wait_for should return normally when the requested pattern appears.
    lxshell.wait_for('echo "ready"', "ready", timeout=1.0, sleepduration=0.01)


def test_wait_for_raises_when_pattern_never_appears_expected(lxshell):
    # Expected-timeout variant: missing pattern must raise timeout error.
    with pytest.raises(ExecutionError, match="Wait timeout expired"):
        lxshell.wait_for("uname", "definitely-not-present", timeout=0.05, sleepduration=0.01)


def test_wait_for_raises_when_pattern_never_appears(lxshell):
    # Demonstration variant: without pytest.raises, timeout surfaces as failure.
    lxshell.wait_for("uname", "definitely-not-present", timeout=0.1, sleepduration=0.01)


def test_poll_until_success_true_command(lxshell):
    # poll_until_success reports True when a command succeeds in time.
    assert lxshell.poll_until_success("true", timeout=1.0, sleepduration=0.01) is True


def test_poll_until_success_false_command(lxshell):
    # poll_until_success reports False after repeated non-zero exits.
    assert lxshell.poll_until_success("false", tries=2, timeout=0.2, sleepduration=0.01) is False


def test_get_status_reports_active(lxshell):
    # Fake shell driver stays active once fixture activation is complete.
    assert lxshell.get_status() == 1
