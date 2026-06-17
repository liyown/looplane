# Workflow Simulation and Edge-Case Review v1

This document validates the Linear agent team from the user's perspective. The goal is
to keep Linear easy to understand while preserving enough internal rigor for reliable
agent execution, including overlapping scheduler cycles and duplicate executors.

## 1. Normal User-Created Feature

User action:

- Creates a Linear issue with natural language only.
- Does not name a repository.

Visible flow:

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
```

Internal behavior:

1. Triage accepts the issue.
2. Backlog resolves `Target/Repo` from project, area, template, or history.
3. Backlog claims the issue and records a Backlog run; Discovery later claims the
   internal discovery handoff.
4. Repo Manager prepares a read-only checkout.
5. Discovery inspects repo files, tests, docs, and config.
6. Discovery report is recorded in local memory and summarized in a Linear comment.
7. Todo writes an execution brief that cites the Discovery report.
8. In Progress uses an active run reservation and write-locked worktree.
9. In Review verifies against issue, Discovery, execution brief, and tests.

User experience:

- No repository field is required.
- The board does not show internal Discovery by default.
- The issue comment explains what was read and why the task is now executable.

## 2. No-Code Task

Input:

- "Write launch checklist" or "Create decision record".

Flow:

```text
Triage -> Backlog -> Todo -> In Review -> Done
```

Expected behavior:

- Backlog sets `Target/No-Code`.
- Discovery is skipped.
- Todo still defines acceptance criteria and output artifact.
- In Review checks the artifact or Linear update.

## 3. Repository Inference Works

Input:

- Project is `Product A`.
- Linear Project agent settings map `Product A` to `product-a-app`.
- User does not specify repo.

Expected behavior:

- Backlog sets `Target/Repo` with high confidence.
- System does not ask the user.
- Discovery reads `product-a-app`.
- Todo may proceed only after Discovery report exists.

## 4. Repository Inference Conflict

Input:

- Project default suggests `web-app`.
- Area label suggests `api-service`.

Expected behavior:

- Backlog does not guess.
- Add `needs-info`.
- Ask one minimal choice: `web-app` or `api-service`.
- Store blocker and cooldown to avoid repeated prompts.

## 5. Todo Without Discovery Report

Input:

- Code-backed issue is moved manually to Todo before Discovery.

Expected behavior:

- Todo re-reads Linear and checks gates before applying.
- It keeps or returns the issue to a safe non-implementation state.
- It requests internal Discovery instead of allowing In Progress.
- It explains that Todo requires repository evidence.

## 6. User Changes Description After Todo

Input:

- Todo issue has Discovery report.
- User edits acceptance criteria.

Expected behavior:

- Fingerprint changes.
- Todo or Coordinator marks old Discovery stale in memory if the edit affects
  technical scope.
- Issue returns to Backlog or stays Todo with a blocking comment, depending on impact.
- No implementation starts from stale evidence.

## 7. Human Moves In Progress to Canceled

Input:

- Worker is running.
- Human moves issue to Canceled.

Expected behavior:

- The running state loop re-reads Linear before apply.
- Canceled wins.
- Active runs are marked stale.
- Worktree is retained or cleaned by retention policy, not by the worker.

## 8. Human Removes `needs-repo`

Input:

- Issue was blocked by `needs-repo`.
- Human removes the label without adding repo metadata.

Expected behavior:

- Backlog treats this as unblock intent.
- It re-runs target resolution.
- If still unresolved, it adds `needs-info` or writes one blocking comment rather than
  blindly restoring `needs-repo`.

## 9. GitHub PR Automation Moves State

Input:

- GitHub integration links a PR and moves issue forward.

Expected behavior:

- The owning state loop or Coordinator treats the update as an external signal.
- It does not overwrite state from old memory.
- If evidence conflicts, it chooses a safer non-terminal state and records a concise
  reconcile comment.

## 10. Multi-Repo Feature

Input:

- One issue requires web, API, and docs changes.

Expected behavior:

- Backlog sets `Target/Parent` and `multi-repo`.
- Coordinator creates or requests child issues, one per repo.
- Parent issue remains coordination-only.
- Children each run their own Discovery and implementation path.

## 11. Discovery Fails Due to Access

Input:

- Linear Project agent settings declare the repo, but clone/fetch fails.

Expected behavior:

- Repo Manager returns `needs-access`.
- Backlog remains blocked.
- Linear comment names the missing capability, not secrets.
- Backlog or Memory/Reconcile suppresses repeat attempts until cooldown or input
  changes.

## 12. Baseline Tests Already Fail

Input:

- Repo can be read and implemented, but default branch tests fail before edits.

Expected behavior:

- Repo Manager records baseline failure.
- Add `baseline-failing`.
- In Progress may continue only with focused verification or Coordinator approval.
- In Review distinguishes baseline failures from introduced failures.

## 13. Long-Running Implementation

Input:

- In Progress requires several sessions.

Expected behavior:

- Active run has heartbeat and expiry.
- Write lock has a lease.
- Progress comments are periodic and concise.
- Expired leases trigger Memory/Reconcile before another worker resumes.
- Stale workers cannot apply old outputs.

## 14. Previous Run Still Active When Next Scheduler Cycle Starts

Input:

- Backlog Discovery run is still active.
- Scheduler starts another cycle and sees the same issue.

Expected behavior:

- The owning loop computes the same run key: `issueId + loop + fingerprint`.
- If heartbeat is fresh, the owning loop does not start another Discovery worker.
- If heartbeat expired, the owning loop routes to Memory/Reconcile or Coordinator.
- If Linear changed and fingerprint is different, the old run is marked superseded and
  the owning loop retries from the latest issue snapshot.
- Output from the old run cannot move state unless fresh CAS checks still match
  current gates.

## 15. Multiple Executors Run the Same Loop

Input:

- Two local agents accidentally run Todo for the same issue/fingerprint.

Expected behavior:

- Both outputs include `observed.runId` and `observed.fingerprint`.
- At most one output matching the active run and current Linear snapshot may apply.
- The later duplicate becomes `no_op` unless it contains non-conflicting read-only
  evidence worth merging into memory.
- No duplicate executor can create an extra write lock or move state from stale data.

## 16. Duplicate In Progress Executor

Input:

- One executor already owns a write lock.
- Another executor starts In Progress for the same repo/worktree.

Expected behavior:

- Repo Manager refuses the second write lock and returns the active run ID.
- The second executor returns `blocked` or `no_op`.
- In Progress does not continue duplicate implementation work until the active run
  finishes, expires, or is reconciled.

## 17. Security-Sensitive Change

Input:

- Issue affects auth, billing, secrets, permissions, deletion, or production infra.

Expected behavior:

- Add `security-sensitive`.
- Set `Mode/Human` or `Mode/Hybrid`.
- Discovery and implementation may proceed, but Done requires human review evidence.

## 18. Optional Visible Discovery State

Default:

- Discovery is internal and appears as comments/activity, not a board column.

Advanced team preference:

- Add visible `Discovery` state between Backlog and Todo.
- Use the same Discovery worker prompt.
- Keep the same gates; only the Linear visualization changes.

## 19. Final Assessment

The v1 workflow is easier for users because:

- Users file normal issues without repo declarations.
- Linear status remains familiar.
- Technical discovery is mandatory but mostly invisible.
- The system asks for help only when target resolution is ambiguous.
- Manual status/label changes are reconciled, not overwritten.

The workflow is safer because:

- Todo cannot be based on speculation.
- Repo operations are centralized under read leases/write locks.
- Worker outputs echo observed run context.
- State loops use CAS before applying changes, and Coordinator handles old runs,
  duplicate executors, GitHub automation, and human edits when they conflict.
