import datetime
import os
import sys
import traceback
import serial.tools.list_ports

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(SCRIPT_DIR)
SRC = os.path.join(PACKAGE_ROOT, "src")
YAML_PATH = os.path.join(PACKAGE_ROOT, "NSM-DEBUG_MCP_R1.example.yaml")
OUT_DIR = os.path.join(PACKAGE_ROOT, "txt")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, SRC)
from nsm_debug_mcp import server as s


def now_tag():
    return datetime.datetime.now().strftime("%Y%m%dT%H%M%S")


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def choose_port():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if s.config.port and s.config.port in ports:
        return s.config.port, ports
    if ports:
        return None, ports
    return s.config.port, ports


def run_verify(command):
    cmd = s.config.commands["run_cli"]
    result = s.serial_connection.send_command(cmd, {"command": command})
    return "\n".join(getattr(item, "text", str(item)) for item in result)


def main():
    s.config = s.Config.load(YAML_PATH)
    desired, ports = choose_port()
    if desired is None:
        s.config.port = None
    else:
        s.config.port = desired
    s.serial_connection.refresh_config()

    tag = now_tag()
    log_path = os.path.join(OUT_DIR, f"R1_自动恢复执行日志_{tag}.txt")
    verify_path = os.path.join(OUT_DIR, f"R1_自动恢复验证_{tag}.txt")

    log_parts = []
    log_parts.append(f"YAML: {YAML_PATH}")
    log_parts.append(f"Detected ports: {', '.join(ports) if ports else '(none)'}")
    log_parts.append(f"Configured port before auto-select: {s.config.port or '(auto scan)'}")

    try:
        reset_output = s.serial_connection.auto_factory_reset(
            profile_name="router",
            warm_reboot=True,
            interrupt_sequence="Ctrl+C",
            bootloader_entry_sequence="Ctrl+Q",
            timeout_seconds=240.0,
        )
        log_parts.append("=== auto_factory_reset output ===")
        log_parts.append(reset_output)
    except Exception as exc:
        log_parts.append("=== auto_factory_reset exception ===")
        log_parts.append(str(exc))
        log_parts.append(traceback.format_exc())
        write_text(log_path, "\n\n".join(log_parts))
        raise
    else:
        write_text(log_path, "\n\n".join(log_parts))

    verify_parts = []
    verify_parts.append("=== hostname check ===")
    try:
        verify_parts.append(run_verify("show running-config | include hostname"))
    except Exception as exc:
        verify_parts.append(f"ERROR: {exc}")
        verify_parts.append(traceback.format_exc())

    verify_parts.append("=== ip interface brief ===")
    try:
        verify_parts.append(run_verify("show ip interface brief"))
    except Exception as exc:
        verify_parts.append(f"ERROR: {exc}")
        verify_parts.append(traceback.format_exc())

    write_text(verify_path, "\n\n".join(verify_parts))
    print(log_path)
    print(verify_path)


if __name__ == "__main__":
    main()
