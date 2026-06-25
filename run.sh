#!/bin/sh

LG_ENV_FILE="env.yaml"
LOG_PREFIX="./logs/env"
if [ "${1:-}" = "--fake" ]; then
  LG_ENV_FILE="env-fake.yaml"
  LOG_PREFIX="./logs/env-fake"
  shift
fi

rm -rf "${LOG_PREFIX}" >/dev/null 2>&1

# -q: quiet mode (less pytest output noise)
# -vv: very verbose test reporting (full test names and details)
# --fake: optional switch to use env-fake.yaml instead of env.yaml
# --lg-env: load the selected labgrid environment/target config
# --log-file: Log file including CLI output
# --lg-log: Directory for labgrid console capture files (one file per console source)
# --log-summary: per-test summary file ("Test Passed/Failed/Skipped: <nodeid>")
# --log-html: HTML report including test status + step primitives
# --log-archive-prefix: creates both <prefix>.zip and <prefix>.tar.zst after pytest finishes
pytest -vv --lg-env "${LG_ENV_FILE}" \
    --lg-log="${LOG_PREFIX}/console/" \
    --log-html="${LOG_PREFIX}/test.html" \
    --log-file="${LOG_PREFIX}/test.verbose" \
    --log-summary="${LOG_PREFIX}/test.summary" \
    --log-archive-prefix="${LOG_PREFIX}/test-logs" \
    "$@"
