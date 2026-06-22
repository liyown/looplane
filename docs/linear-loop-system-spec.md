# Looplane System Spec

## Purpose

Looplane turns Linear into the visible work surface for a local agent loop. A schedule
wakes the agent. The agent chooses useful issues, reads context, acts, verifies, and
writes durable evidence back to Linear, GitHub, Project docs, and minimal local state.

The default system is intentionally small:

- one manual setup prompt;
- one recurring main agent loop;
- one optional low-frequency maintenance loop.

## Design Principle

The agent is an executor, not a flowchart interpreter. Linear states, labels, and
comments are signals that help it decide what to do next. They should not prevent the
agent from making an obvious safe step.

Default behavior:

1. infer from available context;
2. take the smallest useful reversible step;
3. write assumptions and evidence in Linear;
4. ask humans only when the missing decision is high-cost or requires access.

## Prompts

```text
prompts/initial-setup.md
prompts/agent-loop.md
prompts/maintenance-loop.md
```

`initial-setup.md` runs once. It creates the local runtime space and the minimum
Linear Project docs.

`agent-loop.md` is the main scheduled prompt. It handles triage, discovery, planning,
coding, verification, review notes, blockers, and state movement.

`maintenance-loop.md` is optional. It groups repeated runtime issues, promotes useful
lessons into Project docs, and suggests safe cleanup of stale local state.

## Local Runtime Space

```text
~/.linear-loop/config.yaml
~/.linear-loop/state/
~/.linear-loop/runtime-issues/YYYY-MM.jsonl
~/.linear-loop/repos/
~/.linear-loop/worktrees/
```

Local state is operational support, not project truth. The agent should be able to
rebuild most context from Linear, GitHub, Project docs, and the repository.

## Memory Placement

- Linear issue: task facts, decisions, progress, verification, blockers.
- Linear Project docs: team preferences, repo notes, repeated lessons, long-lived
  decisions.
- GitHub/repository: code, branches, commits, pull requests.
- `~/.linear-loop`: runtime state, repo cache, worktrees, temporary notes, runtime
  issue logs.

## Linear Workflow

Looplane does not require a special workflow. It can use common states such as:

```text
Triage -> Backlog -> In Progress -> In Review -> Done
Canceled / Duplicate
```

If a workspace uses different names, the agent should use the closest equivalent.
State transitions are useful when they make the board clearer for humans and later
runs.

## Human Confirmation Boundary

Ask for human input only when needed for:

- credentials, account access, or repository access;
- destructive changes;
- production deploys or irreversible operations;
- security, legal, payment, privacy, or compliance decisions;
- costly product direction choices;
- requirements too ambiguous for a small reversible step.

All other uncertainty should be handled by making a conservative assumption, writing
it down, and continuing.

## Concurrency

The main loop should re-read Linear and relevant local state before applying writes.
If another human or agent changed the same issue, adapt to the new state instead of
overwriting it.

This is a safety rule, not a heavyweight lock system. Use locks or active-run markers
only when overlapping writes would likely damage work, such as concurrent edits to
the same worktree.

## Runtime Issues

Runtime issue logs are iteration evidence for improving the loop. They are not task
requirements and not a second database.

Good entries describe repeated prompt gaps, setup gaps, missing tools, flaky
verification, bad repo inference, access problems, or recurring confusion in Linear
state conventions.
