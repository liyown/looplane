# Linear Loop System

Chinese docs: [README.zh-CN.md](README.zh-CN.md)

This repository maintains a Linear-based loop system for local agents.

Default use is local: the agent or AG platform can access the user's home directory,
runtime state lives in `~/.linear-loop`, and each schedule receives one self-contained
prompt from `dist/zh-CN/prompts/*.standalone.md`.

For setup, start with [INSTALL.zh-CN.md](INSTALL.zh-CN.md).

## Shape

```text
Linear
  -> visible states: Triage / Backlog / Todo / In Progress / In Review / Done
  -> terminal maintenance: Canceled / Duplicate
  -> internal services: Discovery / Repo Manager / Memory-Reconcile / Coordinator

~/.linear-loop
  -> memory / repos / worktrees / runtime issue logs
```

Linear is the collaboration surface. `~/.linear-loop` is the local runtime space.

Coordinator handles exceptions only: conflicts, stale runs, unknown states, lock
problems, and multi-repo coordination.

## User-Facing Files

- [INSTALL.zh-CN.md](INSTALL.zh-CN.md) - local installation and startup.
- [dist/zh-CN/prompts/](dist/zh-CN/prompts/) - standalone prompts to paste into
  schedules.

Do not paste source prompts from `prompts/` into schedules. They are modular sources
and do not embed the shared contract.

## Local Loop Space

The default runtime directory is:

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

Repository origins, default branches, and verification commands still belong in
Linear Project `Agent Project Settings`. The local directory stores runtime evidence
and cache only.

## Maintainer Files

- [prompts/](prompts/) - modular prompt sources.
- [schemas/loop-result.schema.json](schemas/loop-result.schema.json) - loop output
  shape.
- [scripts/build-standalone-prompts.py](scripts/build-standalone-prompts.py) -
  generates the copy pack.
- [scripts/validate-copy-pack.py](scripts/validate-copy-pack.py) - validates the copy
  pack.
- [scripts/validate-loop-schema.py](scripts/validate-loop-schema.py) - validates schema
  and fixtures.
- [docs/usage.md](docs/usage.md) - operating notes for schedules, handoffs, and
  maintenance.

After changing prompts, run:

```sh
python3 scripts/build-standalone-prompts.py
python3 scripts/build-standalone-prompts.py --check
python3 scripts/validate-copy-pack.py
python3 scripts/validate-loop-schema.py
```

## Write Rule

Each state loop must:

1. Scan only the Linear state it owns.
2. Claim an issue and record the observed Linear and `~/.linear-loop` snapshot.
3. Run the matching standalone prompt.
4. Return JSON.
5. Re-read Linear and local memory before writing.
6. Apply only if state, `updatedAt`, fingerprint, active run, and lease or lock data
   still match.
7. Escalate to Coordinator when the snapshot is stale.

This rule is the safety boundary.

## Do Not

- Do not let every loop scan every issue.
- Do not let a state loop write after its observed snapshot is stale.
- Do not let code-backed work enter `Todo` without a fresh Discovery report.
- Do not let In Progress modify code without a Repo Manager write lock.
- Do not use Coordinator for routine state movement.
- Do not hide prompt, schema, access, Linear setup, or local storage problems in
  comments only; emit `runtimeIssues[]` and append them to
  `~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl`.
