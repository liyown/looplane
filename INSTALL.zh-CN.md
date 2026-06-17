# 本地安装

这套系统默认跑在本地。AG 平台里的 schedule 执行 prompt 时，必须能访问用户目录
`~/.linear-loop`。

## 1. 初始化本地 Loop Space

```sh
mkdir -p ~/.linear-loop/memory/{issues,discovery,repos,projects,decisions,runs,runtime-issues}
mkdir -p ~/.linear-loop/{repos,worktrees}
```

创建 `~/.linear-loop/config.yaml`：

```yaml
agent:
  version: 1
  loopSpace: ~/.linear-loop
  linear:
    workspace: null
  schedules:
    copyPack: dist/zh-CN/prompts
```

如果你的 schedule 运行在云端容器，不能访问这个目录，那就不是默认安装方式。先不要启动
loop。

## 2. 复制 standalone prompts 到 schedules

使用 [dist/zh-CN/prompts/](dist/zh-CN/prompts/) 里的文件。每个文件都是自包含
prompt，已经嵌入共享契约、输出 JSON 结构和 `~/.linear-loop` 目录规则。

| schedule | 粘贴的 prompt |
| --- | --- |
| Initial，手动运行一次 | `dist/zh-CN/prompts/initial-loop.standalone.md` |
| Triage | `dist/zh-CN/prompts/triage-loop.standalone.md` |
| Backlog | `dist/zh-CN/prompts/backlog-loop.standalone.md` |
| Todo | `dist/zh-CN/prompts/todo-loop.standalone.md` |
| In Progress | `dist/zh-CN/prompts/in-progress-loop.standalone.md` |
| In Review | `dist/zh-CN/prompts/in-review-loop.standalone.md` |
| Done | `dist/zh-CN/prompts/done-loop.standalone.md` |
| Canceled | `dist/zh-CN/prompts/canceled-loop.standalone.md` |
| Duplicate | `dist/zh-CN/prompts/duplicate-loop.standalone.md` |
| Discovery，内部 handoff | `dist/zh-CN/prompts/discovery-loop.standalone.md` |
| Repo Manager，内部 handoff | `dist/zh-CN/prompts/repo-manager.standalone.md` |
| Memory/Reconcile，定期或内部 handoff | `dist/zh-CN/prompts/memory-reconcile-loop.standalone.md` |
| Coordinator，异常处理 | `dist/zh-CN/prompts/coordinator-loop.standalone.md` |

状态 loop 按 Linear 状态分开跑。不要让每个 schedule 扫所有 issue。

## 3. 运行 Initial prompt

先手动运行 `initial-loop.standalone.md`。它负责检查或创建：

- Linear workflow states。
- labels 和控制标签。
- 每个受管 Linear Project 的 `Agent Project Settings`。
- `~/.linear-loop` 目录结构。
- no-code healthcheck issue。

如果 Linear API 不能完成某项设置，Initial 必须返回明确的人工步骤，并设置
`requiresHuman: true`。

## 必须保留的运行规则

- 写 Linear 前必须重读 Linear 和 `~/.linear-loop` memory。
- observed snapshot 不匹配就不写，交给 Coordinator。
- 代码类 issue 进入 `Todo` 前必须有 fresh Discovery report。
- In Progress 改代码前必须拿到 Repo Manager write lock。
- Repo Manager 只能 clone Linear Project `Agent Project Settings` 声明过的 origin。
- 运行时发现系统问题时，输出 `runtimeIssues[]`，并追加到
  `~/.linear-loop/memory/runtime-issues/YYYY-MM.jsonl`。

## 维护复制包

改了 `prompts/` 或共享契约后，重新生成：

```sh
python3 scripts/build-standalone-prompts.py
python3 scripts/build-standalone-prompts.py --check
python3 scripts/validate-copy-pack.py
python3 scripts/validate-loop-schema.py
```
