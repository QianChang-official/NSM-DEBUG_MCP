<h1 align="center">NSM-DEBUG_MCP 用户指南</h1>

<p align="center">
  <b>串口网络设备 × VS Code × AI —— 零终端窗口切换的网管体验</b>
</p>

<p align="center">
  <a href="NSM-DEBUG_MCP_Guide_EN.md">🌐 English Version</a> ·
  <a href="https://github.com/QianChang-official/NSM-DEBUG_MCP">📦 GitHub 仓库</a>
</p>

---

## 目录

- [简介](#简介)
- [环境要求](#环境要求)
- [安装与准备](#安装与准备)
- [配置设备](#配置设备)
- [启动服务](#启动服务)
- [使用工具](#使用工具)
- [可用工具一览](#可用工具一览)
- [BootLoader 恢复出厂](#bootloader-恢复出厂)
- [独立脚本工具](#独立脚本工具)
- [常见问题排查](#常见问题排查)
- [安全建议](#安全建议)

---

## 简介

NSM-DEBUG_MCP 让你在 VS Code Copilot Chat 中，通过自然语言直接管理串口连接的网络设备。

```
你在 Copilot Chat 中输入 → "查看路由表"
     ↓
NSM-DEBUG_MCP → 串口发送 show ip route → 返回结果到聊天窗口
```

**不需要切换终端，不需要记命令**——对着 AI 说话，设备就执行。

---

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11 / Server |
| Python | ≥ 3.11 |
| 编辑器 | VS Code（已安装 GitHub Copilot Chat 扩展） |
| 串口适配器 | USB 转串口线（CH340 / CP2102 均可） |
| 目标设备 | 锐捷路由器、交换机、AC、网关等 CLI 设备 |
| 串口参数 | 默认 9600 8N1（按设备实际情况调整） |

---

## 安装与准备

### 第一步：克隆仓库

```bash
git clone https://github.com/QianChang-official/NSM-DEBUG_MCP.git
cd NSM-DEBUG_MCP
```

### 第二步：安装依赖

```bash
pip install -e .
```

> 也可以使用虚拟环境：`python -m venv .venv`，然后激活后再安装。

### 第三步：复制示例配置

```bash
cp NSM-DEBUG_MCP.example.yaml my_device.yaml
```

---

## 配置设备

打开复制好的配置文件（如 `my_device.yaml`），按实际情况填写：

### 串口参数

```yaml
serial:
  port: COM3              # 你的串口号，留空则自动检测
  baud_rate: 9600
  bytesize: 8
  parity: N
  stopbits: 1
  xonxoff: true           # 软件流控（按设备需要开关）
```

### 会话参数

```yaml
session:
  hostname: R1                        # 设备主机名
  username: admin                     # 登录用户名
  password: "your_password"           # ⚠️ 请替换为实际密码
  enable_password: "your_enable_pwd"  # ⚠️ 请替换为实际特权密码
  paging_disable_command: "terminal length 0"
```

> **提示**：`hostname` 用于提示符识别，务必与设备实际主机名一致。

---

## 启动服务

### 方式一：VS Code 内启动（推荐）

1. 用 VS Code 打开 `NSM-DEBUG_MCP` 目录
2. 按 `Ctrl+Shift+P` → 输入 `MCP: List Servers`
3. 选择 `NSM-DEBUG_MCP` 并启动
4. 切换到 Copilot Chat → Agent 模式

> `.vscode/mcp.json` 已预配置好启动参数，默认加载 `NSM-DEBUG_MCP.example.yaml`。
> 如需使用自定义配置文件，修改 `mcp.json` 中的 `args` 最后一项即可。

### 方式二：PowerShell 一键启动

```powershell
.\run_nsm_debug_mcp.ps1
# 或指定配置：
.\run_nsm_debug_mcp.ps1 -Config my_device.yaml
```

---

## 使用工具

服务启动后，在 Copilot Chat（Agent 模式）中用自然语言即可调用：

| 你说的话 | 实际执行 |
|----------|----------|
| "查看设备版本" | `show version` |
| "查看路由表" | `show ip route` |
| "查看接口状态" | `show ip interface brief` |
| "查看当前配置" | `show running-config` |
| "查看 VLAN 信息" | `show vlan` |
| "查看 OSPF 邻居" | `show ip ospf neighbor` |
| "查看 AP 列表" | `show ap all` |
| "保存配置" | `write memory` |
| "在设备上执行 show clock" | `show clock`（通过 `run_cli`） |

---

## 可用工具一览

<details>
<summary><b>📋 常规运维（15 个）</b></summary>

| 工具名 | 执行命令 | 用途 |
|--------|----------|------|
| `run_cli` | `{command}` | 执行任意 CLI 命令 |
| `show_version` | `show version` | 查看设备版本信息 |
| `show_running_config` | `show running-config` | 查看当前运行配置 |
| `show_startup_config` | `show startup-config` | 查看启动配置 |
| `show_ip_interface_brief` | `show ip interface brief` | 查看接口 IP 摘要 |
| `show_ip_route` | `show ip route` | 查看 IPv4 路由表 |
| `show_vlan` | `show vlan` | 查看 VLAN 信息 |
| `show_mac_address_table` | `show mac-address-table` | 查看 MAC 地址表 |
| `show_lldp_neighbors` | `show lldp neighbors` | 查看 LLDP 邻居 |
| `show_lldp_neighbors_detail` | `show lldp neighbors detail` | 查看 LLDP 邻居详情 |
| `show_ip_dhcp_binding` | `show ip dhcp binding` | 查看 DHCP 地址绑定 |
| `show_privilege` | `show privilege` | 查看当前权限等级 |
| `show_flash` | `dir flash:` | 查看 Flash 存储内容 |
| `show_interfaces` | `show interfaces {interface}` | 查看指定接口详情 |
| `show_running_include` | `show running-config \| include {pattern}` | 过滤查看配置 |

</details>

<details>
<summary><b>🌐 IPv6（2 个）</b></summary>

| 工具名 | 执行命令 |
|--------|----------|
| `show_ipv6_interface_brief` | `show ipv6 interface brief` |
| `show_ipv6_route` | `show ipv6 route` |

</details>

<details>
<summary><b>🔀 路由协议（4 个）</b></summary>

| 工具名 | 执行命令 |
|--------|----------|
| `show_ip_ospf_neighbor` | `show ip ospf neighbor` |
| `show_ip_bgp_summary` | `show ip bgp summary` |
| `show_isis_neighbors` | `show isis neighbors` |
| `show_ip_rip_database` | `show ip rip database` |

</details>

<details>
<summary><b>📡 无线 AC（2 个）</b></summary>

| 工具名 | 执行命令 |
|--------|----------|
| `show_ap_all` | `show ap all` |
| `show_ap_config_summary` | `show ap-config summary` |

</details>

<details>
<summary><b>💾 保存与重置（2 个）</b></summary>

| 工具名 | 执行命令 |
|--------|----------|
| `write_memory` | `write memory` |
| `save_config` | `save` |

</details>

<details>
<summary><b>🔧 内置工具（无需 YAML 配置）</b></summary>

| 工具名 | 用途 |
|--------|------|
| `send_control_keys` | 发送控制键（Ctrl+C / Ctrl+B / Ctrl+Q 等） |
| `auto_factory_reset` | 自动化 BootLoader 恢复出厂流程 |

**支持的恢复配置：** `router` · `switch` · `ws6008` · `gateway`

</details>

---

## BootLoader 恢复出厂

对于需要恢复出厂设置的设备，NSM-DEBUG_MCP 内置了自动化 BootLoader 重置流程。

**支持设备类型和操作：**

| 设备类型 | 操作 |
|----------|------|
| 路由器（RSR20-X） | Ctrl+C 进入 BootLoader → 清除配置 → 重启 |
| 交换机（S5310/S5760） | Ctrl+B 进入 BootLoader → 清除配置 → 重启 |
| 无线控制器（WS6008） | Ctrl+B 进入 BootLoader → 清除配置 → 重启 |
| 网关（EG3210） | Ctrl+Q 进入恢复模式 → 恢复出厂 |

在 Copilot Chat 中说 **"对设备执行恢复出厂"** 即可触发。

---

## 独立脚本工具

`tools/` 目录提供不依赖 VS Code 的独立 Python 脚本：

| 脚本 | 用途 |
|------|------|
| `selftest_list_tools.py` | 加载配置并打印所有注册工具 |
| `run_r1_ctrlc_ctrlq_factory_reset.py` | 全自动路由器恢复出厂（含日志和验证） |

```bash
# 工具自检
python tools/selftest_list_tools.py

# 自动恢复出厂（输出日志到 txt/ 目录）
python tools/run_r1_ctrlc_ctrlq_factory_reset.py
```

---

## 常见问题排查

<details>
<summary><b>串口打不开 / 提示 "Access Denied"</b></summary>

1. 确认串口线已连接，设备管理器中能看到 COMx
2. 确认没有其他程序（SecureCRT、PuTTY）占用该端口
3. 以管理员身份运行 VS Code

</details>

<details>
<summary><b>登录超时 / 停在 "Waiting for login prompt"</b></summary>

1. 检查 YAML 中 `username_prompt` 和 `password_prompt` 是否与设备实际提示一致
2. 检查波特率是否正确（常见：9600 或 115200）
3. 尝试手动用串口工具（PuTTY/SecureCRT）连接设备确认可用

</details>

<details>
<summary><b>CH340 串口连接失败</b></summary>

NSM-DEBUG_MCP 内置了 Win32 原生接口回退方案。如 pyserial 标准模式失败，服务会自动切换到 Win32 API 直连，无需手动干预。

</details>

<details>
<summary><b>命令返回为空</b></summary>

1. 检查 `hostname` 是否与设备主机名完全一致（用于提示符匹配）
2. 增大 `command_timeout` 值（某些命令输出较慢）
3. 确认已进入特权模式（`show_privilege` 查看当前等级）

</details>

---

## 安全建议

- **不要将真实密码提交到公共仓库**。示例配置中的密码字段是占位符，使用前务必替换
- 建议将包含真实密码的配置文件加入 `.gitignore`
- 生产环境建议结合 TACACS+ / RADIUS 统一认证

---

<p align="center">
  <sub>📖 <a href="NSM-DEBUG_MCP_Guide_EN.md">English Version</a> · 遇到问题？<a href="https://github.com/QianChang-official/NSM-DEBUG_MCP/issues">提交 Issue</a></sub>
</p>