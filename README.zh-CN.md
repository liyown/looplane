# Looplane

把 Linear issue 交给一个本地 agent loop 持续推进。AG 平台只负责定时唤醒；
agent 自己读 Linear、GitHub、本地仓库和项目文档，自己判断下一步，自己执行并写回结果。

这更接近 loop 工程，而不是 prompt 工程：重点不是把流程切成很多 prompt，而是让一个
能工作的 loop 持续感知、行动、记录和修正。

## 先从这里开始

- [本地安装](INSTALL.zh-CN.md)：初始化本地运行空间并创建 schedule。
- [主循环提示词](prompts/agent-loop.md)：复制到定时任务里运行。
- [一次性初始化](prompts/initial-setup.md)：只手动运行一次。
- [维护循环](prompts/maintenance-loop.md)：可选，低频整理经验和运行问题。

## 使用方式

1. 初始化 `~/.linear-loop`。
2. 手动运行 `prompts/initial-setup.md`。
3. 创建一个 recurring schedule，粘贴 `prompts/agent-loop.md`。
4. 可选：创建每日或每周 schedule，粘贴 `prompts/maintenance-loop.md`。

用户不需要理解一堆内部 worker。主 loop 会自己完成 triage、理解代码、计划、实现、验证、
评论、状态更新和阻塞判断。

## 运行模型

```text
schedule wakes agent-loop
  -> scan Linear
  -> choose useful issues
  -> infer context from Linear / GitHub / Project docs / local repos
  -> act: clarify, plan, code, test, review, comment, move state
  -> write durable evidence
  -> remember lessons and runtime problems
```

Linear 状态只是信号，不是边界。agent 可以看一个 issue 当前在哪个状态，然后决定最有价值
的下一步。

## 什么时候问人

默认不问人，默认推进。只有这些情况才停下来：

- 缺少账号、密钥、仓库权限或工具权限。
- 会删除数据、破坏生产、部署到真实环境。
- 涉及安全、法律、支付、隐私或合规决策。
- 多个产品方向都合理，且选错成本高。
- 需求太模糊，无法做一个可逆的小步骤。

普通不确定性不应该阻塞：agent 应该做最小可逆动作，把假设写在 Linear 里，然后继续。

## 本地 Loop Space

默认目录：

```text
~/.linear-loop/config.yaml
~/.linear-loop/state/
~/.linear-loop/runtime-issues/YYYY-MM.jsonl
~/.linear-loop/repos/
~/.linear-loop/worktrees/
```

`~/.linear-loop` 只保存运行态、repo 缓存、worktree、临时记忆和运行问题。长期事实放在
Linear issue、Linear Project docs、GitHub 或代码仓库里。

## Prompt 文件

- [prompts/initial-setup.md](prompts/initial-setup.md)：一次性准备本地目录和 Linear
  项目文档。
- [prompts/agent-loop.md](prompts/agent-loop.md)：主循环，定时运行。
- [prompts/maintenance-loop.md](prompts/maintenance-loop.md)：可选，低频整理经验、
  runtime issues 和本地状态。

直接修改 prompt 文件即可，没有生成步骤。
