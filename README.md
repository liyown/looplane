# Linear Loop System

Chinese docs: [README.zh-CN.md](README.zh-CN.md)

This repository maintains a Linear-based loop system for local agents.

The default model is runnerless: an AG platform or local agent host only starts the
scheduled prompt. Each loop performs its own allowed Linear, GitHub, local filesystem,
and `~/.linear-loop` state changes. There is no separate business runner that consumes
JSON commands.

For setup, start with [INSTALL.zh-CN.md](INSTALL.zh-CN.md).

## Shape

```text
Linear issue
  -> requirements, Discovery, Todo Brief, execution summary, verification

Linear Project Docs
  -> Agent Guidance / Repo Notes / Decision Log

~/.linear-loop
  -> state / locks / cooldowns / runtime issues / repos / worktrees

AG schedule
  -> starts the matching loop
```

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
~/.linear-loop/state/issues/
~/.linear-loop/state/locks/
~/.linear-loop/state/cooldowns/
~/.linear-loop/state/lesson-candidates.jsonl
~/.linear-loop/runtime-issues/YYYY-MM.jsonl
~/.linear-loop/repos/
~/.linear-loop/worktrees/
```

Local Loop Space stores runtime control state, locks, cooldowns, runtime issues, and
repo/worktree cache. It is not the default store for Discovery reports, Todo briefs,
or full run JSON history.

## Memory Placement

- Linear issue: issue-bound facts such as `[Discovery]`, `[Todo Brief]`, execution
  summary, verification, and blockers.
- Linear Project Docs: long-lived experience memory such as `Agent Guidance`,
  `Repo Notes/{repoSlug}`, and `Decision Log`.
- `~/.linear-loop`: cross-session runtime control state such as fingerprint, lock,
  cooldown, lesson candidates, and runtime issues.

Repository origins, default branches, and verification commands still belong in
Linear Project `Agent Project Settings`. The local directory does not replace project
settings or a repo registry.

## Maintainer Files

- [prompts/](prompts/) - modular prompt sources.
- [schemas/loop-result.schema.json](schemas/loop-result.schema.json) - Loop Final
  Report shape.
- [scripts/build-standalone-prompts.py](scripts/build-standalone-prompts.py) -
  generates the copy pack.
- [scripts/validate-copy-pack.py](scripts/validate-copy-pack.py) - validates the copy
  pack.
- [scripts/validate-loop-schema.py](scripts/validate-loop-schema.py) - validates schema
  and fixtures.
- [docs/usage.md](docs/usage.md) - operating notes for schedules, handoffs, state, and
  experience memory.

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
2. Claim an issue and record the observed Linear and `~/.linear-loop/state` snapshot.
3. Perform its own allowed Linear, GitHub, filesystem, and local state changes.
4. Re-read Linear and local state before writing.
5. Apply only if state, `updatedAt`, fingerprint, active run, and lease or lock data
   still match.
6. Escalate to Coordinator when the snapshot is stale.
7. Return a Loop Final Report for logs and exception rollups, not as a second database.

## Do Not

- Do not let every loop scan every issue.
- Do not let a state loop write after its observed snapshot is stale.
- Do not let code-backed work enter `Todo` without a fresh `[Discovery]` block.
- Do not let In Progress modify code without a Repo Manager write lock.
- Do not use Coordinator for routine state movement.
- Do not hide issue-bound evidence in `~/.linear-loop` as long-term truth.
- Do not hide prompt, schema, access, Linear setup, or local storage problems in
  comments only; emit `runtimeIssues[]` and append them to
  `~/.linear-loop/runtime-issues/YYYY-MM.jsonl`.
