# Linear Loop System

中文文档: [README.zh-CN.md](README.zh-CN.md)

This repository defines a Linear-based work loop for local agents.

It is not a runner. It contains the prompts, schema, examples, and operating rules a
runner needs in order to move Linear issues through a small workflow without letting
separate loops overwrite each other.

The intended shape is:

```text
Linear issues
  -> scheduled state loops
     -> Triage / Backlog / Todo / In Progress / In Review / terminal loops
  -> service loops
     -> Discovery / Repo Manager / Memory-Reconcile
  -> Coordinator
     -> conflicts, stale runs, unknown states, lock problems, multi-repo work
```

State loops do normal work. Coordinator handles exceptions.

## What Is In This Repo

- `prompts/` - One prompt per loop role.
- `schemas/loop-result.schema.json` - Required JSON shape for loop output.
- `scripts/validate-loop-schema.py` - Local protocol check for the schema and fixtures.
- `tests/fixtures/loop-results/` - Example valid and invalid loop results.
- `docs/linear-loop-system-spec.md` - Full operating model.
- `docs/workflow-simulation-and-edge-cases.md` - Expected behavior for common and
  failure-path runs.
- `examples/memory-issue.json` - Example issue memory record.

## Operating Model

Each visible Linear state has its own scheduled loop:

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
```

`Canceled` and `Duplicate` are terminal maintenance loops.

Discovery is internal by default. A code-backed issue does not move to `Todo` until
Discovery has produced a fresh report.

Every state loop follows the same write rule:

1. Scan only the state it owns.
2. Claim an issue by creating or reusing a run reservation.
3. Record the observed Linear and memory snapshot.
4. Run the matching prompt.
5. Validate the JSON result.
6. Re-read Linear and memory.
7. Apply only if state, `updatedAt`, fingerprint, active run, and relevant lease or
   lock data still match.
8. If the check fails, do not apply. Escalate to Coordinator.

This is the main safety rule. Do not replace it with a best-effort update.

## Minimum Runner Requirements

A platform using these prompts needs:

- Linear read/write access for issues, comments, labels, projects, and statuses.
- A persistent memory store for fingerprints, runs, discovery reports, locks, and
  cooldowns.
- A runtime issue log, normally `memory/runtime-issues/YYYY-MM.jsonl`, for problems
  found while the loops run.
- Linear Project agent settings for repository origins and verification commands.
  Agents must not infer clone URLs.
- A way to run one prompt per loop role and validate JSON output.
- Repo Manager access for clone, fetch, worktree, read lease, write lock, baseline,
  and verification commands.

If your platform only supports schedules, schedule the state loops separately. Do not
schedule every loop against every issue.

## Quick Start

1. Run [prompts/initial-loop.md](prompts/initial-loop.md) against the Linear
   workspace.
2. Fill in each managed Linear Project's Agent Project Settings.
3. Load `schemas/loop-result.schema.json` into your runner's output validation step.
4. Configure one scheduled job per visible state:

   ```text
   Triage       -> prompts/triage-loop.md
   Backlog      -> prompts/backlog-loop.md
   Todo         -> prompts/todo-loop.md
   In Progress  -> prompts/in-progress-loop.md
   In Review    -> prompts/in-review-loop.md
   Done         -> prompts/done-loop.md
   Canceled     -> prompts/canceled-loop.md
   Duplicate    -> prompts/duplicate-loop.md
   ```

5. Configure service loops:

   ```text
   Discovery        -> prompts/discovery-loop.md
   Repo Manager     -> prompts/repo-manager.md
   Memory/Reconcile -> prompts/memory-reconcile-loop.md
   Coordinator      -> prompts/coordinator-loop.md
   ```

6. Make each state loop process only its owned source state.
7. Make each state loop perform the claim and compare-and-set check before writing.
8. Route `requestedWorker` handoffs to the matching service loop.
9. Route `escalation.target: "coordinator"` to Coordinator.

More detail is in [docs/usage.md](docs/usage.md).

## Validate Changes

Run this after changing schema, prompts, or fixtures:

```sh
python3 scripts/validate-loop-schema.py
```

Expected output:

```text
validated schema shape and 5 fixtures
```

## What Not To Do

- Do not let every loop scan every Linear issue.
- Do not let a state loop write after its observed snapshot is stale.
- Do not let code-backed work enter `Todo` without a fresh Discovery report.
- Do not let implementation run without a Repo Manager write lock.
- Do not use Coordinator for routine state movement.
- Do not hide runner, prompt, schema, access, or setup problems in free-form comments;
  emit `runtimeIssues[]` so the next iteration has evidence.
