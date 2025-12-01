from dataclasses import dataclass


@dataclass(frozen=True)
class Plugin:
    name: str
    requires: str
    run_reason: str
    skip_reason: str
    acquisition: str
    command: str

    def evaluate(self, inspection, context):
        if inspection.features.get(self.requires):
            return {
                "acquisition": self.acquisition,
                "command": self.command,
                "reason": self.run_reason,
                "status": "run",
            }
        return {"reason": self.skip_reason, "status": "skip"}


PLUGINS = [
    Plugin(
        name="ruff",
        requires="has-python",
        run_reason="Python files detected",
        skip_reason="no Python detected",
        acquisition="pip",
        command="ruff check --config .linter/ruff.toml .",
    ),
    Plugin(
        name="markdownlint",
        requires="has-markdown",
        run_reason="Markdown files detected",
        skip_reason="no Markdown detected",
        acquisition="npm",
        command="markdownlint --config .linter/markdownlint.json .",
    ),
    Plugin(
        name="hadolint",
        requires="has-dockerfile",
        run_reason="Dockerfile detected",
        skip_reason="no Dockerfile detected",
        acquisition="binary",
        command="hadolint --config .linter/hadolint.yaml Dockerfile",
    ),
]
