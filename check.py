"""Focused checks for the single-pass inspection, deterministic plan, and executor.

Proves one analyzer traversal, an immutable inspection, byte-equivalent
reruns, filesystem isolation during plugin evaluation, expected plan output,
and that only the planned tools are acquired and executed.
"""

import builtins
import json
import os
import subprocess
import sys
import tempfile

from analyzer import Analyzer
from inspection import Inspection
from plugin import PLUGINS
from planner import Context, Planner
from wrapper import WRAPPERS

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixture")
LINTER = os.path.join(HERE, "linter.py")


def one_traversal():
    calls = []

    def counted_walk(root):
        calls.append(root)
        yield from os.walk(root)

    analyzer = Analyzer(walk=counted_walk)
    analyzer.analyze(FIXTURE)
    assert len(calls) == 1, f"expected one traversal, saw {len(calls)}"
    assert analyzer.traversals == 1, f"expected one analyze, saw {analyzer.traversals}"


def immutable_inspection():
    inspection = Analyzer().analyze(FIXTURE)
    attempts = [
        ("feature mutation", lambda: inspection.features.__setitem__("has-python", False)),
        ("config insertion", lambda: inspection.configs.__setitem__("extra", {})),
        (
            "config entry mutation",
            lambda: inspection.configs["ruff"].__setitem__("path", "x"),
        ),
        ("attribute reassignment", lambda: setattr(inspection, "features", {})),
    ]
    for label, attempt in attempts:
        try:
            attempt()
        except (AttributeError, TypeError):
            continue
        raise AssertionError(f"mutable path exposed: {label}")


def stable_artifact():
    with tempfile.TemporaryDirectory() as tmp:
        runs = []
        for name in ("first.json", "second.json"):
            out = os.path.join(tmp, name)
            subprocess.run(
                [sys.executable, LINTER, "inspect", FIXTURE, "--out", out], check=True
            )
            with open(out, "rb") as f:
                runs.append(f.read())
    assert runs[0] == runs[1], "unchanged runs produced different artifacts"
    payload = json.loads(runs[0])
    assert payload["features"] == {
        "has-dockerfile": False,
        "has-markdown": True,
        "has-python": True,
    }
    assert payload["configs"]["ruff"] == {"exists": True, "path": ".linter/ruff.toml"}
    assert payload["configs"]["markdownlint"] == {
        "exists": True,
        "path": ".linter/markdownlint.json",
    }
    assert payload["configs"]["hadolint"] == {
        "exists": False,
        "path": ".linter/hadolint.yaml",
    }


def no_filesystem_access():
    inspection = Inspection(
        features={"has-python": True, "has-markdown": True, "has-dockerfile": False},
        configs={
            "ruff": {"path": ".linter/ruff.toml", "exists": True},
            "markdownlint": {"path": ".linter/markdownlint.json", "exists": True},
            "hadolint": {"path": ".linter/hadolint.yaml", "exists": False},
        },
    )
    context = Context(root="/fake")
    accesses = []

    real_open = builtins.open
    real_stat = os.stat

    def blocked_open(*args, **kwargs):
        accesses.append(("open", args[0] if args else "?"))
        raise OSError("filesystem blocked during plugin evaluation")

    def blocked_stat(*args, **kwargs):
        accesses.append(("stat", args[0] if args else "?"))
        raise OSError("filesystem blocked during plugin evaluation")

    builtins.open = blocked_open
    os.stat = blocked_stat
    try:
        for p in PLUGINS:
            p.evaluate(inspection, context)
    finally:
        builtins.open = real_open
        os.stat = real_stat

    assert not accesses, f"plugin accessed filesystem: {accesses}"


def stable_plan():
    with tempfile.TemporaryDirectory() as tmp:
        runs = []
        for name in ("first.json", "second.json"):
            out = os.path.join(tmp, name)
            subprocess.run(
                [sys.executable, LINTER, "plan", FIXTURE, "--out", out], check=True
            )
            with open(out, "rb") as f:
                runs.append(f.read())
    assert runs[0] == runs[1], "unchanged plan runs produced different artifacts"


def fixture_plan():
    inspection = Analyzer().analyze(FIXTURE)
    context = Context(root=FIXTURE)
    artifact = Planner().plan(inspection, context)
    payload = json.loads(artifact)

    run_names = [e["name"] for e in payload["run"]]
    skip_names = [e["name"] for e in payload["skip"]]

    assert "ruff" in run_names, f"ruff not in run: {run_names}"
    assert "markdownlint" in run_names, f"markdownlint not in run: {run_names}"
    assert "hadolint" in skip_names, f"hadolint not in skip: {skip_names}"

    for entry in payload["run"] + payload["skip"]:
        assert entry.get("reason"), f"missing reason on {entry['name']}"


def executor_acquisition_log():
    with tempfile.TemporaryDirectory() as tmp:
        diag_out = os.path.join(tmp, "diagnostics.json")
        log_out = os.path.join(tmp, "acquisition.log")
        subprocess.run(
            [sys.executable, LINTER, "run", FIXTURE, "--out", diag_out, "--log", log_out],
            check=True,
        )
        with open(log_out) as f:
            log_text = f.read()
        with open(diag_out) as f:
            diagnostics = json.loads(f.read())

    lines = [l for l in log_text.splitlines() if l.strip()]
    tools_logged = [l.split(":")[0] for l in lines]

    assert "ruff" in tools_logged, f"ruff not in acquisition log: {log_text!r}"
    assert "markdownlint" in tools_logged, f"markdownlint not in acquisition log: {log_text!r}"
    assert "hadolint" not in tools_logged, f"hadolint unexpectedly in acquisition log: {log_text!r}"

    ruff_line = next(l for l in lines if l.startswith("ruff:"))
    md_line = next(l for l in lines if l.startswith("markdownlint:"))
    assert "uvx" in ruff_line, f"ruff not acquired via uvx: {ruff_line!r}"
    assert "npx" in md_line, f"markdownlint not acquired via npx: {md_line!r}"

    assert isinstance(diagnostics, list)
    for d in diagnostics:
        for field in ("tool", "path", "location", "message"):
            assert field in d, f"missing field {field!r} in diagnostic: {d}"


def executor_wrapper_boundary():
    assert "ruff" in WRAPPERS, "ruff wrapper missing"
    assert "markdownlint" in WRAPPERS, "markdownlint wrapper missing"
    assert "hadolint" not in WRAPPERS, "hadolint wrapper must not exist"
    for name, wrapper in WRAPPERS.items():
        assert hasattr(wrapper, "acquire_cmd"), f"{name} missing acquire_cmd"
        assert hasattr(wrapper, "run"), f"{name} missing run"


def main():
    one_traversal()
    immutable_inspection()
    stable_artifact()
    no_filesystem_access()
    stable_plan()
    fixture_plan()
    executor_wrapper_boundary()
    executor_acquisition_log()
    print("ok: one traversal, immutable inspection, byte-equivalent artifact, deterministic plan, planned tools acquired and executed")


if __name__ == "__main__":
    main()
