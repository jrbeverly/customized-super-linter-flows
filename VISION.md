Linter Framework Design

Overview

This project aims to provide a lightweight, extensible linting framework for polyglot repositories without requiring a monolithic container image or tightly coupling lint execution to a specific CI platform.

The core philosophy is to separate repository analysis, planning, tool acquisition, and execution into independent stages with well-defined interfaces.

This enables:

- Local development using the same tooling as CI.
- Efficient CI execution without downloading unnecessary tooling.
- Pluggable acquisition strategies (Docker, native binaries, reusable actions, etc.).
- Small, focused plugins that operate on a common repository model instead of performing their own filesystem discovery.
- Consistent behaviour across Gitea Actions, GitHub Actions, Dev Containers, and local CLI execution.

---

Goals

- Eliminate the need for a large "everything included" container image.
- Run only the tools applicable to a repository.
- Detect repository characteristics exactly once.
- Make plugin behaviour deterministic and testable.
- Keep plugins as simple as possible.
- Support multiple execution environments using the same execution model.
- Encourage project configuration to live in ".linter/" rather than cluttering the repository root.

---

High-Level Architecture

Repository
     │
     ▼
Repository Analyzer
     │
     ▼
Repository Inspection
     │
     ▼
Execution Planner
     │
     ▼
Execution Plan
     │
     ▼
Plugin Wrapper
     │
     ▼
Tool Acquisition
     │
     ▼
Linter Execution
     │
     ▼
Diagnostics

Each stage has a single responsibility.

---

Repository Analyzer

The analyzer performs repository inspection exactly once.

Its purpose is to create a normalized view of the repository that all plugins can consume.

The analyzer is responsible for discovering things such as:

- Languages present
- Repository layout
- Monorepo characteristics
- Configuration files
- Dependency manifests
- CI environment
- Changed files (when available)
- Presence of Docker, Kubernetes, Terraform, etc.
- Available package managers

Rather than exposing only raw filesystem information, the analyzer should derive higher-level capabilities.

Example:

features:
  has-node: true
  has-python: true
  has-go: false
  has-docker: true
  has-markdown: true

languages:
  - javascript
  - typescript
  - markdown

packageManagers:
  - npm

configs:
  biome:
    path: .linter/biome.json

This inspection object is immutable for the duration of execution.

Plugins consume it but never modify it.

---

Repository Inspection

The inspection object becomes the common interface shared by the framework.

Every plugin receives the same model.

This avoids each plugin repeatedly asking questions like:

- Does package.json exist?
- Is this a Node project?
- Is this repository a monorepo?
- Are there any Dockerfiles?

Those questions are answered once.

Benefits include:

- Faster execution
- Consistent behaviour
- Easier testing
- Cleaner plugins
- Better caching opportunities

---

Execution Planner

The planner converts the repository inspection into an execution plan.

Conceptually:

Inspection
      │
      ▼
Available Plugins
      │
      ▼
Applicable Plugins
      │
      ▼
Execution Order

Each plugin evaluates the inspection against its own policy.

Example:

Biome
    requires:
        has-node

Hadolint
    requires:
        has-docker

Markdownlint
    requires:
        has-markdown

The planner determines:

- Which plugins should execute
- Which should be skipped
- Why they were skipped
- Acquisition method
- Execution strategy

The resulting plan is deterministic.

Example output:

✓ biome
✓ markdownlint
✓ hadolint

Skipped:

ruff
    reason: no python detected

golangci-lint
    reason: no go modules detected

This also enables a future "plan" command for debugging.

---

Plugin Model

Plugins should remain intentionally small.

They should not inspect the repository directly.

Instead, they receive:

- Repository inspection
- Plugin configuration
- Execution context

Their responsibilities are limited to:

- Determining applicability
- Declaring requirements
- Invoking the underlying tool
- Returning diagnostics

Conceptually:

Plugin

ShouldRun()

Acquire()

Execute()

Parse()

Fix()

Plugins should never concern themselves with:

- CI platform
- Filesystem discovery
- Tool caching
- Repository scanning

---

Tool Acquisition

Tool acquisition is intentionally separated from execution.

The framework supports multiple acquisition strategies.

Examples include:

- Native binary
- Docker
- OCI image
- Reusable Gitea Action
- mise
- GitHub Release
- Package manager
- System-installed executable

All acquisition methods expose a common executable interface.

For example:

Acquire()

↓

Executable

↓

Run()

Execution remains identical regardless of how the tool was obtained.

This allows a repository to switch acquisition methods without changing plugin logic.

---

Wrapper Layer

Every acquisition method implements a common wrapper interface.

Example:

Biome Plugin

↓

Wrapper

↓

Docker

or

Biome Plugin

↓

Wrapper

↓

mise

or

Biome Plugin

↓

Wrapper

↓

Local Binary

The plugin does not care where the executable originated.

---

Configuration Layout

Whenever possible, configuration should live inside a dedicated ".linter" directory.

Example:

.linter/

    biome.json

    markdownlint.json

    hadolint.yaml

    ruff.toml

    golangci.yml

    framework.yaml

Reasons include:

- Avoid cluttering repository root.
- Group lint-related configuration together.
- Simplify framework discovery.
- Allow future framework-specific metadata.

If a tool requires configuration in the repository root, the wrapper may:

- generate temporary configuration
- create symbolic links
- pass explicit configuration paths

The framework should prefer explicit configuration paths over copying files whenever supported.

---

Local Execution

The framework should behave identically locally and in CI.

Example:

linter run

or

linter plan

or

linter fix

No CI-specific behaviour should be required.

---

Dev Container Support

A Dev Container should provide the same developer experience as CI.

Example:

{
    "postCreateCommand": "linter install"
}

Developers can then execute:

linter run

using exactly the same plugins and configuration as CI.

No Docker-in-Docker should be required unless explicitly configured as an acquisition strategy.

---

Gitea Actions

A minimal workflow becomes:

steps:
  - uses: actions/checkout@v4

  - name: Analyze repository
    uses: my-org/linter/analyze@v1

  - name: Execute plan
    uses: my-org/linter/run@v1

Internally this becomes:

checkout

↓

analyze

↓

inspection

↓

planner

↓

plugins

↓

diagnostics

The action itself remains lightweight.

Only the required tools are acquired.

---

Future Pipeline

Long-term, the framework should expose each phase independently.

Analyze

↓

Plan

↓

Acquire

↓

Execute

↓

Publish

This separation allows future integrations to reuse earlier phases.

Examples include:

- IDE integration
- Pre-commit hooks
- Local CLI
- Dev Containers
- Gitea Actions
- GitHub Actions
- Remote execution
- Cached planning

---

Design Principles

Analyze once

Repository inspection should occur exactly once.

Immutable inspection

Plugins consume repository information but never modify it.

Declarative plugins

Plugins declare capabilities and requirements rather than inspecting the repository themselves.

Pluggable acquisition

Tool installation is independent from tool execution.

Consistent execution

The same execution plan should produce the same results regardless of environment.

Configuration locality

Lint-related configuration belongs in ".linter/" whenever the underlying tool permits.

Environment agnostic

The framework should not assume it is running in CI.

Local development is a first-class use case.

---

Summary

The framework separates linting into four independent concerns:

1. Analyze the repository.
2. Produce a normalized inspection model.
3. Generate a deterministic execution plan.
4. Acquire and execute only the required tools.

By making the repository inspection the shared interface between all plugins, the framework avoids redundant discovery work, simplifies plugin development, enables multiple acquisition strategies, and provides a consistent developer experience across local development, Dev Containers, and CI systems.