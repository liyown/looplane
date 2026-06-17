# 使用方式

这份文档补充 [INSTALL.zh-CN.md](../INSTALL.zh-CN.md)。默认模型是本地运行：
schedule 执行 prompt 时可以访问 `~/.linear-loop`。

## 运行角色

| 角色 | 运行对象 | prompt |
| --- | --- | --- |
| Initial | 手动运行一次 | `dist/zh-CN/prompts/initial-loop.standalone.md` |
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

## 本地 Loop Space

运行态固定在：

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

`memory` 记录 fingerprint、run reservation、Discovery report、lease、lock、
cooldown 和运行故障。`repos` 和 `worktrees` 由 Repo Manager 管。

## Runner 主循环

每个 scheduled state loop 按这个流程跑：

```text
list issues in the owned Linear state
for each candidate:
  load issue memory from ~/.linear-loop
  compute fingerprint
  skip unchanged blocked/no-op issues until nextEligibleAt
  create or reuse run reservation
  build context
  run the matching standalone prompt
  require JSON output
  re-read Linear and ~/.linear-loop memory
  compare observed snapshot with current state
  apply allowed changes only if the snapshot still matches
  otherwise mark stale/no-op and escalate when needed
  append runtimeIssues[] to ~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl
```

compare 至少检查：

- issue id
- Linear state
- Linear `updatedAt`
- labels hash
- description hash
- memory version
- fingerprint
- active run id
- 存在时检查 lease 或 lock id

## Handoff

普通内部交接用 `requestedWorker`：

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
  -> Discovery report in ~/.linear-loop/memory/discovery/
  -> Backlog applies Todo when gates pass
```

不要只凭 issue 描述进入 `Todo`。

## 运行问题日志

loop 遇到系统本身的问题时，用 `runtimeIssues[]` 记录，不要只写在评论里。

适合记录的情况：

- prompt 规则不清楚或缺失；
- schema 表达不了需要的结果；
- runner 没有执行必要的写前检查；
- Linear 配置缺失或不一致；
- Repo Manager 没有权限访问已声明的 origin；
- 缺少必要工具；
- 验证命令不稳定；
- Linear 出现当前 loop 没覆盖的状态；
- schedule 不能访问 `~/.linear-loop`。

runner 把每条记录追加到
`~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl`。Memory/Reconcile 定期归并这些
记录，把重复问题转成 prompt、schema、runner 或 Linear 设置的改动。

## 维护复制包

`prompts/` 是源码层，`dist/zh-CN/prompts/` 是用户复制层。改源码后运行：

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
