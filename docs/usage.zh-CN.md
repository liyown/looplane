# 使用方式

这份文档说明怎么把这些 prompt 接到自动化平台或自定义 runner。

## 角色

| 角色 | 运行对象 | 是否写常规状态迁移 | 职责 |
| --- | --- | --- | --- |
| Triage | `Triage` issue | 是 | 接收、取消或标记重复。 |
| Backlog | `Backlog` issue | 是 | 收敛范围、解析 target、需要时请求 Discovery。 |
| Discovery | 内部 handoff | 默认不写可见状态 | 只读仓库，产出 Discovery report。 |
| Todo | `Todo` issue | 是 | 基于证据生成 execution brief。 |
| In Progress | `In Progress` issue | 是 | 在加锁 worktree 中实现。 |
| In Review | `In Review` issue | 是 | 验证结果，进入 Done 或退回。 |
| Done | `Done` issue | 通常不写 | 整理最终记录。 |
| Canceled | `Canceled` issue | 否 | 保持终态稳定。 |
| Duplicate | `Duplicate` issue | 否 | 保留 canonical link 和说明。 |
| Memory/Reconcile | 内部 handoff 或 schedule | 否 | 标记 stale run、expired run、cooldown 和 drift。 |
| Repo Manager | 内部 handoff | 不写 Linear 状态 | 管 clone、fetch、worktree、lease、lock 和验证命令。 |
| Coordinator | 内部 handoff 或 schedule | 只做异常 reroute | 处理 CAS 冲突、未知状态、重复 run、multi-repo 协调。 |

## Runner 主循环

每个 scheduled state loop 按这个流程跑：

```text
list issues in owned Linear state
for each candidate:
  load issue memory
  compute fingerprint
  skip unchanged blocked/no-op issues until nextEligibleAt
  create or reuse run reservation
  build context
  run the matching prompt
  validate JSON against schemas/loop-result.schema.json
  re-read Linear and memory
  compare observed snapshot with current state
  apply allowed changes only if the snapshot still matches
  otherwise mark stale/no-op and escalate when needed
  append runtimeIssues[] to memory/runtime-issues/YYYY-MM.jsonl
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

## 初始化 Linear

先运行 [prompts/initial-loop.md](../prompts/initial-loop.md)。

Initial loop 要做这些事：

- 检查或创建默认 workflow。
- 检查或创建 label 组和控制 label。
- 在每个受管 Linear Project 上创建或检查 `Agent Project Settings`。
- 创建或检查 memory 存储位置。
- 创建一个 no-code healthcheck issue。
- 如果 API 不能完成某些 Linear UI 配置，返回明确的人工步骤。

默认可见 workflow：

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
Canceled / Duplicate
```

## 启动系统

Initial loop 完成后：

1. 确认每个受管 Linear Project 都有 `Agent Project Settings`。
2. 启动每个可见状态的 schedule：

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

3. 配置服务 loop 的 handoff：

   ```text
   Discovery        -> prompts/discovery-loop.md
   Repo Manager     -> prompts/repo-manager.md
   Memory/Reconcile -> prompts/memory-reconcile-loop.md
   Coordinator      -> prompts/coordinator-loop.md
   ```

4. 在 runner 中强制写前检查：loop 写 Linear 前必须重读 Linear 和 memory，并确认 observed snapshot 仍然匹配。
5. 把 `requestedWorker` 路由到对应服务 loop。
6. 把 `escalation.target: "coordinator"` 路由到 Coordinator。

## Linear Project Agent Settings

项目级配置放在 Linear Project 的 description，或放在一个名为 `Agent Project Settings` 的项目文档里。

使用 fenced YAML，方便 runner 解析：

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
    product-a-api:
      origin: git@github.com:org/product-a-api.git
      defaultBranch: main
      verify:
        test: pnpm test
  componentMap:
    Area/Frontend:
      kind: code
      repo: product-a-app
      confidence: high
    Area/API:
      kind: code
      repo: product-a-api
      confidence: high
```

Backlog loop 可以从 Project、Area label、issue template、linked PR 或历史相似 issue 推断 repo slug。Repo Manager 只能 clone `Agent Project Settings` 中声明过的 origin。

## Memory

Memory 是运行态，不进 git。

建议路径：

```text
memory/issues/{issueId}.json
memory/discovery/{issueId}.json
memory/repos/{repoSlug}.json
memory/projects/{projectSlug}.json
memory/runs/{runId}.json
memory/runtime-issues/{YYYY-MM}.jsonl
```

如果平台没有文件系统，就用数据库或 KV 存同样的数据。

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
- Linear 出现当前 loop 没覆盖的状态。

runner 把每条记录追加到 `memory/runtime-issues/YYYY-MM.jsonl`。记录里应包含
loop、issue id、run id、时间戳和 loop 输出的 runtime issue 对象。Coordinator 或
Memory/Reconcile 定期归并这些记录，把重复问题转成 prompt、schema、runner 或
Linear 设置的改动。

## Discovery Gate

代码类 issue 的路径：

```text
Backlog
  -> requestedWorker: discovery
  -> Discovery report
  -> Backlog applies Todo when gates pass
```

不要只凭 issue 描述进入 `Todo`。

## 校验

运行：

```sh
python3 scripts/validate-loop-schema.py
```

它检查：

- schema 暴露 `requestedWorker`
- schema 使用 `escalation`，不使用旧的中心化 action 字段
- Discovery 和 Todo 的证据字段是必填
- fixtures 覆盖普通 handoff、无效 Discovery report、有效 execution brief 和 CAS conflict escalation

## 新增 loop

新增 loop 前先判断它属于哪类：

- 可见状态 loop：只扫描并推进一个 Linear 状态。
- 服务 loop：从 handoff 取活，不拥有可见状态。
- Coordinator case：只处理异常，不参与日常推进。

需要同步更新：

- `prompts/` 下的 prompt
- spec 里的允许迁移
- schema，只有现有 contract 表达不了时才改
- schema 行为变化时至少补一个 fixture
