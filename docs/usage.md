# Usage

The default Looplane model has one main loop: `agent-loop.md`. A schedule wakes it up.
It scans Linear, chooses useful work, and takes the next step.

## Prompts

| Purpose | Prompt |
| --- | --- |
| One-time setup | `prompts/initial-setup.md` |
| Main schedule | `prompts/agent-loop.md` |
| Optional maintenance schedule | `prompts/maintenance-loop.md` |

## Main Loop

```text
read Linear / GitHub / Project docs / ~/.linear-loop
choose useful issues
write goal / success criteria / verifier / stop condition
decide the next step
act: clarify, plan, inspect code, edit, verify, comment, move state
verify the result
fix the weakest failure and retry when needed
write durable evidence
record runtime issues and lessons
```

The main loop does not require separate pre-analysis or planning workers. When it
needs code context, it inspects the code. When it needs a plan, it writes one. When it
can implement, it creates a worktree, edits, verifies, and records the result.

## Loop Protocol

Each issue should move through a small loop:

```text
DISCOVER -> PLAN -> EXECUTE -> VERIFY -> ITERATE OR STOP
```

Verify is what makes this a loop instead of repeated guessing. Prefer hard verifiers:

- tests;
- type checks;
- lint;
- build;
- format check;
- smoke command;
- Linear acceptance criteria;
- CI or PR status.

When no hard verifier exists, use a strict rubric and score each criterion. Weak
scores are failures, not success with caveats.

Default to at most 3 execute/verify iterations per issue per scheduled run. Stop when
the verifier passes. If the limit is reached, write what still fails and the next best
step in Linear.

## What Belongs On A Schedule

Scheduled loop work should usually have these properties:

- it recurs or belongs to an ongoing Linear queue;
- the agent can act end to end with available tools;
- bad output can be rejected by tests, builds, lint, rules, or acceptance criteria;
- done is objective enough to stop.

If those are missing, keep the action small or manual until the path is reliable.

## Linear State

States are signals, not boundaries. The main loop can decide what the issue needs:

- new issue: accept, label, close, mark duplicate, or ask for necessary information;
- clear requirement: refine acceptance criteria and move toward execution;
- code issue: find the repo, inspect code, plan, implement, verify;
- implemented work: write verification notes and move toward review or done;
- true blocker: explain what is blocked and what human action is needed.

If a workspace uses different state names, the agent should use the closest available
state and explain the mapping once.

## Human Confirmation

Do not ask just because information is imperfect. Default to the smallest reversible
step.

Ask a human only for:

- missing account, secret, repository, or tool access;
- destructive data changes;
- production deploys or irreversible operations;
- security, legal, payment, privacy, or compliance choices;
- costly product direction choices;
- requirements too ambiguous for a small reversible step.

For ordinary uncertainty, write the assumption in Linear and continue.

## Memory Placement

```text
Linear issue
  task facts
  decisions
  progress notes
  verification result
  blocker reason

Linear Project docs
  Agent Guidance
  Agent Project Settings
  Repo Notes/{repoSlug}
  Decision Log

~/.linear-loop
  state/
  runtime-issues/YYYY-MM.jsonl
  repos/
  worktrees/
```

The local directory is not a second project database. Anything humans or later agents
need should usually live in Linear or GitHub.

## Runtime Issues

When the agent finds a problem with the loop system itself, append a line to:

```text
~/.linear-loop/runtime-issues/YYYY-MM.jsonl
```

Good examples:

- unclear prompt rules;
- Linear setup gaps;
- missing repo origin or verification commands;
- missing tool or access;
- repeated task blockers;
- repeated bad assumptions.

The maintenance loop groups repeated issues into Project docs or prompt improvements.
