# Looplane

Chinese docs: [README.zh-CN.md](README.zh-CN.md)

Looplane is a local agent loop for Linear issues. The schedule host only wakes the
agent. The agent reads Linear, GitHub, local repositories, and Project docs; decides
what to do next; acts; and writes durable results back.

This is loop engineering, not prompt engineering. The point is not to split work into
many brittle prompts. The point is to keep one useful loop sensing, acting, recording,
and correcting itself.

A real loop is more than a scheduled prompt. It needs a goal, success criteria, a
verifier, compact state, and a stop condition.

## Start Here

- [Local setup](INSTALL.zh-CN.md): initialize local runtime space and schedules.
- [Main loop prompt](prompts/agent-loop.md): paste into the recurring schedule.
- [Initial setup prompt](prompts/initial-setup.md): run once manually.
- [Maintenance loop prompt](prompts/maintenance-loop.md): optional low-frequency
  cleanup and learning loop.

## How It Runs

1. Initialize `~/.linear-loop`.
2. Run `prompts/initial-setup.md` once.
3. Run `prompts/agent-loop.md` manually on one small issue.
4. After one manual run is reliable, create a recurring schedule using
   `prompts/agent-loop.md`.
5. Optionally create a daily or weekly schedule using `prompts/maintenance-loop.md`.

The user does not need to understand a set of internal workers. The main loop handles
triage, context discovery, planning, implementation, verification, comments, state
updates, and blockers.

## Loop Shape

```text
schedule wakes agent-loop
  -> scan Linear
  -> choose useful issues
  -> define goal / success criteria / verifier / stop condition
  -> infer context from Linear / GitHub / Project docs / local repos
  -> act: clarify, plan, code, test, review, comment, move state
  -> verify
  -> iterate or stop
  -> write durable evidence
  -> remember lessons and runtime problems
```

Linear states are signals, not walls. The agent reads the current state and chooses
the most useful next step.

## When To Ask A Human

Default to action. Ask only when progress really depends on a human choice:

- missing account, secret, repository, or tool access;
- destructive data changes;
- production deploys or irreversible operations;
- security, legal, payment, privacy, or compliance decisions;
- product direction choices where several paths are plausible and costly;
- requirements too ambiguous for a small reversible step.

Ordinary uncertainty should not block the loop. The agent should take the smallest
reversible step, write the assumption in Linear, and continue.

## When Not To Loop

Do not schedule work that has no verifier, cannot be completed by the agent, or has no
objective done condition. Keep it as a manual prompt or one-off agent run until the
manual path is reliable.

Order matters:

```text
manual run -> stable prompt -> verifier and stop condition -> schedule
```

## Local Loop Space

Default directory:

```text
~/.linear-loop/config.yaml
~/.linear-loop/state/
~/.linear-loop/runtime-issues/YYYY-MM.jsonl
~/.linear-loop/repos/
~/.linear-loop/worktrees/
```

`~/.linear-loop` stores runtime state, local repo cache, worktrees, temporary notes,
and runtime issue logs. Long-lived truth belongs in Linear issues, Linear Project
docs, GitHub, or the repository.

Keep local state compact: goal, success criteria, verifier, attempt count, latest
failure, and next step. Do not store full transcripts or full run outputs by default.

## Prompt Files

- [prompts/initial-setup.md](prompts/initial-setup.md): one-time local and Linear
  setup.
- [prompts/agent-loop.md](prompts/agent-loop.md): the main scheduled loop.
- [prompts/maintenance-loop.md](prompts/maintenance-loop.md): optional cleanup and
  learning loop.

Edit prompt files directly. There is no generation step.
