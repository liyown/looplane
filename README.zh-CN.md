# Linear Loop System

这是一套把 Linear issue 交给本地 agent loop 处理的工作流。

默认模型是 runnerless：AG 平台或本地 agent 平台只负责按 schedule 启动 prompt；
每个 loop 自己读写 Linear、GitHub、本地文件和 `~/.linear-loop`。没有独立业务
runner 去消费 JSON。

先看 [INSTALL.zh-CN.md](INSTALL.zh-CN.md)。

## 系统形态

```text
Linear issue
  -> 需求、Discovery、Todo Brief、执行摘要、验证结果

Linear Project Docs
  -> Agent Guidance / Repo Notes / Decision Log

~/.linear-loop
  -> state / locks / cooldowns / runtime issues / repos / worktrees

AG schedule
  -> 只负责启动对应 loop
```

Coordinator 不负责日常推进，只处理冲突、过期 run、未知状态、锁问题和
multi-repo 协调。

## 普通用户用什么

用户只需要这两个入口：

- [INSTALL.zh-CN.md](INSTALL.zh-CN.md) - 本地安装和启动。
- [dist/zh-CN/prompts/](dist/zh-CN/prompts/) - 复制到 schedules 的 standalone
  prompts。

不要把 `prompts/` 下的源码 prompt 直接粘到 schedule。源码 prompt 缺少嵌入式共享契约。

## 本地 Loop Space

默认目录固定为：

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

本地目录只保存运行控制状态、锁、冷却、runtime issues 和 repo/worktree 缓存。
不要把 Discovery report、Todo brief 或完整 run JSON 历史默认存到本地。

## 记忆放哪里

- Linear issue：单个 issue 的事实上下文，例如 `[Discovery]`、`[Todo Brief]`、
  执行摘要、验证结果、blocked 原因。
- Linear Project Docs：长期经验，例如 `Agent Guidance`、`Repo Notes/{repoSlug}`、
  `Decision Log`。
- `~/.linear-loop`：跨会话运行控制状态，例如 fingerprint、lock、cooldown、
  lesson candidates 和 runtime issues。

repo origin、default branch、验证命令仍然写在 Linear Project 的
`Agent Project Settings`。本地目录不重新引入 repo registry。

## 仓库维护者用什么

- [prompts/](prompts/) - 模块化源码 prompt。
- [schemas/loop-result.schema.json](schemas/loop-result.schema.json) - Loop Final
  Report 结构。
- [scripts/build-standalone-prompts.py](scripts/build-standalone-prompts.py) - 生成复制包。
- [scripts/validate-copy-pack.py](scripts/validate-copy-pack.py) - 检查复制包。
- [scripts/validate-loop-schema.py](scripts/validate-loop-schema.py) - 检查 schema 和 fixtures。
- [docs/usage.zh-CN.md](docs/usage.zh-CN.md) - schedule、handoff、state 和经验记忆规则。

修改 prompt 后运行：

```sh
python3 scripts/build-standalone-prompts.py
python3 scripts/build-standalone-prompts.py --check
python3 scripts/validate-copy-pack.py
python3 scripts/validate-loop-schema.py
```

## 核心写入规则

每个状态 loop 都必须：

1. 只扫描自己负责的 Linear 状态。
2. claim issue，记录当时看到的 Linear 和 `~/.linear-loop/state` 快照。
3. 自己执行允许的 Linear、GitHub、本地文件和本地 state 修改。
4. 写入前重新读取 Linear 和本地 state。
5. 只有 state、`updatedAt`、fingerprint、active run、lease/lock 都匹配时才写。
6. 不匹配就不要写，交给 Coordinator。
7. 最后输出 Loop Final Report，作为日志和异常归并依据，不作为第二套数据库。

## 不要这样做

- 不要让所有 loop 扫所有 issue。
- 不要让状态 loop 在快照过期后继续写 Linear。
- 不要让代码类 issue 在没有 `[Discovery]` 时进入 `Todo`。
- 不要让 In Progress 在没有 Repo Manager write lock 时改代码。
- 不要让 Coordinator 负责日常状态推进。
- 不要把业务证据藏进 `~/.linear-loop` 当长期事实库。
- 不要把 prompt、schema、权限、Linear 设置或本地目录问题只写在评论里；用
  `runtimeIssues[]` 记录到 `~/.linear-loop/runtime-issues/YYYY-MM.jsonl`。
