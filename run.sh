#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 linter.py inspect fixture --out inspection.json
python3 linter.py plan fixture --out plan.json
python3 linter.py run fixture --out diagnostics.json --log acquisition.log
