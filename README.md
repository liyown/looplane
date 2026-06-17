# Linear Agent Loop System

This repository defines a generic Linear-driven local agent loop collaboration system.
It is designed to work with an empty Linear workspace after initialization, and to
scale to multiple projects, repositories, and local agent workers.

The default profile is intentionally small: Linear stays readable, state loops own
normal progression for their source states, and the Coordinator loop owns exception
handling, conflict resolution, and cross-loop reconciliation.

## Artifacts

- `docs/linear-loop-system-spec.md` - System design, workflow, state machine, labels,
  repository registry, memory model, and edge-case handling.
- `docs/workflow-simulation-and-edge-cases.md` - Normal and failure-path simulations
  used to validate the workflow design.
- `prompts/` - Prompt files for the Coordinator loop, init loop, repo manager behavior,
  internal Discovery worker, and every visible Linear issue state loop.
- `schemas/loop-result.schema.json` - Structured output contract for every loop,
  including escalation signals and core Discovery/Todo evidence fields.
- `scripts/validate-loop-schema.py` - Lightweight local protocol validator for schema
  shape and example loop results.
- `tests/fixtures/loop-results/` - Positive and negative loop-result examples used by
  the validator.
- `examples/repo-registry.yaml` - Example project/repository registry.
- `examples/memory-issue.json` - Example per-issue execution memory.

## Validation

Run the local protocol validator after changing the loop-result schema, prompts, or
fixtures:

```sh
python3 scripts/validate-loop-schema.py
```

## Core Idea

Linear is the human-visible collaboration source of truth. Local memory is runtime
execution state. Each state loop may scan, claim, process, and apply allowed
transitions for the Linear state it owns. Before applying, a state loop re-reads
Linear and memory and applies only when its observed snapshot still matches. The
Coordinator loop handles CAS conflicts, stale runs, duplicate executors, unknown
states, manual edits, GitHub automation drift, and cross-repo coordination.

```text
Linear workspace
  -> Scheduled state loops
     -> Triage / Backlog / Todo / In Progress / In Review / terminal loops
     -> Discovery worker through Backlog/Todo handoff
     -> Repo Manager for leases, locks, worktrees, and verification
  -> Coordinator loop for exceptions and reconciliation
  -> Linear updates
```

The default visible issue flow stays simple:

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
```

Code-backed issues pass through an internal read-only Discovery gate before
Todo, but Discovery is not a default Linear board state.

Terminal paths:

```text
Triage|Backlog -> Duplicate
Triage|Backlog -> Canceled
```
