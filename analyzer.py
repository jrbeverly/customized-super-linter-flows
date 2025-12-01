"""The repository analyzer: one walk, one frozen inspection."""

import os
import tomllib

from inspection import Inspection


class Analyzer:
    """Walks a repository exactly once and derives an immutable inspection.

    `walk` is injectable only so checks can count or fail extra traversals;
    it is not a filesystem abstraction.
    """

    def __init__(self, walk=os.walk):
        self.walk = walk
        self.traversals = 0

    def analyze(self, root):
        self.traversals += 1
        files = self._collect(root)
        return Inspection(
            features={
                "has-python": any(f.endswith(".py") for f in files),
                "has-markdown": any(f.endswith(".md") for f in files),
                "has-dockerfile": any(
                    os.path.basename(f).lower() == "dockerfile" for f in files
                ),
            },
            configs=self._resolve_configs(root, files),
        )

    def _collect(self, root):
        files = []
        for dirpath, dirnames, filenames in self.walk(root):
            dirnames.sort()
            for name in filenames:
                files.append(os.path.relpath(os.path.join(dirpath, name), root))
        return files

    def _known_configs(self, root):
        with open(os.path.join(root, ".linter", "framework.toml"), "rb") as f:
            return tomllib.load(f)["linters"]

    def _resolve_configs(self, root, files):
        present = set(files)
        return {
            name: {"path": path, "exists": path in present}
            for name, path in self._known_configs(root).items()
        }
