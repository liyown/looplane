# 使用方式

这份文档补充 [INSTALL.zh-CN.md](../INSTALL.zh-CN.md)。默认模型是 loop-first：
schedule 只启动 loop，loop 自己读写 Linear、GitHub、本地文件和
`~/.linear-loop`，并在写入前完成自己的状态检查。

## 运行角色

| 角色 | 运行对象 | prompt |
| --- | --- | --- |
| Initial setup | 一次性手动运行 | `prompts/initial-setup.md` |
| Triage | `Triage` issue | `prompts/triage-loop.md` |
| Backlog | `Backlog` issue | `prompts/backlog-loop.md` |
| Todo | `Todo` issue | `prompts/todo-loop.md` |
| In Progress | `In Progress` issue | `prompts/in-progress-loop.md` |
| In Review | `In Review` issue | `prompts/in-review-loop.md` |
| Done | `Done` issue | `prompts/done-loop.md` |
| Canceled | `Canceled` issue | `prompts/canceled-loop.md` |
| Duplicate | `Duplicate` issue | `prompts/duplicate-loop.md` |
| Discovery | 内部 handoff | `prompts/discovery-loop.md` |
| Repo Manager | 内部 handoff | `prompts/repo-manager.md` |
| Memory/Reconcile | 定期或内部 handoff | `prompts/memory-reconcile-loop.md` |
| Coordinator | 异常处理 | `prompts/coordinator-loop.md` |

状态 loop 只扫描自己负责的状态。服务 loop 不拥有常规可见状态。

## 记忆分层

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

`~/.linear-loop` 不保存默认 Discovery report、Todo brief 或完整 run JSON 历史。

## Loop 主流程

每个 scheduled state loop 自己闭环：

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
  append runtime issue records to ~/.linear-loop/runtime-issues/YYYY-MM.jsonl when needed
  optionally write a short Markdown Run Note for humans
```

compare 至少检查：

- issue id
- Linear state
- Linear `updatedAt`
- labels hash
- description/comment evidence hash
- local state version
- fingerprint
- active run id
- 存在时检查 lease 或 lock id

## Handoff

handoff 必须写到后续 loop 能读到的地方。不要只把交接信息放在 agent 最终消息里。

可用的持久 marker：

- Linear issue 里的简短评论或块，例如 `[Discovery Requested]`。
- `needs-access`、`needs-repo`、`blocked` 这类 label。
- `~/.linear-loop/state/issues/` 下的本地状态记录。
- `~/.linear-loop/state/locks/` 或 `~/.linear-loop/state/cooldowns/` 下的 lock、
  lease、cooldown 记录。

Backlog handoff 示例：

```md
[Discovery Requested]
Reason: Code-backed issue has a confirmed repo target but no fresh Discovery block.
Target: product-a-app
Freshness: issue fingerprint sha256:...
```

Coordinator 处理这些类型：

- `cas_conflict`
- `stale_run`
- `expired_lease`
- `unknown_state`
- `human_or_automation_drift`
- `multi_repo`
- `repo_or_lock_conflict`

## Linear Project Agent Settings

项目级配置放在 Linear Project 的 description，或一个名为 `Agent Project Settings`
的项目文档里。

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

Backlog 可以从 Project、Area label、issue template、linked PR 或历史相似 issue
推断 repo slug。Repo Manager 只能 clone 这里声明过的 origin。

## Discovery Gate

代码类 issue 的路径：

```text
Backlog
  -> records a Discovery handoff marker
  -> Discovery writes [Discovery] to the Linear issue
  -> Backlog or Todo proceeds when gates pass
```

不要只凭 issue 描述进入 `Todo`。Todo brief 也写回 Linear issue 的 `[Todo Brief]`。

## 经验记忆

loop 可以把候选经验写入 `~/.linear-loop/state/lesson-candidates.jsonl`。这只是暂存。

Memory/Reconcile 或 Coordinator 定期归并：

- 重复出现；
- 不绑定单个 issue；
- 可执行；
- 对未来 loop 或人类有用。

满足条件后写入 Linear Project Docs：

- `Agent Guidance`
- `Repo Notes/{repoSlug}`
- `Decision Log`

不满足条件就丢弃或继续保留为候选。不要把本地候选队列当长期知识库。

## Run Note

如果 agent host 需要一次可见的最终消息，用 Markdown：

```md
## Run Note
- Status: completed
- Issue: ABC-123
- Changed: added [Todo Brief], moved Todo -> In Progress
- Evidence: Linear issue comment
- Next: In Progress loop
```

Run Note 是给人看的。后续 loop 必须读取 Linear、GitHub、Project Docs 和
`~/.linear-loop`，不要依赖这条 note。

## 运行问题日志

loop 遇到系统本身的问题时，追加 runtime issue records，不要只写在评论里。

适合记录的情况：

- prompt 规则不清楚或缺失；
- 通用 loop 规则表达不了需要的动作；
- loop 没有执行必要的写前检查；
- Linear 配置缺失或不一致；
- Repo Manager 没有权限访问已声明的 origin；
- 缺少必要工具；
- 验证命令不稳定；
- Linear 出现当前 loop 没覆盖的状态；
- schedule 不能访问 `~/.linear-loop`。

loop 把每条记录作为一行 JSON 追加到
`~/.linear-loop/runtime-issues/YYYY-MM.jsonl`。Memory/Reconcile 定期归并这些记录，
把重复问题转成 prompt、loop 规则、loop runtime 或 Linear 设置的改动。

## 维护提示词

`prompts/` 里的文件就是用户复制层：Initial setup 手动运行一次，周期性 loops 粘到
schedules。

新增 loop 时，把 prompt 文件放进 `prompts/`，并在流程文档里说明它接入哪个状态或
handoff。
