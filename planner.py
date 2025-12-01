import json
from dataclasses import dataclass

from plugin import PLUGINS


@dataclass(frozen=True)
class Context:
    root: str


class Planner:
    def plan(self, inspection, context):
        run = []
        skip = []
        for p in PLUGINS:
            result = p.evaluate(inspection, context)
            if result["status"] == "run":
                run.append({
                    "name": p.name,
                    "reason": result["reason"],
                    "acquisition": result["acquisition"],
                    "command": result["command"],
                })
            else:
                skip.append({"name": p.name, "reason": result["reason"]})
        return json.dumps({"run": run, "skip": skip}, sort_keys=True, indent=2) + "\n"
