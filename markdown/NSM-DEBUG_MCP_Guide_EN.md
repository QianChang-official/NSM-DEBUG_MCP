# NSM-DEBUG_MCP Guide

## Notice

NSM-DEBUG_MCP is a derivative project based on MCP2Serial.

Most of the refactoring, real-device adaptation, VS Code integration work, and documentation writing were completed with GPT-5.4 assistance.

If any content is considered infringing, contact the maintainer for direct removal.

## What This Project Is

NSM-DEBUG_MCP is a Windows-first MCP project for Visual Studio Code.

Its job is specific:

1. Connect to a real serial console device.
2. Complete username, password, and privileged-mode entry automatically.
3. Expose device CLI commands as MCP tools in VS Code.

This rollback keeps only the shortest usable path: direct source-based startup in VS Code.

## Current Repository Layout

The retained structure is now:

- `.vscode/mcp.json`
- `src/nsm_debug_mcp/`
- `NSM-DEBUG_MCP_R1.example.yaml`
- `NSM-DEBUG_MCP_R2.example.yaml`
- `markdown/NSM-DEBUG_MCP_Guide_EN.md`
- `markdown/NSM-DEBUG_MCP_Guide_ZH.md`

Meaning:

- `.vscode/mcp.json`: starts the server directly from VS Code.
- `src/nsm_debug_mcp/`: actual MCP server implementation.
- `NSM-DEBUG_MCP_R1.example.yaml` and `NSM-DEBUG_MCP_R2.example.yaml`: validated example device profiles.

## Verified Environment

Verified environment during implementation:

- Windows
- Python 3.14
- VS Code with GitHub Copilot Chat and Agent mode
- CH340 serial adapter on `COM3`
- Ruijie devices with hostnames `R1` and `R2`
- Serial settings `9600 8N1 XON/XOFF`

The current example YAML files intentionally keep the validated credentials and console settings.

## Exposed MCP Tools

The current example profiles expose these tools:

### `run_cli`

Runs any device CLI command passed through `{command}`.

Typical use:

- `show ip interface brief`
- `show version`
- `show running-config`

### `show_version`

Fixed wrapper for `show version`.

### `show_ip_interface_brief`

Fixed wrapper for `show ip interface brief`.

### `show_running_config`

Fixed wrapper for `show running-config`.

## How The Server Works

The runtime flow is:

1. VS Code starts the server through `.vscode/mcp.json`.
2. The server loads a YAML profile.
3. The server opens the serial port.
4. The server detects login prompts.
5. The server logs in automatically.
6. The server enters privileged mode when needed.
7. The server disables paging if configured.
8. Tool calls are translated into CLI commands.

The Windows build includes a CH340-oriented raw Win32 fallback because standard pyserial configuration failed on the verified hardware during real testing.

## YAML Configuration Structure

Each example YAML contains two parts.

### Serial section

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

### Session section

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

This is not a generic text-serial demo anymore.

It is a CLI session automation profile for real network devices.

## Use It Directly In VS Code

This path is best for development and direct debugging.

The current package-local `.vscode/mcp.json` pattern is:

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

Meaning:

1. VS Code starts Python through the Windows `py -3` launcher.
2. Python starts the server from source.
3. The server reads the selected YAML profile by direct path.

Recommended steps:

1. Open `NSM-DEBUG_MCP_03312026_Windows/NSM-DEBUG_MCP/` as a standalone VS Code workspace.
2. Edit `NSM-DEBUG_MCP_R1.example.yaml` or `NSM-DEBUG_MCP_R2.example.yaml` if needed.
3. Run `MCP: List Servers`.
4. Start `NSM-DEBUG_MCP`.
5. Open Copilot Chat in Agent mode and invoke the tools.

## How To Use The Tools In Chat

Typical chat prompts:

```text
Show version information of R2
Show the interface summary of R2
Execute show ip route on R2
Execute show running-config on R2
```

## Verified Results

These flows were verified against real devices:

1. Opened `COM3` successfully.
2. Completed automatic username and password login.
3. Entered privileged mode automatically.
4. Executed `show version` successfully.
5. Executed `show ip interface brief` successfully.
6. Executed `show running-config` successfully.
7. Switched validation from `R1` to `R2` successfully.

Also confirmed:

1. Re-running `enable` after login is unnecessary because the session is already privileged.
2. `configure terminal` was rejected by the tested device CLI in the verified session.
3. Prompt recognition handles forms like `R1(config)#`.

## Security Note

The example YAML files currently keep real validated credentials because that is how this repository was requested to be retained.

If this repository is published publicly, change them first.

## Final Positioning

NSM-DEBUG_MCP is now a trimmed, VS Code focused, Windows-first MCP deployment for serial network device management and debugging.

It is no longer a general demo package.

It is a practical toolchain for:

1. Starting inside VS Code.
2. Connecting to a real router or switch console.
3. Logging in automatically.
4. Exposing useful management commands as MCP tools.