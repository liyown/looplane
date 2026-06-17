# Linear Loop System

这是一套基于 Linear 的本地 agent 工作流规范。

它不是运行器，也不绑定某个平台。这个仓库放的是 prompt、输出 schema、示例和运行规则。你可以把它接到 AG 平台、自动化平台，或者自己写一个很薄的 runner。

核心目标很窄：让多个状态 loop 分工处理 Linear issue，同时避免重复抢任务、旧结果覆盖新状态、没有仓库证据就进入开发。

## 系统形态

```text
Linear issues
  -> 状态 loop
     -> Triage / Backlog / Todo / In Progress / In Review / terminal loops
  -> 服务 loop
     -> Discovery / Repo Manager / Memory-Reconcile
  -> Coordinator
     -> 冲突、过期 run、未知状态、锁问题、multi-repo 协调
```

状态 loop 负责日常推进。Coordinator 只处理异常。

默认可见流程：

```text
Triage -> Backlog -> Todo -> In Progress -> In Review -> Done
Canceled / Duplicate
```

Discovery 默认不是 Linear 状态。代码类 issue 必须先有 fresh Discovery report，才能进入 `Todo`。

## 仓库内容

- [prompts/](prompts/) - 每个 loop 的 prompt。
- [schemas/loop-result.schema.json](schemas/loop-result.schema.json) - loop 输出 JSON 结构。
- [scripts/validate-loop-schema.py](scripts/validate-loop-schema.py) - 本地协议校验脚本。
- [tests/fixtures/loop-results/](tests/fixtures/loop-results/) - 正反例输出。
- [docs/linear-loop-system-spec.md](docs/linear-loop-system-spec.md) - 完整设计。
- [docs/workflow-simulation-and-edge-cases.md](docs/workflow-simulation-and-edge-cases.md) - 正常路径和边界场景。
- [docs/usage.zh-CN.md](docs/usage.zh-CN.md) - 中文使用方式。

## 写入规则

每个状态 loop 都必须按同一套规则写 Linear：

1. 只扫描自己负责的 Linear 状态。
2. claim 一个 issue，创建或复用 run reservation。
3. 记录 claim 时看到的 Linear 和 memory 快照。
4. 运行对应 prompt。
5. 校验 JSON 输出。
6. 写入前重新读取 Linear 和 memory。
7. 只有 state、`updatedAt`、fingerprint、active run、相关 lease/lock 都匹配时才写。
8. 不匹配就不要写，交给 Coordinator。

这条规则比 prompt 本身更重要。不要让 loop 做“差不多还能写”的更新。

## 最小运行条件

接入平台或 runner 至少需要：

- Linear issue、comment、label、project、status 的读写能力。
- 一个持久化 memory，用来存 fingerprint、run、Discovery report、lock 和 cooldown。
- Linear Project 里的 `Agent Project Settings`，保存 repo origin、default branch 和验证命令。
- 按 loop role 运行 prompt，并校验 JSON 输出。
- Repo Manager 能执行 clone、fetch、worktree、read lease、write lock、baseline 和 verification。

Agent 不能自己猜 clone URL。repo origin 只能来自 Linear Project 的 `Agent Project Settings`。

## 快速启动

1. 先运行 [prompts/initial-loop.md](prompts/initial-loop.md)，让它初始化 Linear workflow、labels、project settings、memory 目录和 healthcheck issue。
2. 在每个受管 Linear Project 填好 `Agent Project Settings`。
3. 把 [schemas/loop-result.schema.json](schemas/loop-result.schema.json) 接到 runner 的输出校验。
4. 给每个可见状态配置一个 schedule：

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

5. 配置服务 loop：

   ```text
   Discovery        -> prompts/discovery-loop.md
   Repo Manager     -> prompts/repo-manager.md
   Memory/Reconcile -> prompts/memory-reconcile-loop.md
   Coordinator      -> prompts/coordinator-loop.md
   ```

6. 让 runner 执行写前 compare-and-set 检查。
7. 把 `requestedWorker` 路由到对应服务 loop。
8. 把 `escalation.target: "coordinator"` 路由到 Coordinator。

更细的接入说明看 [docs/usage.zh-CN.md](docs/usage.zh-CN.md)。

## 校验

修改 schema、prompt 或 fixture 后运行：

```sh
python3 scripts/validate-loop-schema.py
```

预期输出：

```text
validated schema shape and 4 fixtures
```

## 不要这样做

- 不要让所有 loop 扫所有 issue。
- 不要让状态 loop 在快照过期后继续写 Linear。
- 不要让代码类 issue 在没有 Discovery report 时进入 `Todo`。
- 不要让实现 loop 在没有 Repo Manager write lock 时改代码。
- 不要让 Coordinator 负责日常状态推进。
