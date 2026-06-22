# Workflow Simulation And Edge Cases

These examples describe the simplified Looplane model: one main agent loop, plus an
optional maintenance loop.

## Natural-Language Feature

Input:

- A user creates a Linear issue without naming a repository.

Expected behavior:

1. The main loop reads the issue, project, labels, linked PRs, Project docs, and local
   repo cache.
2. It infers the likely repo if confidence is reasonable.
3. It inspects code before planning.
4. It writes a short assumption and plan in Linear.
5. It implements the smallest useful change, verifies it, and updates Linear.

The user should not have to manually route the issue through Discovery or Todo.

## No-Code Task

Input:

- "Write a launch checklist" or "Create a decision record".

Expected behavior:

- The main loop recognizes that no repository work is required.
- It writes the artifact in Linear or Project docs.
- It updates state when useful and records what changed.

## Repository Inference Conflict

Input:

- Project context suggests `web-app`.
- Issue text strongly suggests `api-service`.

Expected behavior:

- The main loop inspects available evidence: linked PRs, Project docs, labels, repo
  names, and local cache.
- If one repo becomes likely, it records the assumption and proceeds with a small
  reversible step.
- If confidence remains low and wrong choice would be costly, it asks one concrete
  question in Linear.

## User Changes Issue During A Run

Input:

- The agent is planning or coding.
- A human edits the issue or changes state.

Expected behavior:

- Before writing, the loop re-reads Linear.
- If the human change affects the work, the loop adapts or stops before applying stale
  changes.
- It leaves a concise note only when the conflict matters.

## Access Missing

Input:

- The loop identifies the repo but cannot clone or fetch it.

Expected behavior:

- It labels or comments with the missing capability.
- It does not ask for secrets in public issue text.
- It records a runtime issue if the setup gap is likely to repeat.

## Baseline Fails

Input:

- Tests fail on the existing default branch before the agent changes anything.

Expected behavior:

- The loop records baseline failure.
- It still uses focused verification when possible.
- It distinguishes pre-existing failures from failures introduced by its change.

## Repeated Bad Assumption

Input:

- Runtime issue logs show the same repo inference mistake several times.

Expected behavior:

- The maintenance loop promotes a lesson into `Repo Notes/{repoSlug}` or
  `Agent Guidance`.
- The main loop uses that guidance in later runs.

## Destructive Operation

Input:

- An issue asks the agent to delete production data or deploy a risky migration.

Expected behavior:

- The loop stops before the irreversible step.
- It explains the risk and asks for explicit human confirmation.
