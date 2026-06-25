import re
from html import escape
from pathlib import Path

import pytest

from .common import HTML_REPORT_PATH_KEY, TEST_EVENT_LOGS_KEY, TEST_RESULTS_KEY, ensure_report_state


_HTML_HEADER_LINE_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\s-+")
_STEP_DONE_RE = re.compile(r"^Step Done: (?P<cmd>.+?)\s+(PASS|FAIL)$")
_HTML_REPORT_PATH = None
_TEST_EVENT_LOGS = None
_TEST_RESULTS = None


def pytest_addoption(parser):
    parser.addoption(
        "--log-html",
        action="store",
        dest="log_html",
        default=None,
        help="write a simple HTML report with test result + step primitives",
    )


def _render_command(cmd):
    if re.match(r"^\S+\$\s", cmd):
        return cmd
    return f"$ {cmd}"


def _format_html_step_blocks(lines):
    commands = []
    current = None
    collecting = None

    for line in lines:
        if line.startswith("Test: ") or _HTML_HEADER_LINE_RE.match(line):
            continue

        if line.startswith("Step Start: "):
            if current is not None:
                commands.append(current)
            current = {"cmd": line[len("Step Start: "):], "stdout": [], "stderr": []}
            collecting = None
            continue

        done_match = _STEP_DONE_RE.match(line)
        if done_match:
            if current is None:
                current = {"cmd": done_match.group("cmd"), "stdout": [], "stderr": []}
            collecting = None
            continue

        if line == "stdout:":
            collecting = "stdout"
            continue
        if line == "stderr:":
            collecting = "stderr"
            continue

        if collecting and current is not None:
            current[collecting].append(line)

    if current is not None:
        commands.append(current)

    formatted = []
    for item in commands:
        formatted.append("------------------------------")
        formatted.append(_render_command(item["cmd"]))
        formatted.append("")
        if item["stdout"]:
            formatted.append("stdout:")
            formatted.extend(item["stdout"])
            formatted.append("")
        if item["stderr"]:
            formatted.append("stderr:")
            formatted.extend(item["stderr"])
            formatted.append("")

    while formatted and formatted[-1] == "":
        formatted.pop()
    return formatted


def _render_html_report(path, test_results):
    results = list(test_results.items())
    total = len(results)
    passed = sum(1 for _, data in results if data["status"] == "passed")
    failed = sum(1 for _, data in results if data["status"] == "failed")
    skipped = sum(1 for _, data in results if data["status"] == "skipped")

    def _display_nodeid(nodeid):
        parts = nodeid.split("::")
        if len(parts) >= 2:
            return "::".join(parts[1:])
        return nodeid

    summary_rows = []
    detail_rows = []
    for nodeid, data in results:
        status = data["status"].upper()
        row_class = {"PASSED": "", "FAILED": "alert-danger", "SKIPPED": "alert-warning"}.get(status, "")
        html_lines = _format_html_step_blocks(data["logs"])
        log_text = "\n".join(html_lines)
        anchor = (
            nodeid.replace("/", "")
            .replace(":", "")
            .replace(".", "")
            .replace("[", "")
            .replace("]", "")
            .replace(" ", "")
        )
        step_cell = escape(_display_nodeid(nodeid))
        summary_rows.append(
            f"<tr class='{row_class}'><td><a href='#{escape(anchor)}'>{step_cell}</a></td><td>{escape(status)}</td></tr>"
        )
        detail_rows.append(
            f"<tr class='{row_class}'><td id='{escape(anchor)}'>{step_cell}</td><td>{escape(status)}</td><td><pre><code class='language-bash'>{escape(log_text)}</code></pre></td></tr>"
        )

    alert_class = "alert-danger" if failed else "alert-success"
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pytest Labgrid Test Results</title>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" crossorigin="anonymous">
  <style>
    body {{ margin: 24px; }}
    pre {{ margin: 0; white-space: pre-wrap; }}
    code.language-bash {{
      display: block;
      background: #f3f5f7;
      border: 1px solid #e1e4e8;
      border-radius: 4px;
      padding: 10px 12px;
    }}
  </style>
</head>
<body>
  <h1>Test Finished</h1>
  <div class="alert {alert_class}" role="alert">
    Total Tests: {total}<br>
    Passed: {passed}<br>
    Failed: {failed}<br>
    Skipped: {skipped}
  </div>

  <h1>Summary</h1>
  <table class="table">
    <thead>
      <tr><th scope="col">Step</th><th scope="col">Status</th></tr>
    </thead>
    <tbody>
      {''.join(summary_rows)}
    </tbody>
  </table>

  <h1>Detailed Log</h1>
  <table class="table">
    <thead class="thead-dark">
      <tr><th scope="col">Step</th><th scope="col">Status</th><th scope="col">Log</th></tr>
    </thead>
    <tbody>
      {''.join(detail_rows)}
    </tbody>
  </table>
</body>
</html>
"""
    report_file = Path(path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(html, encoding="utf-8")


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    ensure_report_state(config)
    config.stash[HTML_REPORT_PATH_KEY] = config.getoption("log_html")
    global _HTML_REPORT_PATH, _TEST_EVENT_LOGS, _TEST_RESULTS
    _HTML_REPORT_PATH = config.stash[HTML_REPORT_PATH_KEY]
    _TEST_EVENT_LOGS = config.stash[TEST_EVENT_LOGS_KEY]
    _TEST_RESULTS = config.stash[TEST_RESULTS_KEY]


@pytest.hookimpl
def pytest_runtest_logreport(report):
    if report.when != "call" or not _HTML_REPORT_PATH:
        return
    _TEST_RESULTS[report.nodeid] = {
        "status": report.outcome,
        "logs": list(_TEST_EVENT_LOGS.get(report.nodeid, [])),
    }
    _render_html_report(_HTML_REPORT_PATH, _TEST_RESULTS)
