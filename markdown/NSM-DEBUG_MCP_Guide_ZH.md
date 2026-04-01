# NSM-DEBUG_MCP 使用教程

## 说明

NSM-DEBUG_MCP 基于 MCP2Serial 做了定向改造。

本仓库的大部分重构、真机适配、VS Code 集成和文档整理工作，由 GPT-5.4 协助完成。

如果有任何内容涉及侵权，请直接联系维护者删除。

## 这个项目现在是什么

NSM-DEBUG_MCP 是一个面向 Windows 和 VS Code 的串口网络设备管理 MCP。

它现在只做三件事：

1. 连接真实串口控制台设备。
2. 自动完成用户名、密码和特权模式进入。
3. 把设备 CLI 命令暴露成 VS Code 里的 MCP 工具。

这个版本只保留源码直跑这一个最短路径。

## 当前仓库结构

现在保留的核心内容是：

- `.vscode/mcp.json`
- `src/nsm_debug_mcp/`
- `NSM-DEBUG_MCP_R1.example.yaml`
- `NSM-DEBUG_MCP_R2.example.yaml`
- `markdown/NSM-DEBUG_MCP_Guide_EN.md`
- `markdown/NSM-DEBUG_MCP_Guide_ZH.md`

含义很直接：

- `.vscode/mcp.json` 负责让 VS Code 直接启动 MCP。
- `src/nsm_debug_mcp/` 是实际 MCP 服务端代码。
- 两个 `.example.yaml` 是已经验证过的设备示例配置。

## 已验证环境

实现和联调时实际验证过的环境如下：

- Windows
- Python 3.14
- VS Code
- GitHub Copilot Chat + Agent 模式
- CH340 串口芯片
- `COM3`
- `9600 8N1 XON/XOFF`
- Ruijie 设备主机名 `R1` 和 `R2`

当前两个 YAML 示例文件，按你的要求，保留了已经验证过的口令和参数。

## 当前暴露的 MCP 工具

### `run_cli`

通用命令执行工具。

传入 `{command}` 后，直接在设备上执行任意 CLI。

常见例子：

- `show ip interface brief`
- `show version`
- `show running-config`

### `show_version`

固定执行 `show version`。

### `show_ip_interface_brief`

固定执行 `show ip interface brief`。

### `show_running_config`

固定执行 `show running-config`。

## 运行流程

整个运行链路现在是：

1. VS Code 通过 `.vscode/mcp.json` 启动 MCP 服务。
2. 服务读取 YAML 配置。
3. 打开串口。
4. 识别 `Username:` 和 `Password:` 提示。
5. 自动登录。
6. 需要时自动进入特权模式。
7. 如果配置了分页关闭命令，就先执行一次。
8. 把工具调用翻译成设备 CLI 命令。

在 Windows 上，项目还额外做了 CH340 的 Win32 原始句柄回退。

原因很简单：真机联调时，标准 pyserial 和 .NET 的 `SetCommState` 都在这个设备上失败过，但 Win32 直连能工作。

## YAML 配置结构

每个 YAML 文件分为两部分。

### 串口参数

```yaml
serial:
  port: COM3
  baud_rate: 9600
  bytesize: 8
  parity: N
  stopbits: 1
  timeout: 1.0
  read_timeout: 1.0
  xonxoff: true
  rtscts: false
  dsrdtr: false
  inter_byte_timeout: 0.1
```

### 会话参数

```yaml
session:
  hostname: R2
  username: admin
  password: "Test@123456"
  enable_password: "Test@123456"
  username_prompt: "Username:"
  password_prompt: "Password:"
  enable_command: "enable"
  user_prompt_suffix: ">"
  privileged_prompt_suffix: "#"
  line_ending: "\r\n"
  command_timeout: 15.0
  login_timeout: 20.0
  paging_disable_command: "terminal length 0"
```

这说明它现在不是简单的串口收发器，而是真正面向网络设备 CLI 会话的 MCP。

## 直接在 VS Code 里使用

这个路径最适合开发、调试、看日志。

当前本地工作区的 `mcp.json` 启动模式是：

```json
{
  "servers": {
    "NSM-DEBUG_MCP": {
      "type": "stdio",
      "command": "py",
      "args": [
        "-3",
        "src/nsm_debug_mcp/server.py",
        "NSM-DEBUG_MCP_R1.example.yaml"
      ]
    }
  }
}
```

含义：

1. VS Code 通过 Windows 自带 `py -3` 拉起 Python。
2. Python 直接运行源码里的 MCP 服务。
3. 服务按传入的 YAML 路径加载配置。

推荐步骤：

1. 直接打开 `NSM-DEBUG_MCP_03312026_Windows/NSM-DEBUG_MCP/` 这个目录作为独立工作区。
2. 按需修改 `NSM-DEBUG_MCP_R1.example.yaml` 或 `NSM-DEBUG_MCP_R2.example.yaml`。
3. 打开命令面板，执行 `MCP: List Servers`。
4. 启动 `NSM-DEBUG_MCP`。
5. 打开 Copilot Chat 的 Agent 模式，调用工具。

## 在 Chat 里怎么调用

可以直接用这些提示词：

```text
查看 R2 的版本信息
查看 R2 接口摘要
在 R2 上执行 show ip route
在 R2 上执行 show running-config
```

## 已验证结果

真机已经确认这些链路有效：

1. `COM3` 打开成功。
2. 用户名密码自动登录成功。
3. 特权模式自动进入成功。
4. `show version` 执行成功。
5. `show ip interface brief` 执行成功。
6. `show running-config` 执行成功。
7. 从 `R1` 切到 `R2` 继续工作成功。

另外也确认了几件事：

1. 自动登录后再执行 `enable` 没意义，因为已经在特权模式。
2. 当前验证设备上，测试时的 `configure terminal` 形式不被接受。
3. 提示符识别已经覆盖了 `R1(config)#` 这种配置模式提示符。

## 安全说明

当前两个示例 YAML 按你的要求保留了真实验证过的口令。

如果这个仓库要公开发布，建议先改掉。

## 最后定位

NSM-DEBUG_MCP 现在是一个精简、面向 VS Code、优先 Windows 兼容性的串口网络设备管理调试 MCP。

它的职责非常明确：

1. 在 VS Code 里启动。
2. 连到真实路由器或交换机串口。
3. 自动登录。
4. 通过 MCP 工具暴露常用管理命令。