# Linear Loop System

这是一套把 Linear issue 交给本地 agent loop 处理的工作流。

默认使用方式很直接：本地 agent 或 AG 平台能访问用户目录；运行态统一放在
`~/.linear-loop`；每个 schedule 粘贴一个 `dist/zh-CN/prompts/*.standalone.md`
里的自包含 prompt。

先看 [INSTALL.zh-CN.md](INSTALL.zh-CN.md)。

## 系统形态

```text
Linear
  -> 可见状态: Triage / Backlog / Todo / In Progress / In Review / Done
  -> 终态维护: Canceled / Duplicate
  -> 内部服务: Discovery / Repo Manager / Memory-Reconcile / Coordinator

~/.linear-loop
  -> memory / repos / worktrees / runtime issue logs
```

Linear 是用户看得见的协作界面。`~/.linear-loop` 是 agent 的本地运行空间。

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

repo origin、default branch、验证命令仍然写在 Linear Project 的
`Agent Project Settings`。本地目录只做运行缓存和证据记录，不重新引入 repo registry。

## 仓库维护者用什么

- [prompts/](prompts/) - 模块化源码 prompt。
- [schemas/loop-result.schema.json](schemas/loop-result.schema.json) - loop 输出结构。
- [scripts/build-standalone-prompts.py](scripts/build-standalone-prompts.py) - 生成复制包。
- [scripts/validate-copy-pack.py](scripts/validate-copy-pack.py) - 检查复制包。
- [scripts/validate-loop-schema.py](scripts/validate-loop-schema.py) - 检查 schema 和 fixtures。
- [docs/usage.zh-CN.md](docs/usage.zh-CN.md) - schedule、handoff、memory 和维护规则。

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
2. claim issue，记录当时看到的 Linear 和 `~/.linear-loop` 快照。
3. 运行对应 standalone prompt。
4. 输出 JSON。
5. 写入前重新读取 Linear 和本地 memory。
6. 只有 state、`updatedAt`、fingerprint、active run、lease/lock 都匹配时才写。
7. 不匹配就不要写，交给 Coordinator。

这条规则比 prompt 文案更重要。

## 不要这样做

- 不要让所有 loop 扫所有 issue。
- 不要让状态 loop 在快照过期后继续写 Linear。
- 不要让代码类 issue 在没有 Discovery report 时进入 `Todo`。
- 不要让 In Progress 在没有 Repo Manager write lock 时改代码。
- 不要让 Coordinator 负责日常状态推进。
- 不要把 prompt、schema、权限、Linear 设置或本地目录问题只写在评论里；用
  `runtimeIssues[]` 记录到 `~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl`。
