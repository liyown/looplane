# 本地安装

Looplane 默认跑在本地。AG 平台里的 schedule 只负责定时唤醒 agent；真正的判断和执行
由 `prompts/agent-loop.md` 完成。

## 1. 初始化本地 Loop Space

```sh
mkdir -p ~/.linear-loop/{state,runtime-issues,repos,worktrees}
```

创建 `~/.linear-loop/config.yaml`：

```yaml
agent:
  version: 1
  loopSpace: ~/.linear-loop
  linear:
    workspace: null
```

如果你的 schedule 运行在不能访问本机 home 目录的云端容器里，这不是默认安装方式。先
不要启动 loop。

## 2. 一次性运行 Initial Setup

把 [prompts/initial-setup.md](prompts/initial-setup.md) 复制到 agent 里手动运行一次。
它会准备：

- `~/.linear-loop` 目录。
- Linear Project docs：`Agent Guidance`、`Agent Project Settings`、`Repo Notes/*`、
  `Decision Log`。
- 少量必要标签，例如 `needs-info`、`needs-access`、`blocked`。
- 一个 no-code healthcheck issue，如果当前工具权限允许。

Initial setup 不需要做成 schedule。

## 3. 创建主 Schedule

创建一个 recurring schedule，粘贴：

```text
prompts/agent-loop.md
```

建议频率从 10-30 分钟一次开始。主 loop 会自己扫描 Linear，选择有价值的 issue，然后
完成 triage、理解、计划、实现、验证、评论和状态更新。

## 4. 可选：创建维护 Schedule

如果想让系统定期整理经验和运行问题，创建一个低频 schedule，粘贴：

```text
prompts/maintenance-loop.md
```

建议每天或每周一次。它只整理 runtime issues、lesson candidates、Project docs 和本地
状态，不负责日常产品任务。

## 记忆和证据放哪里

- Issue 相关事实、执行摘要、验证结果、阻塞原因：写到 Linear issue。
- 长期经验和项目偏好：写到 Linear Project docs。
- repo 缓存、worktree、临时状态、runtime issue log：写到 `~/.linear-loop`。

## 人工确认边界

默认让 agent 推进。只有权限、破坏性操作、生产部署、安全/法律/支付/隐私/合规、或者高
成本产品方向选择，才需要人工确认。

普通不确定性不应该停止 loop。agent 应该做最小可逆动作，并把假设写在 Linear 里。
