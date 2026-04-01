<h1 align="center">NSM-DEBUG_MCP User Guide</h1>

<p align="center">
  <b>Serial Console × VS Code × AI — Manage Network Devices Without Leaving Your Editor</b>
</p>

<p align="center">
  <a href="NSM-DEBUG_MCP_Guide_ZH.md">🌐 中文版</a> ·
  <a href="https://github.com/QianChang-official/NSM-DEBUG_MCP">📦 GitHub Repository</a>
</p>

---

## Table of Contents

- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation](#installation)
- [Device Configuration](#device-configuration)
- [Starting the Server](#starting-the-server)
- [Using the Tools](#using-the-tools)
- [Available Tools](#available-tools)
- [BootLoader Factory Reset](#bootloader-factory-reset)
- [Standalone Scripts](#standalone-scripts)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

## Introduction

NSM-DEBUG_MCP lets you manage serial-connected network devices directly from VS Code Copilot Chat using natural language.

```
You (Copilot Chat) → "Show me the routing table"
     ↓
NSM-DEBUG_MCP → serial → show ip route → result back to chat
```

**No terminal switching. No memorizing commands.** Just talk to the AI — the device executes.

---

## Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10 / 11 / Server |
| Python | ≥ 3.11 |
| Editor | VS Code with GitHub Copilot Chat extension |
| Serial Adapter | USB-to-serial cable (CH340 / CP2102) |
| Target Devices | Ruijie routers, switches, ACs, gateways, or any CLI device |
| Serial Settings | Default 9600 8N1 (adjust to match your device) |

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/QianChang-official/NSM-DEBUG_MCP.git
cd NSM-DEBUG_MCP
```

### Step 2: Install Dependencies

```bash
pip install -e .
```

> Optional: use a virtual environment — `python -m venv .venv`, activate it, then install.

### Step 3: Copy the Example Config

```bash
cp NSM-DEBUG_MCP.example.yaml my_device.yaml
```

---

## Device Configuration

Open your config file (e.g. `my_device.yaml`) and fill in the actual values:

### Serial Settings

```yaml
serial:
  port: COM3              # Your COM port, or leave empty for auto-detect
  baud_rate: 9600
  bytesize: 8
  parity: N
  stopbits: 1
  xonxoff: true           # Software flow control (adjust as needed)
```

### Session Settings

```yaml
session:
  hostname: R1                        # Must match device hostname exactly
  username: admin                     # Login username
  password: "your_password"           # ⚠️ Replace with actual password
  enable_password: "your_enable_pwd"  # ⚠️ Replace with actual enable password
  paging_disable_command: "terminal length 0"
```

> **Tip**: The `hostname` field is used for prompt detection. It must match the device's actual hostname.

---

## Starting the Server

### Option A: Inside VS Code (Recommended)

1. Open the `NSM-DEBUG_MCP` folder in VS Code
2. Press `Ctrl+Shift+P` → type `MCP: List Servers`
3. Select `NSM-DEBUG_MCP` and start it
4. Switch to Copilot Chat → Agent mode

> The `.vscode/mcp.json` is pre-configured to load `NSM-DEBUG_MCP.example.yaml`.
> To use a custom config, change the last item in `args`.

### Option B: PowerShell Launcher

```powershell
.\run_nsm_debug_mcp.ps1
# Or with a custom config:
.\run_nsm_debug_mcp.ps1 -Config my_device.yaml
```

---

## Using the Tools

Once the server is running, use natural language in Copilot Chat (Agent mode):

| What You Say | What Executes |
|-------------|---------------|
| "Show device version" | `show version` |
| "Show the routing table" | `show ip route` |
| "Show interface status" | `show ip interface brief` |
| "Show the running config" | `show running-config` |
| "Show VLAN info" | `show vlan` |
| "Show OSPF neighbors" | `show ip ospf neighbor` |
| "List all APs" | `show ap all` |
| "Save the config" | `write memory` |
| "Run show clock on the device" | `show clock` (via `run_cli`) |

---

## Available Tools

<details>
<summary><b>📋 General Operations (15)</b></summary>

| Tool | Command | Purpose |
|------|---------|---------|
| `run_cli` | `{command}` | Execute any CLI command |
| `show_version` | `show version` | Device version info |
| `show_running_config` | `show running-config` | Running configuration |
| `show_startup_config` | `show startup-config` | Startup configuration |
| `show_ip_interface_brief` | `show ip interface brief` | Interface IP summary |
| `show_ip_route` | `show ip route` | IPv4 routing table |
| `show_vlan` | `show vlan` | VLAN information |
| `show_mac_address_table` | `show mac-address-table` | MAC address table |
| `show_lldp_neighbors` | `show lldp neighbors` | LLDP neighbors |
| `show_lldp_neighbors_detail` | `show lldp neighbors detail` | LLDP neighbor details |
| `show_ip_dhcp_binding` | `show ip dhcp binding` | DHCP lease table |
| `show_privilege` | `show privilege` | Current privilege level |
| `show_flash` | `dir flash:` | Flash storage contents |
| `show_interfaces` | `show interfaces {interface}` | Specific interface details |
| `show_running_include` | `show running-config \| include {pattern}` | Filtered config output |

</details>

<details>
<summary><b>🌐 IPv6 (2)</b></summary>

| Tool | Command |
|------|---------|
| `show_ipv6_interface_brief` | `show ipv6 interface brief` |
| `show_ipv6_route` | `show ipv6 route` |

</details>

<details>
<summary><b>🔀 Routing Protocols (4)</b></summary>

| Tool | Command |
|------|---------|
| `show_ip_ospf_neighbor` | `show ip ospf neighbor` |
| `show_ip_bgp_summary` | `show ip bgp summary` |
| `show_isis_neighbors` | `show isis neighbors` |
| `show_ip_rip_database` | `show ip rip database` |

</details>

<details>
<summary><b>📡 Wireless AC (2)</b></summary>

| Tool | Command |
|------|---------|
| `show_ap_all` | `show ap all` |
| `show_ap_config_summary` | `show ap-config summary` |

</details>

<details>
<summary><b>💾 Save & Reset (2)</b></summary>

| Tool | Command |
|------|---------|
| `write_memory` | `write memory` |
| `save_config` | `save` |

</details>

<details>
<summary><b>🔧 Built-in Tools (no YAML config needed)</b></summary>

| Tool | Purpose |
|------|---------|
| `send_control_keys` | Send control keys (Ctrl+C / Ctrl+B / Ctrl+Q, etc.) |
| `auto_factory_reset` | Automated BootLoader factory reset workflow |

**Supported profiles:** `router` · `switch` · `ws6008` · `gateway`

</details>

---

## BootLoader Factory Reset

For devices that need a full factory reset, NSM-DEBUG_MCP includes automated BootLoader reset workflows.

**Supported device types:**

| Device Type | Procedure |
|-------------|-----------|
| Router (RSR20-X) | Ctrl+C → BootLoader → clear config → reboot |
| Switch (S5310/S5760) | Ctrl+B → BootLoader → clear config → reboot |
| Wireless Controller (WS6008) | Ctrl+B → BootLoader → clear config → reboot |
| Gateway (EG3210) | Ctrl+Q → recovery mode → factory restore |

In Copilot Chat, say **"Factory reset the device"** to trigger the workflow.

---

## Standalone Scripts

The `tools/` directory provides standalone Python scripts that work without VS Code:

| Script | Purpose |
|--------|---------|
| `selftest_list_tools.py` | Load config and print all registered tools |
| `run_r1_ctrlc_ctrlq_factory_reset.py` | Full automated router factory reset with logging |

```bash
# Self-test
python tools/selftest_list_tools.py

# Automated factory reset (logs output to txt/)
python tools/run_r1_ctrlc_ctrlq_factory_reset.py
```

---

## Troubleshooting

<details>
<summary><b>Cannot open serial port / "Access Denied"</b></summary>

1. Verify the serial cable is connected and appears as COMx in Device Manager
2. Close any other program using that port (SecureCRT, PuTTY, etc.)
3. Run VS Code as Administrator

</details>

<details>
<summary><b>Login timeout / stuck at "Waiting for login prompt"</b></summary>

1. Check that `username_prompt` and `password_prompt` in YAML match your device's actual prompts
2. Verify baud rate (common: 9600 or 115200)
3. Test the connection manually with PuTTY or SecureCRT first

</details>

<details>
<summary><b>CH340 serial connection fails</b></summary>

NSM-DEBUG_MCP includes a built-in Win32 native API fallback. If the standard pyserial driver fails, the server automatically switches to direct Win32 API calls — no manual intervention required.

</details>

<details>
<summary><b>Command returns empty output</b></summary>

1. Ensure `hostname` matches the device hostname exactly (used for prompt matching)
2. Increase `command_timeout` (some commands produce slow output)
3. Confirm you're in privileged mode (use `show_privilege` to check)

</details>

---

## Security Notes

- **Never commit real passwords to a public repository.** The example config uses placeholder values — replace them before use
- Add config files with real credentials to `.gitignore`
- For production environments, consider TACACS+ / RADIUS centralized authentication

---

<p align="center">
  <sub>📖 <a href="NSM-DEBUG_MCP_Guide_ZH.md">中文版</a> · Found an issue? <a href="https://github.com/QianChang-official/NSM-DEBUG_MCP/issues">Open an Issue</a></sub>
</p>