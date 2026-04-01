<p align="center">
  <img src="https://img.shields.io/badge/MCP-Serial_Console-blue?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="MCP Badge"/>
  <img src="https://img.shields.io/badge/Python-≥3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/github/license/QianChang-official/NSM-DEBUG_MCP?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">NSM-DEBUG_MCP</h1>

<p align="center">
  <b>Network System Management — Debug MCP Server</b><br/>
  A Windows-first <a href="https://modelcontextprotocol.io/">MCP</a> server for VS Code that turns serial console interactions into AI-callable tools.
</p>

<p align="center">
  <a href="markdown/NSM-DEBUG_MCP_Guide_EN.md">📖 English Guide</a> ·
  <a href="markdown/NSM-DEBUG_MCP_Guide_ZH.md">📖 中文教程</a> ·
  <a href="https://github.com/QianChang-official/NSM-DEBUG_MCP/issues">🐛 Report Bug</a> ·
  <a href="https://github.com/QianChang-official/NSM-DEBUG_MCP/issues">💡 Request Feature</a>
</p>

---

## What It Does

Connect a serial cable, point the server at your device, and talk to network equipment through VS Code Copilot Agent — no terminal window switching required.

```
You (Copilot Chat) → "查看 R1 路由表"
     ↓
NSM-DEBUG_MCP → serial console → show ip route
     ↓
Device output → Copilot Chat
```

## Features

| Category | Capability |
|----------|-----------|
| **Session Automation** | Auto login (username / password / enable), paging disable |
| **CLI Tools** | 20+ pre-defined commands: show, OSPF, BGP, IS-IS, VLAN, DHCP, IPv6… |
| **BootLoader Reset** | Automated factory reset for routers, switches, ACs, gateways |
| **Control Keys** | Raw Ctrl+C / Ctrl+B / Ctrl+Q injection over serial |
| **Win32 Fallback** | CH340 USB-serial workaround via native Win32 API |
| **YAML Profiles** | One config file per device — swap targets in seconds |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/QianChang-official/NSM-DEBUG_MCP.git
cd NSM-DEBUG_MCP

# 2. Install dependencies
pip install -e .

# 3. Copy and edit the example config
cp NSM-DEBUG_MCP.example.yaml my_device.yaml
# Edit my_device.yaml: set hostname, credentials, COM port

# 4. Open in VS Code → MCP: List Servers → Start NSM-DEBUG_MCP
# 5. Open Copilot Chat (Agent mode) → invoke tools
```

## Available MCP Tools

<details>
<summary><b>General (click to expand)</b></summary>

| Tool | Command | Description |
|------|---------|-------------|
| `run_cli` | `{command}` | Execute any CLI command |
| `show_version` | `show version` | Device version info |
| `show_running_config` | `show running-config` | Running configuration |
| `show_startup_config` | `show startup-config` | Startup configuration |
| `show_ip_interface_brief` | `show ip interface brief` | Interface summary |
| `show_ip_route` | `show ip route` | IPv4 routing table |
| `show_vlan` | `show vlan` | VLAN configuration |
| `show_mac_address_table` | `show mac-address-table` | MAC address table |
| `show_lldp_neighbors` | `show lldp neighbors` | LLDP neighbors |
| `show_lldp_neighbors_detail` | `show lldp neighbors detail` | LLDP neighbor details |
| `show_ip_dhcp_binding` | `show ip dhcp binding` | DHCP lease table |
| `show_privilege` | `show privilege` | Current privilege level |
| `show_flash` | `dir flash:` | Flash directory |
| `show_interfaces` | `show interfaces {interface}` | Interface details |
| `show_running_include` | `show running-config \| include {pattern}` | Filtered config |

</details>

<details>
<summary><b>IPv6</b></summary>

| Tool | Command |
|------|---------|
| `show_ipv6_interface_brief` | `show ipv6 interface brief` |
| `show_ipv6_route` | `show ipv6 route` |

</details>

<details>
<summary><b>Routing Protocols</b></summary>

| Tool | Command |
|------|---------|
| `show_ip_ospf_neighbor` | `show ip ospf neighbor` |
| `show_ip_bgp_summary` | `show ip bgp summary` |
| `show_isis_neighbors` | `show isis neighbors` |
| `show_ip_rip_database` | `show ip rip database` |

</details>

<details>
<summary><b>AC / Wireless</b></summary>

| Tool | Command |
|------|---------|
| `show_ap_all` | `show ap all` |
| `show_ap_config_summary` | `show ap-config summary` |

</details>

<details>
<summary><b>Save & Reset</b></summary>

| Tool | Command |
|------|---------|
| `write_memory` | `write memory` |
| `save_config` | `save` |

</details>

<details>
<summary><b>Built-in Tools (no YAML config needed)</b></summary>

| Tool | Description |
|------|-------------|
| `send_control_keys` | Send raw control keys (Ctrl+C, Ctrl+B, Ctrl+Q…) |
| `auto_factory_reset` | Automated BootLoader factory reset workflow |

**Supported reset profiles:** `router` · `switch` · `ws6008` · `gateway`

</details>

## Standalone Tool Scripts

The `tools/` directory provides standalone Python scripts for headless automation (no VS Code needed):

| Script | Purpose |
|--------|---------|
| `selftest_list_tools.py` | Load config and print all registered MCP tool names |
| `run_r1_ctrlc_ctrlq_factory_reset.py` | Execute full router factory reset with logging & verification |

```bash
# Run self-test
python tools/selftest_list_tools.py

# Run automated factory reset (outputs to txt/)
python tools/run_r1_ctrlc_ctrlq_factory_reset.py
```

## Configuration

A single YAML file controls everything. See [`NSM-DEBUG_MCP.example.yaml`](NSM-DEBUG_MCP.example.yaml) for the full reference.

```yaml
serial:
  port: COM3          # or leave empty for auto-detect
  baud_rate: 9600
  bytesize: 8
  parity: N
  stopbits: 1

session:
  hostname: R1
  username: admin
  password: "your_password"
  enable_password: "your_enable_password"

commands:
  run_cli:
    command: "{command}"
    need_parse: true
    prompts:
      - "Execute {command} on the device"
```

## VS Code Integration

`.vscode/mcp.json` starts the server directly:

```json
{
  "servers": {
    "NSM-DEBUG_MCP": {
      "type": "stdio",
      "command": ".venv/Scripts/python.exe",
      "args": ["src/nsm_debug_mcp/server.py", "NSM-DEBUG_MCP.example.yaml"]
    }
  }
}
