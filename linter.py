#!/usr/bin/env python3
"""Framework entrypoint."""

import argparse
import json
import os
import sys

from analyzer import Analyzer
from executor import Executor
from planner import Context, Planner


def main(argv=None):
    parser = argparse.ArgumentParser(prog="linter")
    parser.add_argument("command", choices=["inspect", "plan", "run"])
    parser.add_argument("root", help="repository root")
    parser.add_argument("--out", help="write artifact to this file instead of stdout")
    parser.add_argument("--log", help="write acquisition log to this file (run only)")
    args = parser.parse_args(argv)

    inspection = Analyzer().analyze(args.root)
    if args.command == "inspect":
        artifact = inspection.to_json()
    elif args.command == "plan":
        artifact = Planner().plan(inspection, Context(root=args.root))
    else:
        plan = json.loads(Planner().plan(inspection, Context(root=args.root)))
        log_path = args.log or "acquisition.log"
        artifact = Executor().execute(plan, os.path.abspath(args.root), log_path)

    if args.out:
        with open(args.out, "w") as f:
            f.write(artifact)
    else:
        sys.stdout.write(artifact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
