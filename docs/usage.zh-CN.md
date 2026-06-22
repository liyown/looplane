# 使用方式

Looplane 的默认模型只有一个主循环：`agent-loop.md`。它定时醒来，自己扫描 Linear，
自己决定处理哪个 issue，自己完成下一步。

## Prompt

| 用途 | prompt |
| --- | --- |
| 一次性初始化 | `prompts/initial-setup.md` |
| 主 schedule | `prompts/agent-loop.md` |
| 可选维护 schedule | `prompts/maintenance-loop.md` |

## 主循环做什么

```text
读取 Linear / GitHub / Project docs / ~/.linear-loop
选择有价值的 issue
判断下一步
执行：澄清、计划、读代码、改代码、验证、评论、移动状态
写回持久证据
记录运行问题和经验
```

主 loop 不要求 issue 必须先经过单独的预分析或计划 worker。需要理解代码时，它自己读；
需要计划时，它自己写；能实现时，它自己创建 worktree、改代码、运行验证。

## Linear 状态

状态只是信号，不是边界。主 loop 可以根据当前 issue 的实际情况做判断：

- 新 issue：接受、补充标签、关闭、标记重复或询问必要信息。
- 需求清楚：补充验收标准，进入可执行状态。
- 代码任务：查 repo、读代码、制定方案、实现、验证。
- 已实现：写验证结果，进入 review 或 done。
- 真正卡住：写清楚 blocker 和需要的人类动作。

如果 Linear 的状态名不是 `Backlog / In Progress / In Review / Done` 这套，也没关系。
agent 使用最接近的状态，并在必要时解释一次。

## 什么时候问人

不要因为信息不完美就问人。默认做最小可逆动作。

需要人工确认的情况：

- 缺少账号、密钥、仓库权限或工具权限。
- 会删除数据、破坏生产、部署到真实环境。
- 涉及安全、法律、支付、隐私或合规。
- 多个产品方向都合理，且选错成本高。
- 需求太模糊，无法做一个小的可逆步骤。

其他情况，agent 应该写下假设并继续。

## 记忆分层

```text
Linear issue
  task facts
  decisions
  progress notes
  verification result
  blocker reason

Linear Project docs
  Agent Guidance
  Agent Project Settings
  Repo Notes/{repoSlug}
  Decision Log

~/.linear-loop
  state/
  runtime-issues/YYYY-MM.jsonl
  repos/
  worktrees/
```

本地目录不是第二套项目数据库。能给人和后续 agent 看的东西，优先写到 Linear 或 GitHub。

## Runtime Issues

agent 遇到系统本身的问题时，追加到：

```text
~/.linear-loop/runtime-issues/YYYY-MM.jsonl
```

适合记录：

- prompt 规则不清楚；
- Linear 设置不够用；
- repo origin 或验证命令缺失；
- 工具或权限缺失；
- 某类任务反复卡住；
- 某个判断经常出错。

维护 loop 会定期把重复问题整理成 Project docs 或 prompt 改进建议。
