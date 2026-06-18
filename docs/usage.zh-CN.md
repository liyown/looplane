# 使用方式

这份文档补充 [INSTALL.zh-CN.md](../INSTALL.zh-CN.md)。默认模型是 loop-first：
schedule 只启动 loop，loop 自己读写 Linear、GitHub、本地文件和
`~/.linear-loop`，并在写入前完成自己的状态检查。

## 运行角色

| 角色 | 运行对象 | prompt |
| --- | --- | --- |
| Initial setup | 一次性手动运行 | `dist/zh-CN/prompts/initial-setup.standalone.md` |
| Triage | `Triage` issue | `dist/zh-CN/prompts/triage-loop.standalone.md` |
| Backlog | `Backlog` issue | `dist/zh-CN/prompts/backlog-loop.standalone.md` |
| Todo | `Todo` issue | `dist/zh-CN/prompts/todo-loop.standalone.md` |
| In Progress | `In Progress` issue | `dist/zh-CN/prompts/in-progress-loop.standalone.md` |
| In Review | `In Review` issue | `dist/zh-CN/prompts/in-review-loop.standalone.md` |
| Done | `Done` issue | `dist/zh-CN/prompts/done-loop.standalone.md` |
| Canceled | `Canceled` issue | `dist/zh-CN/prompts/canceled-loop.standalone.md` |
| Duplicate | `Duplicate` issue | `dist/zh-CN/prompts/duplicate-loop.standalone.md` |
| Discovery | 内部 handoff | `dist/zh-CN/prompts/discovery-loop.standalone.md` |
| Repo Manager | 内部 handoff | `dist/zh-CN/prompts/repo-manager.standalone.md` |
| Memory/Reconcile | 定期或内部 handoff | `dist/zh-CN/prompts/memory-reconcile-loop.standalone.md` |
| Coordinator | 异常处理 | `dist/zh-CN/prompts/coordinator-loop.standalone.md` |

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
  append runtimeIssues[] to ~/.linear-loop/runtime-issues/YYYY-MM.jsonl when present
  return Loop Final Report for logs and exception rollups
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

普通内部交接用 `requestedWorker` 表示“本 loop 已标记或创建后续工作”：

```json
{
  "nextState": "Backlog",
  "requestedWorker": "discovery"
}
```

阻塞或异常交接用 `escalation`：

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
  -> requestedWorker: discovery
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

## 运行问题日志

loop 遇到系统本身的问题时，用 `runtimeIssues[]` 记录，不要只写在评论里。

适合记录的情况：

- prompt 规则不清楚或缺失；
- schema 表达不了需要的结果；
- loop 没有执行必要的写前检查；
- Linear 配置缺失或不一致；
- Repo Manager 没有权限访问已声明的 origin；
- 缺少必要工具；
- 验证命令不稳定；
- Linear 出现当前 loop 没覆盖的状态；
- schedule 不能访问 `~/.linear-loop`。

loop 把每条记录追加到 `~/.linear-loop/runtime-issues/YYYY-MM.jsonl`。
Memory/Reconcile 定期归并这些记录，把重复问题转成 prompt、schema、loop runtime
或 Linear 设置的改动。

## 维护复制包

`prompts/` 是源码层，`dist/zh-CN/prompts/` 是用户复制层：Initial setup 手动运行一次，
周期性 loops 才粘到 schedules。改源码后运行：

```sh
python3 scripts/build-standalone-prompts.py
python3 scripts/build-standalone-prompts.py --check
python3 scripts/validate-copy-pack.py
python3 scripts/validate-loop-schema.py
```

新增 loop 时同步更新：

- `prompts/` 下的源码 prompt。
- `scripts/build-standalone-prompts.py` 的 prompt 列表。
- `scripts/validate-copy-pack.py` 的 expected prompt 列表。
- 需要时更新 schema 和 fixtures。
