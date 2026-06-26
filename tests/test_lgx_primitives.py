import pytest
from labgrid.driver.exception import ExecutionError


def test_run_expect_success_returns_stdout(lxshell):
    stdout = lxshell.run_expect('echo "needle"', "needle")
    assert stdout == ["needle"]


def test_run_expect_raises_when_pattern_missing(lxshell):
    with pytest.raises(ExecutionError, match="Pattern not found in output"):
        lxshell.run_expect('echo "hello"', "needle")
