import json
import os
import re
import subprocess


class RuffWrapper:
    name = "ruff"
    acquire_cmd = "uvx ruff@0.16.5"

    def run(self, fixture, config):
        result = subprocess.run(
            ["uvx", "ruff@0.16.5", "check", "--output-format", "json", "--config", config, fixture],
            capture_output=True,
            text=True,
        )
        findings = json.loads(result.stdout or "[]")
        return [
            {
                "location": f"{f['location']['row']}:{f['location']['column']}",
                "message": f"{f['code']} {f['message']}",
                "path": os.path.relpath(f["filename"], fixture),
                "tool": "ruff",
            }
            for f in findings
        ]


class MarkdownlintWrapper:
    name = "markdownlint"
    acquire_cmd = "npx markdownlint-cli@0.44.0"

    def run(self, fixture, config):
        md_files = []
        for dirpath, _, filenames in os.walk(fixture):
            for name in sorted(filenames):
                if name.endswith(".md"):
                    md_files.append(os.path.join(dirpath, name))
        if not md_files:
            return []
        result = subprocess.run(
            ["npx", "markdownlint-cli@0.44.0", "--config", config] + md_files,
            capture_output=True,
            text=True,
        )
        pattern = re.compile(r"^(.+):(\d+)(?::(\d+))?\s+(.+)$")
        diagnostics = []
        for line in result.stdout.splitlines():
            m = pattern.match(line.strip())
            if not m:
                continue
            path_abs, row, col, message = m.group(1), m.group(2), m.group(3), m.group(4)
            diagnostics.append({
                "location": f"{row}:{col}" if col else row,
                "message": message,
                "path": os.path.relpath(path_abs, fixture),
                "tool": "markdownlint",
            })
        return diagnostics


WRAPPERS = {
    "ruff": RuffWrapper(),
    "markdownlint": MarkdownlintWrapper(),
}
