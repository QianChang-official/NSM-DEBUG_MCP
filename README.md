# NSM-DEBUG_MCP

**Network System Management — Debug MCP Server**

A Windows-first MCP (Model Context Protocol) server for Visual Studio Code that automates serial console interaction with network devices (Ruijie routers, switches, gateways, ACs).

## Features

- Automatic serial console login (username / password / enable)
- CLI command execution exposed as MCP tools in VS Code Copilot Agent mode
- BootLoader-based factory reset automation (Ctrl+C / Ctrl+B / Ctrl+Q workflows)
- Raw control-key injection over serial
- CH340 Win32 fallback for problematic USB-serial adapters
- YAML-driven device profiles

## Quick Start

1. Open this folder as a VS Code workspace.
2. Copy an example YAML and fill in your device credentials:
   ```
   cp NSM-DEBUG_MCP_R1.example.yaml my_device.yaml
   ```
3. Edit `.vscode/mcp.json` to point to your YAML.
4. Run **MCP: List Servers** → start **NSM-DEBUG_MCP**.
5. Open Copilot Chat in Agent mode and invoke the tools.

## Requirements

- Windows (primary target)
- Python ≥ 3.11
- `pyserial`, `mcp`, `pyyaml` (see `pyproject.toml`)

## Documentation

- [English Guide](markdown/NSM-DEBUG_MCP_Guide_EN.md)
- [中文教程](markdown/NSM-DEBUG_MCP_Guide_ZH.md)

## License

[MIT](LICENSE)
