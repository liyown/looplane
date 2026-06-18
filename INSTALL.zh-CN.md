# 本地安装

这套系统默认跑在本地。AG 平台里的 schedule 只负责启动 loop；loop 自己操作
Linear、GitHub、本地文件和 `~/.linear-loop`，并在写入前完成自己的状态检查。

## 1. 初始化本地 Loop Space

```sh
mkdir -p ~/.linear-loop/state/{issues,locks,cooldowns}
mkdir -p ~/.linear-loop/runtime-issues
mkdir -p ~/.linear-loop/{repos,worktrees}
touch ~/.linear-loop/state/lesson-candidates.jsonl
```

创建 `~/.linear-loop/config.yaml`：

```yaml
agent:
  version: 1
  loopSpace: ~/.linear-loop
  linear:
    workspace: null
```

如果你的 schedule 运行在云端容器，不能访问这个目录，那就不是默认安装方式。先不要启动
loop。

## 2. 复制 prompts 到运行入口

使用 [prompts/](prompts/) 里的文件。每个 loop prompt 都是自包含 prompt，已经包含
自己的职责、loop 规则、Markdown run note 约定、runtime issue 日志格式和
`~/.linear-loop` 目录规则。

| 运行方式 | 粘贴的 prompt |
| --- | --- |
| Initial setup，一次性手动运行 | `prompts/initial-setup.md` |
| Triage | `prompts/triage-loop.md` |
| Backlog | `prompts/backlog-loop.md` |
| Todo | `prompts/todo-loop.md` |
| In Progress | `prompts/in-progress-loop.md` |
| In Review | `prompts/in-review-loop.md` |
| Done | `prompts/done-loop.md` |
| Canceled | `prompts/canceled-loop.md` |
| Duplicate | `prompts/duplicate-loop.md` |
| Discovery，内部 handoff | `prompts/discovery-loop.md` |
| Repo Manager，内部 handoff | `prompts/repo-manager.md` |
| Memory/Reconcile，定期或内部 handoff | `prompts/memory-reconcile-loop.md` |
| Coordinator，异常处理 | `prompts/coordinator-loop.md` |

状态 loop 按 Linear 状态分开跑。不要让每个 schedule 扫所有 issue。

## 3. 运行 Initial setup prompt

先手动运行 `prompts/initial-setup.md`。它负责检查或创建：

- Linear workflow states。
- labels 和控制标签。
- 每个受管 Linear Project 的 `Agent Project Settings`。
- Linear Project docs：`Agent Guidance`、`Decision Log`、需要时的 `Repo Notes/{repoSlug}`。
- `~/.linear-loop` 最小运行目录。
- no-code healthcheck issue。

如果 Linear API 不能完成某项设置，Initial setup 必须返回明确的人工步骤，并在
Markdown 结果里标记 `Requires human: true`。

## 记忆约定

- Discovery report 写到 Linear issue 的 `[Discovery]` 块或结构化评论。
- Todo brief 写到 Linear issue 的 `[Todo Brief]` 块或结构化评论。
- 执行摘要、验证结果、blocked 原因写到 Linear issue。
- 长期经验写到 Linear Project Docs。
- `~/.linear-loop` 只存 fingerprint、lock、cooldown、lesson candidates、
  runtime issues、repo cache 和 worktrees。

## 必须保留的运行规则

- 每个 loop 自己执行允许的 Linear、GitHub、本地文件和 local state 修改。
- 写 Linear 前必须重读 Linear 和 `~/.linear-loop/state`。
- observed snapshot 不匹配就不写，交给 Coordinator。
- 代码类 issue 进入 `Todo` 前必须有 fresh `[Discovery]`。
- In Progress 改代码前必须拿到 Repo Manager write lock。
- Repo Manager 只能 clone Linear Project `Agent Project Settings` 声明过的 origin。
- 运行时发现系统问题时，直接追加 runtime issue record 到
  `~/.linear-loop/runtime-issues/YYYY-MM.jsonl`。

## 修改提示词

直接修改 [prompts/](prompts/) 里的文件，不需要额外工具。
