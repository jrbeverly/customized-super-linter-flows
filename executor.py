import json
import os

from wrapper import WRAPPERS

_CONFIGS = {
    "ruff": os.path.join(".linter", "ruff.toml"),
    "markdownlint": os.path.join(".linter", "markdownlint.json"),
}


class Executor:
    def execute(self, plan, fixture, log_path):
        log_entries = []
        all_diagnostics = []

        for entry in plan["run"]:
            name = entry["name"]
            wrapper = WRAPPERS.get(name)
            if wrapper is None:
                continue
            config = os.path.join(fixture, _CONFIGS[name])
            log_entries.append({"tool": name, "command": wrapper.acquire_cmd})
            all_diagnostics.extend(wrapper.run(fixture, config))

        with open(log_path, "w") as f:
            for entry in log_entries:
                f.write(f"{entry['tool']}: {entry['command']}\n")

        return json.dumps(all_diagnostics, sort_keys=True, indent=2) + "\n"
