# Mysuperlinting

> [!WARNING]
> **AI-authored:** This change was autonomously planned and implemented by an AI software factory from a human-authored specification, with possible subsequent human review or modification.

> [!WARNING]
> This experiment is effectively abandoned. The generated material is retained primarily as a research artifact.

Demonstrates that a single-pass inspection, deterministic plan, and acquisition-separated execution produce byte-equivalent artifacts locally and in Gitea Actions.

- `./run.sh` — run the full pipeline; write `inspection.json`, `plan.json`, `diagnostics.json`, and `acquisition.log`.
- `./validate.sh` — rerun the pipeline twice and compare all four artifacts byte-for-byte.
- `make inspect` — write the inspection artifact to `inspection.json`.
- `make plan` — write the execution plan artifact to `plan.json`.
- `make run` — acquire and run only the planned tools; write `diagnostics.json` and `acquisition.log`.
- `make check` — prove one traversal, immutability, byte-equivalent reruns, filesystem isolation, deterministic plan, and correct executor behavior.

## Notes

- came out of work with MegaLinter from Ox Security
- idea; untangle the concept into a lightweight superlinter framework
- started with a vision; pushed it through the Factory with a bit more rigor
- did not pan out
- convoluted to work with
- too many components without clear value
- weak focus on the base/common case
- overall system just not very good
- would not recommend OCT adopt it as a real system
- mostly useful as another Factory artifact / learning example
