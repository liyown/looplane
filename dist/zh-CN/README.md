# 复制包

这个目录是给用户复制到 AG 平台运行入口的材料。Initial setup 是一次性手动运行；
其它状态 loop 才放进 schedules。

只复制 `prompts/*.standalone.md`。不要复制仓库源码里的 `prompts/*.md`。

| 运行方式 | prompt |
| --- | --- |
| Initial setup | `prompts/initial-setup.standalone.md` |
| Triage | `prompts/triage-loop.standalone.md` |
| Backlog | `prompts/backlog-loop.standalone.md` |
| Todo | `prompts/todo-loop.standalone.md` |
| In Progress | `prompts/in-progress-loop.standalone.md` |
| In Review | `prompts/in-review-loop.standalone.md` |
| Done | `prompts/done-loop.standalone.md` |
| Canceled | `prompts/canceled-loop.standalone.md` |
| Duplicate | `prompts/duplicate-loop.standalone.md` |
| Discovery | `prompts/discovery-loop.standalone.md` |
| Repo Manager | `prompts/repo-manager.standalone.md` |
| Memory/Reconcile | `prompts/memory-reconcile-loop.standalone.md` |
| Coordinator | `prompts/coordinator-loop.standalone.md` |

运行态默认在 `~/.linear-loop`，不是这个仓库目录。
