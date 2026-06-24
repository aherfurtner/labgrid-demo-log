from pathlib import Path


def add_pytest_options(parser):
    parser.addoption(
        "--log-summary",
        action="store",
        dest="log_summary",
        default=None,
        help="append one test result line per executed test to this file",
    )


def append_summary_line(path, nodeid, outcome):
    logfile = Path(path)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open("a", encoding="utf-8") as fh:
        fh.write(f"Test {outcome.capitalize()}: {nodeid}\n")
