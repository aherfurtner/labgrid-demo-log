import pytest


SUMMARY_LOG_PATH_KEY = pytest.StashKey[object]()
HTML_REPORT_PATH_KEY = pytest.StashKey[object]()
TEST_EVENT_LOGS_KEY = pytest.StashKey[dict]()
TEST_RESULTS_KEY = pytest.StashKey[dict]()


def ensure_report_state(config):
    if TEST_EVENT_LOGS_KEY not in config.stash:
        config.stash[TEST_EVENT_LOGS_KEY] = {}
    if TEST_RESULTS_KEY not in config.stash:
        config.stash[TEST_RESULTS_KEY] = {}
