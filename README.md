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
