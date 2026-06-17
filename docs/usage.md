# Usage

This document describes how to wire the prompts into an automation platform or a
small custom runner.

## Roles

| Role | Runs On | Writes Normal State Transitions | Main Job |
| --- | --- | --- | --- |
| Triage | `Triage` issues | Yes | Accept, cancel, or mark duplicates. |
| Backlog | `Backlog` issues | Yes | Bound scope, resolve target, request Discovery when needed. |
| Discovery | Internal handoff | No visible state by default | Read repository context and produce a report. |
| Todo | `Todo` issues | Yes | Build an execution brief from evidence. |
| In Progress | `In Progress` issues | Yes | Implement approved work in a locked worktree. |
| In Review | `In Review` issues | Yes | Verify work and move to Done or send it back. |
| Done | `Done` issues | Usually no | Keep final records tidy. |
| Canceled | `Canceled` issues | No | Keep terminal state stable. |
| Duplicate | `Duplicate` issues | No | Preserve canonical links and comments. |
| Memory/Reconcile | Internal handoff or schedule | No | Mark stale runs, expired runs, cooldowns, and drift. |
| Repo Manager | Internal handoff | No Linear state writes | Own clone, fetch, worktree, leases, locks, and verification. |
| Coordinator | Internal handoff or schedule | Only exceptional reroutes | Resolve CAS conflicts, unknown states, duplicate runs, and multi-repo coordination. |

## Runner Loop

Each scheduled state loop should do this:

```text
list issues in owned Linear state
for each candidate:
  load issue memory
  compute fingerprint
  skip unchanged blocked/no-op issues until nextEligibleAt
  create or reuse run reservation
  build context
  run the matching prompt
  validate JSON against schemas/loop-result.schema.json
  re-read Linear and memory
  compare observed snapshot with current state
  apply allowed changes only if the snapshot still matches
  otherwise mark stale/no-op and escalate when needed
```

The compare step must check at least:

- issue id
- Linear state
- Linear `updatedAt`
- labels hash
- description hash
- memory version
- fingerprint
- active run id
- lease or lock id when present

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

Coordinator should handle:

- `cas_conflict`
- `stale_run`
- `expired_lease`
- `unknown_state`
- `human_or_automation_drift`
- `multi_repo`
- `repo_or_lock_conflict`

## Linear Setup

Use this visible workflow:

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
Canceled / Duplicate
```

Default labels are defined in [docs/linear-loop-system-spec.md](linear-loop-system-spec.md).

Keep repository data out of high-cardinality labels unless the workspace is small.
The registry should carry repository origins and default verification commands.

## Repository Registry

Start from [examples/repo-registry.yaml](../examples/repo-registry.yaml).

The registry is the only source for clone URLs. A loop may infer a target repo slug
from project, area, template, linked PR, or history, but Repo Manager may clone only
origins present in the registry.

## Memory

Memory is runtime state. It should be rebuildable from Linear, registry, and Git with
some loss of convenience.

Suggested paths:

```text
memory/issues/{issueId}.json
memory/discovery/{issueId}.json
memory/repos/{repoSlug}.json
memory/projects/{projectSlug}.json
memory/runs/{runId}.json
```

`memory/` is ignored by git because it belongs to a runner instance.

## Discovery Gate

For code-backed work:

```text
Backlog
  -> requestedWorker: discovery
  -> Discovery report
  -> Backlog applies Todo when gates pass
```

Do not use issue text alone to enter `Todo`.

## Verification

Use the local protocol validator:

```sh
python3 scripts/validate-loop-schema.py
```

It checks:

- the schema exposes `requestedWorker`
- the schema uses `escalation`, not the old centralized action field
- Discovery and Todo evidence fields are required
- fixtures cover valid handoff, invalid Discovery report, valid execution brief, and
  CAS conflict escalation

## Adding A Loop

Before adding a new loop, decide whether it is:

- a visible state loop, which may scan and apply normal transitions for one Linear
  state;
- a service loop, which works from handoffs and should not own visible state;
- a Coordinator case, which should stay exceptional.

Add or update:

- prompt file in `prompts/`
- allowed transition in the spec
- schema field only if the existing contract cannot express the result
- at least one fixture if schema behavior changes
