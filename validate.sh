#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

a=$(mktemp -d)
b=$(mktemp -d)

pipeline() {
    local out="$1"
    python3 linter.py inspect fixture --out "$out/inspection.json"
    python3 linter.py plan fixture --out "$out/plan.json"
    python3 linter.py run fixture --out "$out/diagnostics.json" --log "$out/acquisition.log"
}

pipeline "$a"
pipeline "$b"

failures=0
for artifact in inspection.json plan.json acquisition.log diagnostics.json; do
    if diff -q "$a/$artifact" "$b/$artifact" >/dev/null 2>&1; then
        echo "PASS $artifact: byte-equivalent"
    else
        failures=$((failures + 1))
        echo "FAIL $artifact: runs differ"
        diff "$a/$artifact" "$b/$artifact" | head -n 20
    fi
done

rm -rf "$a" "$b"
[ "$failures" -eq 0 ]
