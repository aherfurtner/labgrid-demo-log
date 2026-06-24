#!/bin/sh

rm -rf ./logs >/dev/null 2>&1

# -q: quiet mode (less pytest output noise)
# -vv: very verbose test reporting (full test names and details)
# --lg-env env.yaml: load the labgrid environment/target config from env.yaml
# --log-file: Log file including CLI output
# --lg-log: Directory for labgrid console capture files (one file per console source)
# --log-summary: per-test summary file ("Test Passed/Failed/Skipped: <nodeid>")
# --log-html: HTML report including test status + step primitives
pytest -vv --lg-env env.yaml --log-file=./logs/test.verbose --lg-log=./logs/console/ --log-summary=./logs/test.summary --log-html=./logs/test.html
