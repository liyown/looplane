# Looplane

把 Linear issue 交给一组本地 agent loop 持续处理。Looplane 维护 prompt 文件、
运行文档和 examples；真正的运行界面仍然是 Linear。

它更接近最近很火的 loop 工程，而不是传统 prompt 工程。重点不是写一段漂亮
prompt，而是把状态、证据、记忆、迁移、冲突处理和周期性执行组织成能长期运转的
闭环。

![Looplane overview](docs/assets/loop-system-overview.svg)

## 先从这里开始

- [本地安装](INSTALL.zh-CN.md)：三步启动。
- [Prompts](prompts/)：一次性初始化 prompt 和 schedules 用的 loop prompts。
- [使用细则](docs/usage.zh-CN.md)：状态、handoff、记忆和异常处理规则。

`prompts/` 下的文件就是复制到 agent runtime 的提示词。每个 loop prompt 都包含
自己的职责、目录约定、handoff 规则、Markdown run note 约定和 runtime issue 日志格式。

## 它解决什么

单个 agent 很容易把“现在该做什么”“之前学到了什么”“谁可以改代码”“状态能不能迁移”
混在一起。这个系统把它们拆开：

- Linear issue 保存单个任务的事实、证据和执行记录。
- Linear Project Docs 保存长期经验和项目偏好。
- `~/.linear-loop` 保存最小运行态、锁、冷却和本地 repo/worktree 缓存。
- schedule 只负责定时启动对应 loop。
- Coordinator 只处理冲突、未知状态、过期 run、锁问题和 multi-repo 协调。

## 三步启动

1. 初始化本地 Loop Space：

   ```sh
   mkdir -p ~/.linear-loop/state/{issues,locks,cooldowns}
   mkdir -p ~/.linear-loop/runtime-issues
   mkdir -p ~/.linear-loop/{repos,worktrees}
   touch ~/.linear-loop/state/lesson-candidates.jsonl
   ```

2. 把 [prompts/](prompts/) 里的 prompt 文件放到对应运行入口：
   `prompts/initial-setup.md` 手动运行一次，其它 loop prompt 粘到 AG 平台对应
   schedule。

3. 手动运行 `prompts/initial-setup.md`。它会检查本地目录、Linear workflow
   states、labels、Project `Agent Project Settings` 和 Project Docs，并告诉你
   还需要创建哪些 schedules。

完整步骤见 [INSTALL.zh-CN.md](INSTALL.zh-CN.md)。


## loop 怎么协作

```text
Triage
  -> Backlog
      -> Discovery writes [Discovery]
      -> Todo writes [Todo Brief]
      -> In Progress asks Repo Manager for code lock
      -> In Review
      -> Done

Canceled / Duplicate
  -> close or archive with evidence

Memory/Reconcile
  -> merge repeated lessons into Project Docs

Coordinator
  -> resolve conflicts, stale runs, unknown states, lock problems
```

每个状态 loop 只扫描自己负责的 Linear 状态。它自己读 Linear、GitHub、本地文件和
`~/.linear-loop`，自己做写前重读和冲突判断，自己写回允许的结果。

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

repo origin、default branch、验证命令写在 Linear Project 的 `Agent Project Settings`。
本地目录不重新引入 repo registry。

## 核心写入规则

每个状态 loop 都必须：

1. 只扫描自己负责的 Linear 状态。
2. claim issue，并记录当时看到的 Linear 和 `~/.linear-loop/state` 快照。
3. 执行自己允许的 Linear、GitHub、本地文件和 local state 修改。
4. 写入前重新读取 Linear 和本地 state。
5. 只有 state、`updatedAt`、fingerprint、active run、lease/lock 都匹配时才写。
6. 不匹配就不要写，交给 Coordinator。
7. 持久事实写到 Linear、GitHub、Project Docs 或 `~/.linear-loop`；如果需要一次运行摘要，
   用简短 Markdown `Run Note`。

## Prompt 文件

- [prompts/initial-setup.md](prompts/initial-setup.md)：手动运行一次，准备 Linear、
  Project Docs 和 `~/.linear-loop`。
- `*-loop.md`：状态 loop 或服务 loop，按 schedule 运行。
- [prompts/repo-manager.md](prompts/repo-manager.md)：负责 clone、fetch、worktree 和
  repo lock。

直接修改这些 prompt 文件即可，没有生成步骤。

## 不要这样做

- 不要让所有 loop 扫所有 issue。
- 不要让状态 loop 在快照过期后继续写 Linear。
- 不要让代码类 issue 在没有 `[Discovery]` 时进入 `Todo`。
- 不要让 In Progress 在没有 Repo Manager write lock 时改代码。
- 不要让 Coordinator 负责日常状态推进。
- 不要把业务证据藏进 `~/.linear-loop` 当长期事实库。
- 不要把 prompt、权限、Linear 设置或本地目录问题只写在评论里；追加 runtime issue
  records 到 `~/.linear-loop/runtime-issues/YYYY-MM.jsonl`。
