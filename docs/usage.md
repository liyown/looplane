# Usage

This document complements [INSTALL.zh-CN.md](../INSTALL.zh-CN.md). The default model
is loop-first: schedules start loops, and each loop performs its own allowed Linear,
GitHub, filesystem, and `~/.linear-loop` operations after checking current state.

## Roles

| Role | Runs On | Prompt |
| --- | --- | --- |
| Initial setup | one manual run | `dist/zh-CN/prompts/initial-setup.standalone.md` |
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

## Memory Placement

```text
Linear issue
  [Discovery]
  [Todo Brief]
  execution summary
  verification result
  blocker / needs-info reason

Linear Project Docs
  Agent Guidance
  Repo Notes/{repoSlug}
  Decision Log

~/.linear-loop
  state/issues/
  state/locks/
  state/cooldowns/
  state/lesson-candidates.jsonl
  runtime-issues/YYYY-MM.jsonl
  repos/
  worktrees/
```

`~/.linear-loop` is not the default store for Discovery reports, Todo briefs, or full
run JSON history.

## Loop Flow

Each scheduled state loop closes its own loop:

```text
list issues in the owned Linear state
for each candidate:
  read Linear issue, labels, comments, project, and Project docs
  read minimal local state from ~/.linear-loop/state
  compute fingerprint
  skip unchanged blocked/no-op issues until nextEligibleAt
  claim or verify active run state
  perform the loop-specific work
  re-read Linear and ~/.linear-loop/state
  compare observed snapshot with current state
  apply allowed Linear / GitHub / filesystem / local state changes only if the snapshot still matches
  otherwise mark stale/no-op and escalate when needed
  append runtimeIssues[] to ~/.linear-loop/runtime-issues/YYYY-MM.jsonl when present
  return Loop Final Report for logs and exception rollups
```

The compare step must check at least issue id, Linear state, `updatedAt`, labels hash,
description/comment evidence hash, local state version, fingerprint, active run id,
and lease or lock id when present.

## Handoffs

Use `requestedWorker` to summarize that this loop marked or created follow-up work:

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
  -> Discovery writes [Discovery] to the Linear issue
  -> Backlog or Todo proceeds when gates pass
```

Do not use issue text alone to enter `Todo`. Todo writes `[Todo Brief]` back to the
Linear issue.

## Experience Memory

Loops may write candidate lessons to `~/.linear-loop/state/lesson-candidates.jsonl`.
This is only a staging area.

Memory/Reconcile or Coordinator promotes a lesson only when it is repeated,
non-issue-specific, actionable, and useful to future loops or humans.

Promoted lessons go to Linear Project Docs:

- `Agent Guidance`
- `Repo Notes/{repoSlug}`
- `Decision Log`

Discard weak candidates instead of turning local state into a knowledge base.

## Runtime Issue Log

Loops use `runtimeIssues[]` for problems in the loop system itself:

- prompt instructions were ambiguous or missing;
- schema could not express a needed result;
- a loop did not enforce a required write rule;
- Linear setup was missing or inconsistent;
- Repo Manager lacked access to a declared origin;
- a required tool was unavailable;
- verification was flaky;
- Linear entered a state the loop set does not handle;
- the schedule could not access `~/.linear-loop`.

The loop appends each entry to `~/.linear-loop/runtime-issues/YYYY-MM.jsonl`.
Memory/Reconcile groups repeated records and turns them into prompt, schema, loop
runtime, or Linear setup changes.

## Maintaining The Copy Pack

`prompts/` is source. `dist/zh-CN/prompts/` is what users paste into runtime entries:
Initial setup is run manually once, and recurring loops are pasted into schedules.

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
- schema and fixtures when the final report shape changes
