# Usage

This document complements [INSTALL.zh-CN.md](../INSTALL.zh-CN.md). The default model
is local execution: schedules can access `~/.linear-loop`.

## Roles

| Role | Runs On | Prompt |
| --- | --- | --- |
| Initial | one manual run | `dist/zh-CN/prompts/initial-loop.standalone.md` |
| Triage | `Triage` issues | `dist/zh-CN/prompts/triage-loop.standalone.md` |
| Backlog | `Backlog` issues | `dist/zh-CN/prompts/backlog-loop.standalone.md` |
| Todo | `Todo` issues | `dist/zh-CN/prompts/todo-loop.standalone.md` |
| In Progress | `In Progress` issues | `dist/zh-CN/prompts/in-progress-loop.standalone.md` |
| In Review | `In Review` issues | `dist/zh-CN/prompts/in-review-loop.standalone.md` |
| Done | `Done` issues | `dist/zh-CN/prompts/done-loop.standalone.md` |
| Canceled | `Canceled` issues | `dist/zh-CN/prompts/canceled-loop.standalone.md` |
| Duplicate | `Duplicate` issues | `dist/zh-CN/prompts/duplicate-loop.standalone.md` |
| Discovery | internal handoff | `dist/zh-CN/prompts/discovery-loop.standalone.md` |
| Repo Manager | internal handoff | `dist/zh-CN/prompts/repo-manager.standalone.md` |
| Memory/Reconcile | schedule or internal handoff | `dist/zh-CN/prompts/memory-reconcile-loop.standalone.md` |
| Coordinator | exception handling | `dist/zh-CN/prompts/coordinator-loop.standalone.md` |

State loops scan only their owned state. Service loops do not own normal visible
states.

## Local Loop Space

Runtime state lives here:

```text
~/.linear-loop/config.yaml
~/.linear-loop/memory/issues/
~/.linear-loop/memory/discovery/
~/.linear-loop/memory/repos/
~/.linear-loop/memory/projects/
~/.linear-loop/memory/decisions/
~/.linear-loop/memory/runs/
~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl
~/.linear-loop/repos/
~/.linear-loop/worktrees/
```

Memory records fingerprints, run reservations, Discovery reports, leases, locks,
cooldowns, and runtime issues. Repo Manager owns `repos` and `worktrees`.

## Runner Loop

Each scheduled state loop should do this:

```text
list issues in the owned Linear state
for each candidate:
  load issue memory from ~/.linear-loop
  compute fingerprint
  skip unchanged blocked/no-op issues until nextEligibleAt
  create or reuse run reservation
  build context
  run the matching standalone prompt
  require JSON output
  re-read Linear and ~/.linear-loop memory
  compare observed snapshot with current state
  apply allowed changes only if the snapshot still matches
  otherwise mark stale/no-op and escalate when needed
  append runtimeIssues[] to ~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl
```

The compare step must check at least issue id, Linear state, `updatedAt`, labels hash,
description hash, memory version, fingerprint, active run id, and lease or lock id
when present.

## Handoffs

Use `requestedWorker` for ordinary internal handoffs:

```json
{
  "nextState": "Backlog",
  "requestedWorker": "discovery"
}
```

Use `escalation` for blocking or exceptional handoffs:

```json
{
  "status": "blocked",
  "nextState": null,
  "requestedWorker": "coordinator",
  "escalation": {
    "target": "coordinator",
    "kind": "cas_conflict",
    "blocking": true,
    "reason": "Current Linear updatedAt no longer matches the observed snapshot."
  }
}
```

Coordinator handles CAS conflicts, stale runs, expired leases, unknown states,
human/automation drift, multi-repo decisions, and repo or lock conflicts.

## Linear Project Agent Settings

Store project settings on the Linear Project, either in the project description or in
a linked project document named `Agent Project Settings`.

```yaml
agent:
  version: 1
  defaultTarget:
    kind: code
    repo: product-a-app
    confidence: high
  repos:
    product-a-app:
      origin: git@github.com:org/product-a.git
      defaultBranch: main
      verify:
        test: pnpm test
  componentMap:
    Area/Frontend:
      kind: code
      repo: product-a-app
      confidence: high
```

Backlog may infer a repo slug from project, area label, issue template, linked PR, or
history. Repo Manager may clone only origins declared in the Linear Project settings.

## Discovery Gate

For code-backed work:

```text
Backlog
  -> requestedWorker: discovery
  -> Discovery report in ~/.linear-loop/memory/discovery/
  -> Backlog applies Todo when gates pass
```

Do not use issue text alone to enter `Todo`.

## Runtime Issue Log

Loops use `runtimeIssues[]` for problems in the loop system itself:

- prompt instructions were ambiguous or missing;
- schema could not express a needed result;
- runner did not enforce a required write rule;
- Linear setup was missing or inconsistent;
- Repo Manager lacked access to a declared origin;
- a required tool was unavailable;
- verification was flaky;
- Linear entered a state the loop set does not handle;
- the schedule could not access `~/.linear-loop`.

The runner appends each entry to
`~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl`. Memory/Reconcile groups repeated
records and turns them into prompt, schema, runner, or Linear setup changes.

## Maintaining The Copy Pack

`prompts/` is source. `dist/zh-CN/prompts/` is what users paste into schedules.

After source changes, run:

```sh
python3 scripts/build-standalone-prompts.py
python3 scripts/build-standalone-prompts.py --check
python3 scripts/validate-copy-pack.py
python3 scripts/validate-loop-schema.py
```

When adding a loop, update:

- the source prompt in `prompts/`
- `scripts/build-standalone-prompts.py`
- `scripts/validate-copy-pack.py`
- schema and fixtures when the output contract changes
