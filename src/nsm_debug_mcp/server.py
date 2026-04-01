# ====================================================
# Project: NSM-DEBUG_MCP
# Description: MCP server for network system management,
#              debugging, and serial console automation
#              in Visual Studio Code.
# License: MIT License
# ====================================================
from typing import Any, Optional, Dict, List
import asyncio
import serial
import serial.tools.list_ports
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import logging
import yaml
import os
from dataclasses import dataclass, field
import time
import re
import subprocess
import sys

if os.name == 'nt':
    try:
        import pywintypes
        import win32file
    except ImportError:
        pywintypes = None
        win32file = None
else:
    pywintypes = None
    win32file = None

_LOG_LEVEL_NAME = os.getenv("NSM_DEBUG_MCP_LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)

logging.basicConfig(
    level=_LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_DISPLAY_NAME = "NSM-DEBUG_MCP"
PROJECT_IDENTIFIER = "NSM-DEBUG_MCP"
VERSION = "0.6.0"
DEFAULT_CONFIG_FILES = (
    "NSM-DEBUG_MCP_R2.example.yaml",
    "NSM-DEBUG_MCP_R1.example.yaml",
)

server = Server(PROJECT_IDENTIFIER)

_BYTESIZE_MAP = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
    "5": serial.FIVEBITS,
    "6": serial.SIXBITS,
    "7": serial.SEVENBITS,
    "8": serial.EIGHTBITS,
}

_PARITY_MAP = {
    "N": serial.PARITY_NONE,
    "NONE": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "EVEN": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
    "ODD": serial.PARITY_ODD,
    "M": serial.PARITY_MARK,
    "MARK": serial.PARITY_MARK,
    "S": serial.PARITY_SPACE,
    "SPACE": serial.PARITY_SPACE,
}

_STOPBITS_MAP = {
    1: serial.STOPBITS_ONE,
    1.0: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2: serial.STOPBITS_TWO,
    2.0: serial.STOPBITS_TWO,
    "1": serial.STOPBITS_ONE,
    "1.0": serial.STOPBITS_ONE,
    "1.5": serial.STOPBITS_ONE_POINT_FIVE,
    "2": serial.STOPBITS_TWO,
    "2.0": serial.STOPBITS_TWO,
}

_CONTROL_KEY_ALIASES = {
    "CTRL+A": b"\x01",
    "CTRL+B": b"\x02",
    "CTRL+C": b"\x03",
    "CTRL+D": b"\x04",
    "CTRL+E": b"\x05",
    "CTRL+F": b"\x06",
    "CTRL+G": b"\x07",
    "CTRL+H": b"\x08",
    "CTRL+I": b"\x09",
    "CTRL+J": b"\x0a",
    "CTRL+K": b"\x0b",
    "CTRL+L": b"\x0c",
    "CTRL+M": b"\x0d",
    "CTRL+N": b"\x0e",
    "CTRL+O": b"\x0f",
    "CTRL+P": b"\x10",
    "CTRL+Q": b"\x11",
    "CTRL+R": b"\x12",
    "CTRL+S": b"\x13",
    "CTRL+T": b"\x14",
    "CTRL+U": b"\x15",
    "CTRL+V": b"\x16",
    "CTRL+W": b"\x17",
    "CTRL+X": b"\x18",
    "CTRL+Y": b"\x19",
    "CTRL+Z": b"\x1a",
    "ENTER": b"\r\n",
    "CR": b"\r",
    "LF": b"\n",
    "TAB": b"\t",
    "ESC": b"\x1b",
    "SPACE": b" ",
}

_BOOTLOADER_RESET_PROFILES: Dict[str, Dict[str, Any]] = {
    "router": {
        "description": "RG-RSR20-X / 路由器：Ctrl+C 进 BootLoader，delete config.text，再尝试 CLI 二次清理。",
        "interrupt_sequence": "Ctrl+C",
        "boot_menu_patterns": [],
        "bootloader_entry_sequence": None,
        "bootloader_prompt_patterns": ["BootLoader>", "bootloader>", "bootloader#"],
        "bootloader_command": "delete config.text",
        "bootloader_read_delay": 0.15,
        "bootloader_timeout": 2.0,
        "bootloader_responses": [
            {"if_contains": ["delete", "[no/yes]"], "text": "yes"},
            {"if_contains": ["delete", "[y/n]"], "text": "y"},
        ],
        "bootloader_reboot_sequence": "load -main",
        "bootloader_reboot_read_delay": 2.0,
        "bootloader_reboot_timeout": 5.0,
        "bootloader_reboot_responses": [],
        "wait_for_reconnect_after_bootloader": True,
        "reconnect_timeout": 180.0,
        "interrupt_interval": 0.3,
        "interrupt_timeout_per_attempt": 0.8,
        "warm_reboot_step": {
            "command": "reload",
            "responses": [
                {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                {"if_contains": ["reload", "reboot", "system"], "text": "y"},
            ],
            "read_delay": 0.8,
            "timeout": 2.0,
            "disconnect_after": True,
        },
        "post_boot_steps": [
            {
                "command": "delete flash:config.text",
                "responses": [
                    {"if_contains": ["delete", "[no/yes]"], "text": "yes"},
                    {"if_contains": ["delete", "[y/n]"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 1.5,
            },
            {
                "command": "reload",
                "responses": [
                    {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                    {"if_contains": ["reload", "reboot", "system"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 2.0,
                "disconnect_after": True,
            },
        ],
    },
    "switch": {
        "description": "交换机：Ctrl+B 进 Boot Menu，Ctrl+Q 进 bootloader，main_config_password_clear，再从 CLI 删除 config.text 并 reload。",
        "interrupt_sequence": "Ctrl+B",
        "boot_menu_patterns": ["BootLoader Menu", "Boot Menu", "TOP menu items"],
        "bootloader_entry_sequence": "Ctrl+Q",
        "bootloader_prompt_patterns": ["bootloader#", "Bootload>", "BootLoader>"],
        "bootloader_command": "main_config_password_clear",
        "bootloader_responses": [],
        "bootloader_reboot_sequence": None,
        "bootloader_reboot_responses": [],
        "wait_for_reconnect_after_bootloader": True,
        "reconnect_timeout": 180.0,
        "interrupt_interval": 0.3,
        "interrupt_timeout_per_attempt": 0.8,
        "warm_reboot_step": {
            "command": "reload",
            "responses": [
                {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                {"if_contains": ["reload", "reboot", "system"], "text": "y"},
            ],
            "read_delay": 0.8,
            "timeout": 2.0,
            "disconnect_after": True,
        },
        "post_boot_steps": [
            {
                "command": "delete flash:config.text",
                "responses": [
                    {"if_contains": ["delete", "[no/yes]"], "text": "yes"},
                    {"if_contains": ["delete", "[y/n]"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 1.5,
            },
            {
                "command": "reload",
                "responses": [
                    {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                    {"if_contains": ["reload", "reboot", "system"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 2.0,
                "disconnect_after": True,
            },
        ],
    },
    "ws6008": {
        "description": "WS6008 / AC：Ctrl+B 进 Boot Menu，Ctrl+Q 进 bootloader，main_config_password_clear，再从 CLI 删除 config.text 并 reload。",
        "interrupt_sequence": "Ctrl+B",
        "boot_menu_patterns": ["BootLoader Menu", "Boot Menu", "TOP menu items"],
        "bootloader_entry_sequence": "Ctrl+Q",
        "bootloader_prompt_patterns": ["bootloader#", "Bootload>", "BootLoader>"],
        "bootloader_command": "main_config_password_clear",
        "bootloader_responses": [],
        "bootloader_reboot_sequence": None,
        "bootloader_reboot_responses": [],
        "wait_for_reconnect_after_bootloader": True,
        "reconnect_timeout": 240.0,
        "interrupt_interval": 0.3,
        "interrupt_timeout_per_attempt": 0.8,
        "warm_reboot_step": {
            "command": "reload",
            "responses": [
                {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                {"if_contains": ["reload", "reboot", "system"], "text": "y"},
            ],
            "read_delay": 0.8,
            "timeout": 2.0,
            "disconnect_after": True,
        },
        "post_boot_steps": [
            {
                "command": "delete flash:config.text",
                "responses": [
                    {"if_contains": ["delete", "[no/yes]"], "text": "yes"},
                    {"if_contains": ["delete", "[y/n]"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 1.5,
            },
            {
                "command": "reload",
                "responses": [
                    {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                    {"if_contains": ["reload", "reboot", "system"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 2.0,
                "disconnect_after": True,
            },
        ],
    },
    "gateway": {
        "description": "网关：Ctrl+B/Ctrl+Q 进 bootloader，main_config_password_clear，再删除 config.text 和 ap-config.text。",
        "interrupt_sequence": "Ctrl+B",
        "boot_menu_patterns": ["BootLoader Menu", "Boot Menu", "TOP menu items"],
        "bootloader_entry_sequence": "Ctrl+Q",
        "bootloader_prompt_patterns": ["bootloader#", "Bootload>", "BootLoader>"],
        "bootloader_command": "main_config_password_clear",
        "bootloader_responses": [],
        "bootloader_reboot_sequence": None,
        "bootloader_reboot_responses": [],
        "wait_for_reconnect_after_bootloader": True,
        "reconnect_timeout": 240.0,
        "interrupt_interval": 0.3,
        "interrupt_timeout_per_attempt": 0.8,
        "warm_reboot_step": {
            "command": "reload",
            "responses": [
                {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                {"if_contains": ["reload", "reboot", "system"], "text": "y"},
            ],
            "read_delay": 0.8,
            "timeout": 2.0,
            "disconnect_after": True,
        },
        "post_boot_steps": [
            {
                "command": "delete flash:config.text",
                "responses": [
                    {"if_contains": ["delete", "[no/yes]"], "text": "yes"},
                    {"if_contains": ["delete", "[y/n]"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 1.5,
            },
            {
                "command": "delete flash:ap-config.text",
                "responses": [
                    {"if_contains": ["delete", "[no/yes]"], "text": "yes"},
                    {"if_contains": ["delete", "[y/n]"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 1.5,
            },
            {
                "command": "reload",
                "responses": [
                    {"if_contains": ["save", "modified", "configuration"], "text": "no"},
                    {"if_contains": ["reload", "reboot", "system"], "text": "y"},
                ],
                "read_delay": 0.8,
                "timeout": 2.0,
                "disconnect_after": True,
            },
        ],
    },
}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _parse_bytesize(value: Any) -> int:
    return _BYTESIZE_MAP.get(value, serial.EIGHTBITS)


def _parse_parity(value: Any) -> str:
    if value is None:
        return serial.PARITY_NONE
    return _PARITY_MAP.get(str(value).strip().upper(), serial.PARITY_NONE)


def _parse_stopbits(value: Any) -> float:
    return _STOPBITS_MAP.get(value, serial.STOPBITS_ONE)


def _normalize_patterns(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if re.search(r"[,;|\n]", text):
        return [item.strip() for item in re.split(r"[,;|\n]+", text) if item.strip()]
    return [text]


def _find_first_pattern(text: str, patterns: List[str]) -> Optional[str]:
    lowered_text = text.lower()
    for pattern in patterns:
        if pattern.lower() in lowered_text:
            return pattern
    return None


def _control_token_to_bytes(token: str) -> bytes:
    normalized = token.strip().upper()
    if not normalized:
        return b""
    if normalized in _CONTROL_KEY_ALIASES:
        return _CONTROL_KEY_ALIASES[normalized]
    if normalized.startswith("^") and len(normalized) == 2 and normalized[1].isalpha():
        return bytes([ord(normalized[1]) & 0x1F])
    return token.encode()


def _sequence_to_bytes(sequence: str) -> bytes:
    raw = str(sequence or "").strip()
    if not raw:
        return b""

    if re.search(r"[,;\n]", raw):
        tokens = re.split(r"[,;\n]+", raw)
        return b"".join(_control_token_to_bytes(token) for token in tokens if token.strip())

    parts = [part for part in raw.split() if part]
    if len(parts) > 1 and all(
        part.strip().upper() in _CONTROL_KEY_ALIASES or (part.startswith("^") and len(part) == 2)
        for part in parts
    ):
        return b"".join(_control_token_to_bytes(part) for part in parts)

    return _control_token_to_bytes(raw)


class Win32SerialPort:
    """Minimal serial-port adapter using Win32 APIs for CH340-style fallback on Windows."""

    def __init__(self, port: str, timeout: float, read_timeout: float, inter_byte_timeout: float = 0.1):
        self.port = port
        self.name = port
        self.timeout = timeout
        self.read_timeout = read_timeout
        self._inter_byte_timeout = inter_byte_timeout
        self.handle = None
        self.is_open = False

    def open(self) -> None:
        self.handle = win32file.CreateFile(
            fr"\\.\{self.port}",
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        inter_byte = getattr(self, '_inter_byte_timeout', None) or 0.1
        interval_ms = max(1, int(max(inter_byte, 0.01) * 1000))
        read_ms = max(1, int(max(self.read_timeout, 0.1) * 1000))
        write_ms = max(1, int(max(self.timeout, 0.1) * 1000))
        win32file.SetCommTimeouts(self.handle, (interval_ms, 0, read_ms, 0, write_ms))
        self.is_open = True

    @property
    def in_waiting(self) -> int:
        if not self.is_open:
            return 0
        _, stat = win32file.ClearCommError(self.handle)
        return stat.cbInQue

    def read(self, size: int = 1) -> bytes:
        if not self.is_open:
            return b''
        _, data = win32file.ReadFile(self.handle, max(1, size))
        return data

    def write(self, payload: bytes) -> int:
        if not self.is_open:
            raise serial.SerialException(f"Port {self.port} is not open")
        _, bytes_written = win32file.WriteFile(self.handle, payload)
        return bytes_written

    def flush(self) -> None:
        return None

    def reset_input_buffer(self) -> None:
        if self.is_open:
            win32file.PurgeComm(self.handle, win32file.PURGE_RXCLEAR)

    def reset_output_buffer(self) -> None:
        if self.is_open:
            win32file.PurgeComm(self.handle, win32file.PURGE_TXCLEAR)

    def close(self) -> None:
        if self.is_open and self.handle is not None:
            self.handle.Close()
            self.handle = None
            self.is_open = False

@dataclass
class Command:
    """Configuration for a serial command."""
    command: str
    need_parse: bool
    prompts: List[str]

@dataclass
class Config:
    """Configuration for the VS Code oriented MCP service."""
    port: Optional[str] = None
    baud_rate: int = 115200
    timeout: float = 1.0
    read_timeout: float = 1.0
    response_start_string: str = "OK"
    bytesize: int = serial.EIGHTBITS
    parity: str = serial.PARITY_NONE
    stopbits: float = serial.STOPBITS_ONE
    xonxoff: bool = False
    rtscts: bool = False
    dsrdtr: bool = False
    inter_byte_timeout: Optional[float] = None
    hostname: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enable_password: Optional[str] = None
    username_prompt: str = "Username:"
    password_prompt: str = "Password:"
    enable_command: str = "enable"
    user_prompt_suffix: str = ">"
    privileged_prompt_suffix: str = "#"
    line_ending: str = "\r\n"
    command_timeout: float = 10.0
    login_timeout: float = 15.0
    paging_disable_command: Optional[str] = "terminal length 0"
    commands: Dict[str, Command] = field(default_factory=dict)

    @staticmethod
    def load(config_path: str = DEFAULT_CONFIG_FILES[0]) -> 'Config':
        """Load configuration from YAML file."""
        config_paths: List[str] = []
        executable_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        def add_candidate(path: Optional[str]) -> None:
            if path and path not in config_paths:
                config_paths.append(path)

        if config_path:
            config_name = os.path.basename(config_path)
            add_candidate(config_path)
            add_candidate(os.path.join(os.getcwd(), config_name))
            add_candidate(os.path.join(executable_dir, config_name))

        for default_name in DEFAULT_CONFIG_FILES:
            add_candidate(os.path.join(os.getcwd(), default_name))
            add_candidate(os.path.join(executable_dir, default_name))
            add_candidate(default_name)

        # 尝试从每个位置加载配置
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                    logger.info(f"Loading configuration from {path}")
                    
                    # Load serial configuration
                    serial_config = config_data.get('serial', {})
                    session_config = config_data.get('session', {})
                    config = Config(
                        port=serial_config.get('port'),
                        baud_rate=serial_config.get('baud_rate', 115200),
                        timeout=serial_config.get('timeout', 1.0),
                        read_timeout=serial_config.get('read_timeout', 1.0),
                        response_start_string=serial_config.get('response_start_string', 'OK'),
                        bytesize=_parse_bytesize(serial_config.get('bytesize', 8)),
                        parity=_parse_parity(serial_config.get('parity', 'N')),
                        stopbits=_parse_stopbits(serial_config.get('stopbits', 1)),
                        xonxoff=_as_bool(serial_config.get('xonxoff', False)),
                        rtscts=_as_bool(serial_config.get('rtscts', False)),
                        dsrdtr=_as_bool(serial_config.get('dsrdtr', False)),
                        inter_byte_timeout=serial_config.get('inter_byte_timeout'),
                        hostname=session_config.get('hostname'),
                        username=session_config.get('username'),
                        password=session_config.get('password'),
                        enable_password=session_config.get('enable_password'),
                        username_prompt=session_config.get('username_prompt', 'Username:'),
                        password_prompt=session_config.get('password_prompt', 'Password:'),
                        enable_command=session_config.get('enable_command', 'enable'),
                        user_prompt_suffix=session_config.get('user_prompt_suffix', '>'),
                        privileged_prompt_suffix=session_config.get('privileged_prompt_suffix', '#'),
                        line_ending=session_config.get('line_ending', '\r\n'),
                        command_timeout=session_config.get('command_timeout', 10.0),
                        login_timeout=session_config.get('login_timeout', 15.0),
                        paging_disable_command=session_config.get('paging_disable_command', 'terminal length 0')
                    )

                    # Load commands
                    commands_data = config_data.get('commands', {})
                    for cmd_id, cmd_data in commands_data.items():
                        raw_command = cmd_data.get('command', '')
                        logger.debug(f"Loading command {cmd_id}: {repr(raw_command)}")
                        config.commands[cmd_id] = Command(
                            command=raw_command,
                            need_parse=cmd_data.get('need_parse', False),
                            prompts=cmd_data.get('prompts', [])
                        )
                        logger.debug(f"Loaded command {cmd_id}: {repr(config.commands[cmd_id].command)}")

                    return config
                except Exception as e:
                    logger.warning(f"Error loading config from {path}: {e}")
                    continue

        logger.info("No valid config file found, using defaults")
        return Config()

config = Config()

class SerialConnection:
    """Serial port connection manager."""
    
    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.is_loopback: bool = False
        self.session_ready: bool = False
        self.privileged_mode: bool = False
        self.refresh_config()

    def refresh_config(self) -> None:
        """Refresh runtime settings from the global config."""
        self.baud_rate = config.baud_rate
        self.timeout = config.timeout
        self.read_timeout = config.read_timeout
        self.is_loopback = False
        self.session_ready = False
        self.privileged_mode = False

    def _session_enabled(self) -> bool:
        return any([
            config.hostname,
            config.username,
            config.password,
            config.enable_password,
        ])

    def _configure_windows_port(self, port_name: str) -> None:
        if os.name != 'nt':
            return

        parity_str = "n" if config.parity == serial.PARITY_NONE else config.parity.lower()
        stop_str = "1" if config.stopbits == serial.STOPBITS_ONE else "2" if config.stopbits == serial.STOPBITS_TWO else "1.5"
        xon_str = "on" if config.xonxoff else "off"
        mode_args = [
            'mode',
            port_name,
            f'BAUD={config.baud_rate}',
            f'PARITY={parity_str}',
            f'DATA={int(config.bytesize)}',
            f'STOP={stop_str}',
            f'XON={xon_str}',
            'TO=on',
        ]
        result = subprocess.run(
            mode_args,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        if result.returncode != 0:
            logger.warning(f"mode command failed for {port_name}: {result.stderr or result.stdout}")

    def _connect_with_win32_fallback(self, port_name: str) -> bool:
        if os.name != 'nt' or win32file is None or pywintypes is None:
            return False

        logger.info(f"Falling back to Win32 serial backend for {port_name}")
        self._configure_windows_port(port_name)
        try:
            win32_port = Win32SerialPort(
                port_name, config.timeout, config.read_timeout,
                inter_byte_timeout=config.inter_byte_timeout or 0.1,
            )
            win32_port.open()
            self.serial_port = win32_port
            self.session_ready = False
            self.privileged_mode = False
            logger.info(f"Connected to configured port with Win32 backend: {port_name}")
            return True
        except pywintypes.error as exc:
            logger.error(f"Win32 fallback failed for {port_name}: {exc}")
            return False

    def _known_prompts(self) -> List[str]:
        prompts = []
        if config.hostname:
            prompts.append(f"{config.hostname}{config.user_prompt_suffix}")
            prompts.append(f"{config.hostname}{config.privileged_prompt_suffix}")
        else:
            prompts.append(config.user_prompt_suffix)
            prompts.append(config.privileged_prompt_suffix)
        return prompts

    def _line_is_prompt(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False

        if stripped in self._known_prompts():
            return True

        if config.hostname:
            user_prompt_pattern = rf"^{re.escape(config.hostname)}(?:\([^)]+\))*{re.escape(config.user_prompt_suffix)}$"
            privileged_prompt_pattern = rf"^{re.escape(config.hostname)}(?:\([^)]+\))*{re.escape(config.privileged_prompt_suffix)}$"
            if bool(
                re.match(user_prompt_pattern, stripped)
                or re.match(privileged_prompt_pattern, stripped)
            ):
                return True

        return stripped.endswith(config.user_prompt_suffix) or stripped.endswith(config.privileged_prompt_suffix)

    def _get_prompt_suffix(self, line: str) -> Optional[str]:
        stripped = line.strip()
        if not self._line_is_prompt(stripped):
            return None
        if stripped.endswith(config.privileged_prompt_suffix):
            return config.privileged_prompt_suffix
        if stripped.endswith(config.user_prompt_suffix):
            return config.user_prompt_suffix
        return None

    def _write_text(self, text: str) -> None:
        self._write_payload(text.encode())

    def _write_payload(self, payload: bytes) -> None:
        bytes_written = self.serial_port.write(payload)
        logger.info(f"Wrote {bytes_written} bytes")
        self.serial_port.flush()

    def _write_line(self, text: str) -> None:
        self._write_text(text.rstrip("\r\n") + config.line_ending)

    def _decode_buffer(self, buffer: bytearray) -> str:
        return buffer.decode(errors='ignore').replace('\x00', '')

    def _prompt_detected(self, text: str) -> bool:
        normalized = text.replace('\r', '')
        lines = [line for line in normalized.split('\n') if line.strip()]
        if not lines:
            return False
        return self._line_is_prompt(lines[-1])

    def _interaction_detected(self, text: str) -> bool:
        lowered = text.lower()
        return (
            self._prompt_detected(text)
            or config.username_prompt.lower() in lowered
            or config.password_prompt.lower() in lowered
        )

    def _read_until(self, stop_condition, timeout: float) -> str:
        buffer = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = self.serial_port.read(1)
            if chunk:
                buffer.extend(chunk)
                text = self._decode_buffer(buffer)
                if stop_condition(text):
                    return text
                continue

            waiting = self.serial_port.in_waiting
            if waiting:
                buffer.extend(self.serial_port.read(waiting))
                text = self._decode_buffer(buffer)
                if stop_condition(text):
                    return text
            else:
                time.sleep(0.05)
        return self._decode_buffer(buffer)

    def _read_for(self, duration: float) -> str:
        if duration <= 0:
            return ""

        buffer = bytearray()
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            waiting = self.serial_port.in_waiting
            if waiting:
                buffer.extend(self.serial_port.read(waiting))
                continue

            chunk = self.serial_port.read(1)
            if chunk:
                buffer.extend(chunk)
                continue

            time.sleep(0.05)

        waiting = self.serial_port.in_waiting
        if waiting:
            buffer.extend(self.serial_port.read(waiting))

        return self._decode_buffer(buffer)

    def _read_until_patterns(self, patterns: List[str], timeout: float) -> tuple[Optional[str], str]:
        normalized_patterns = _normalize_patterns(patterns)
        if not normalized_patterns:
            return None, self._read_for(timeout)

        buffer = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            waiting = self.serial_port.in_waiting
            if waiting:
                buffer.extend(self.serial_port.read(waiting))
            else:
                chunk = self.serial_port.read(1)
                if chunk:
                    buffer.extend(chunk)
                else:
                    time.sleep(0.05)

            text = self._decode_buffer(buffer)
            matched_pattern = _find_first_pattern(text, normalized_patterns)
            if matched_pattern:
                return matched_pattern, text

        return None, self._decode_buffer(buffer)

    def _ensure_raw_connection(self) -> None:
        if not self.is_loopback and (not self.serial_port or not self.serial_port.is_open):
            self.connect()

    def _response_text_from_spec(self, spec: Any, transcript: str) -> Optional[str]:
        if isinstance(spec, str):
            return spec

        if not isinstance(spec, dict):
            return str(spec)

        response_text = str(spec.get("text", "")).strip()
        if not response_text:
            return None

        include_patterns = _normalize_patterns(spec.get("if_contains"))
        exclude_patterns = _normalize_patterns(spec.get("unless_contains"))
        lowered_transcript = transcript.lower()

        if include_patterns and not any(pattern.lower() in lowered_transcript for pattern in include_patterns):
            return None

        if exclude_patterns and any(pattern.lower() in lowered_transcript for pattern in exclude_patterns):
            return None

        return response_text

    def send_interactive_command(
        self,
        command_text: str,
        responses: Optional[List[Any]] = None,
        ensure_cli_session: bool = True,
        read_delay: float = 1.0,
        timeout: float = 1.0,
        reset_input: bool = True,
    ) -> str:
        self._ensure_raw_connection()
        if ensure_cli_session:
            self._ensure_cli_session()

        if reset_input:
            try:
                self.serial_port.reset_input_buffer()
            except Exception:
                pass

        transcript_parts: List[str] = []
        self._write_line(command_text)

        initial_output = self._read_for(max(read_delay, 0.1))
        if initial_output:
            transcript_parts.append(initial_output)
        transcript = ''.join(transcript_parts)

        for spec in responses or []:
            response_text = self._response_text_from_spec(spec, transcript)
            if not response_text:
                continue
            self._write_line(response_text)
            response_output = self._read_for(max(read_delay, 0.1))
            if response_output:
                transcript_parts.append(response_output)
                transcript += response_output

        trailing_output = self._read_for(max(timeout, 0.0))
        if trailing_output:
            transcript_parts.append(trailing_output)

        return ''.join(transcript_parts).strip()

    def send_control_keys(
        self,
        sequence: str,
        repeat: int = 1,
        interval_seconds: float = 0.3,
        expect_patterns: Optional[List[str]] = None,
        timeout_seconds: float = 1.0,
        append_line_ending: bool = False,
        reset_input: bool = False,
    ) -> Dict[str, Any]:
        self._ensure_raw_connection()

        payload = _sequence_to_bytes(sequence)
        if append_line_ending:
            payload += config.line_ending.encode()
        if not payload:
            raise ValueError("Control sequence is empty")

        if reset_input:
            try:
                self.serial_port.reset_input_buffer()
            except Exception:
                pass

        transcript_parts: List[str] = []
        matched_pattern: Optional[str] = None
        repeat = max(1, int(repeat))
        interval_seconds = max(0.0, float(interval_seconds))
        timeout_seconds = max(0.0, float(timeout_seconds))

        for attempt in range(repeat):
            self._write_payload(payload)
            wait_timeout = timeout_seconds if attempt == repeat - 1 else max(interval_seconds, 0.1)

            if expect_patterns:
                matched_pattern, console_output = self._read_until_patterns(expect_patterns, wait_timeout)
            else:
                console_output = self._read_for(wait_timeout)

            if console_output:
                transcript_parts.append(console_output)

            if matched_pattern:
                break

            if interval_seconds > 0 and attempt < repeat - 1:
                time.sleep(interval_seconds)

        return {
            "matched_pattern": matched_pattern,
            "transcript": ''.join(transcript_parts).strip(),
        }

    def reconnect_until(self, timeout_seconds: float, interval_seconds: float = 2.0) -> str:
        deadline = time.monotonic() + max(timeout_seconds, 1.0)
        attempts: List[str] = []

        while time.monotonic() < deadline:
            try:
                self.close()
            except Exception:
                pass

            time.sleep(0.5)
            try:
                if self.connect():
                    port_name = getattr(self.serial_port, 'name', getattr(self.serial_port, 'port', config.port or 'unknown'))
                    attempts.append(f"Reconnected to {port_name}")
                    return '\n'.join(attempts)
            except Exception as exc:
                attempts.append(f"Reconnect failed: {exc}")

            time.sleep(max(interval_seconds, 0.2))

        raise ValueError("Timed out waiting for serial reconnect\n" + '\n'.join(attempts))

    def auto_factory_reset(
        self,
        profile_name: str,
        warm_reboot: bool = True,
        interrupt_sequence: Optional[str] = None,
        bootloader_entry_sequence: Optional[str] = None,
        bootloader_command: Optional[str] = None,
        bootloader_reboot_sequence: Optional[str] = None,
        timeout_seconds: float = 180.0,
    ) -> str:
        profile_key = str(profile_name or '').strip().lower()
        if profile_key not in _BOOTLOADER_RESET_PROFILES:
            raise ValueError(
                "Unknown reset profile. Available profiles: "
                + ', '.join(sorted(_BOOTLOADER_RESET_PROFILES.keys()))
            )

        profile = _BOOTLOADER_RESET_PROFILES[profile_key]
        transcript_parts = [
            f"Profile: {profile_key}",
            f"Description: {profile.get('description', '')}".strip(),
        ]

        self._ensure_raw_connection()

        if warm_reboot and profile.get("warm_reboot_step"):
            warm_step = profile["warm_reboot_step"]
            warm_output = self.send_interactive_command(
                warm_step["command"],
                responses=warm_step.get("responses"),
                ensure_cli_session=warm_step.get("ensure_cli_session", True),
                read_delay=float(warm_step.get("read_delay", 1.0)),
                timeout=float(warm_step.get("timeout", 1.0)),
            )
            transcript_parts.append(f"Warm reboot step [{warm_step['command']}]:\n{warm_output}".strip())
            self.session_ready = False
            self.privileged_mode = False

        interrupt = interrupt_sequence or profile.get("interrupt_sequence")
        bootloader_entry = bootloader_entry_sequence if bootloader_entry_sequence is not None else profile.get("bootloader_entry_sequence")
        bootloader_prompts = _normalize_patterns(profile.get("bootloader_prompt_patterns"))
        boot_menu_patterns = _normalize_patterns(profile.get("boot_menu_patterns"))
        per_attempt_timeout = float(profile.get("interrupt_timeout_per_attempt", 0.8))
        interrupt_interval = float(profile.get("interrupt_interval", 0.3))

        if not interrupt:
            raise ValueError("Reset profile does not define an interrupt sequence")

        deadline = time.monotonic() + max(timeout_seconds, 1.0)
        boot_menu_seen = False
        bootloader_matched = None
        boot_transcript_parts: List[str] = []

        while time.monotonic() < deadline:
            current_sequence = bootloader_entry if boot_menu_seen and bootloader_entry else interrupt
            expect_patterns = bootloader_prompts + ([] if boot_menu_seen else boot_menu_patterns)
            result = self.send_control_keys(
                current_sequence,
                repeat=1,
                interval_seconds=0.0,
                expect_patterns=expect_patterns,
                timeout_seconds=per_attempt_timeout,
                append_line_ending=False,
                reset_input=False,
            )

            if result["transcript"]:
                boot_transcript_parts.append(result["transcript"])

            matched_pattern = result["matched_pattern"]
            if matched_pattern and matched_pattern in bootloader_prompts:
                bootloader_matched = matched_pattern
                break

            if matched_pattern and matched_pattern in boot_menu_patterns:
                boot_menu_seen = True

            time.sleep(max(interrupt_interval, 0.05))

        if not bootloader_matched:
            transcript_parts.append("Boot transcript:\n" + ''.join(boot_transcript_parts).strip())
            raise ValueError("Failed to detect bootloader prompt while sending control sequences")

        transcript_parts.append(f"Bootloader prompt matched: {bootloader_matched}")
        boot_transcript = ''.join(boot_transcript_parts).strip()
        if boot_transcript:
            transcript_parts.append("Boot transcript:\n" + boot_transcript)

        selected_bootloader_command = bootloader_command or profile.get("bootloader_command")
        if selected_bootloader_command:
            bootloader_output = self.send_interactive_command(
                selected_bootloader_command,
                responses=profile.get("bootloader_responses"),
                ensure_cli_session=False,
                read_delay=float(profile.get("bootloader_read_delay", 0.8)),
                timeout=float(profile.get("bootloader_timeout", 1.5)),
            )
            transcript_parts.append(
                f"Bootloader step [{selected_bootloader_command}]:\n{bootloader_output}".strip()
            )

        selected_bootloader_reboot = bootloader_reboot_sequence
        if selected_bootloader_reboot is None:
            selected_bootloader_reboot = profile.get("bootloader_reboot_sequence")

        if selected_bootloader_reboot:
            reboot_output = self.send_interactive_command(
                selected_bootloader_reboot,
                responses=profile.get("bootloader_reboot_responses"),
                ensure_cli_session=False,
                read_delay=float(profile.get("bootloader_reboot_read_delay", 0.8)),
                timeout=float(profile.get("bootloader_reboot_timeout", 1.5)),
            )
            transcript_parts.append(
                f"Bootloader reboot step [{selected_bootloader_reboot}]:\n{reboot_output}".strip()
            )

        if profile.get("wait_for_reconnect_after_bootloader", True):
            reconnect_output = self.reconnect_until(float(profile.get("reconnect_timeout", 180.0)))
            transcript_parts.append(reconnect_output)

        for index, step in enumerate(profile.get("post_boot_steps", []), start=1):
            step_output = self.send_interactive_command(
                step["command"],
                responses=step.get("responses"),
                ensure_cli_session=step.get("ensure_cli_session", True),
                read_delay=float(step.get("read_delay", 1.0)),
                timeout=float(step.get("timeout", 1.0)),
            )
            transcript_parts.append(f"Post step {index} [{step['command']}]:\n{step_output}".strip())
            if step.get("disconnect_after"):
                self.session_ready = False
                self.privileged_mode = False

        return '\n\n'.join(part for part in transcript_parts if part)

    def _detect_session_state(self, text: str) -> str:
        normalized = text.replace('\r', '')
        lines = [line for line in normalized.split('\n') if line.strip()]
        if lines:
            prompt_suffix = self._get_prompt_suffix(lines[-1])
            if prompt_suffix == config.privileged_prompt_suffix:
                return "privileged"
            if prompt_suffix == config.user_prompt_suffix:
                return "user"

        normalized = normalized.rstrip()
        lowered = normalized.lower()
        if config.username_prompt.lower() in lowered:
            return "username"
        if config.password_prompt.lower() in lowered:
            return "password"
        return "unknown"

    def _strip_cli_output(self, text: str, command_text: str) -> str:
        lines = text.replace('\r', '').split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)

        if lines:
            first_line = lines[0].strip()
            command_text = command_text.strip()
            if (
                first_line == command_text
                or re.match(rf"^.*[>#]\s*{re.escape(command_text)}$", first_line)
            ):
                lines.pop(0)

        while lines and not lines[-1].strip():
            lines.pop()

        if lines and self._line_is_prompt(lines[-1]):
            lines.pop()

        return '\n'.join(lines).strip()

    def _send_cli_command(self, command_text: str, timeout: Optional[float] = None) -> str:
        self._ensure_cli_session()
        self.serial_port.reset_input_buffer()
        self._write_line(command_text)
        raw_output = self._read_until(self._prompt_detected, timeout or config.command_timeout)
        logger.info(f"CLI raw response: {raw_output!r}")
        return self._strip_cli_output(raw_output, command_text)

    def _ensure_cli_session(self) -> None:
        if not self._session_enabled() or self.session_ready:
            return

        enable_pending = False
        transcript = ""
        for _ in range(8):
            if not transcript:
                self.serial_port.reset_input_buffer()
                self._write_text(config.line_ending)
                transcript = self._read_until(self._interaction_detected, config.login_timeout)

            state = self._detect_session_state(transcript)
            logger.info(f"Console session state: {state}")
            logger.debug(f"Console transcript: {transcript!r}")

            if state == "privileged":
                self.session_ready = True
                self.privileged_mode = True
                break

            if state == "user":
                self.session_ready = True
                self.privileged_mode = False
                if config.enable_password:
                    enable_pending = True
                    self._write_line(config.enable_command)
                    transcript = self._read_until(self._interaction_detected, config.login_timeout)
                    continue
                break

            if state == "username":
                if not config.username:
                    raise ValueError("Username prompt received but username is not configured")
                self._write_line(config.username)
                transcript = self._read_until(self._interaction_detected, config.login_timeout)
                continue

            if state == "password":
                secret = config.enable_password if enable_pending else config.password
                if not secret:
                    raise ValueError("Password prompt received but password is not configured")
                self._write_line(secret)
                enable_pending = False
                transcript = self._read_until(self._interaction_detected, config.login_timeout)
                continue

            self._write_text(config.line_ending)
            transcript = self._read_until(self._interaction_detected, config.login_timeout)

        if not self.session_ready:
            raise ValueError("Unable to reach a usable device prompt over the serial console")

        if self.privileged_mode and config.paging_disable_command:
            try:
                self._send_cli_command(config.paging_disable_command, timeout=config.command_timeout)
            except Exception as exc:
                logger.warning(f"Failed to disable paging: {exc}")

    def connect(self) -> bool:
        """Attempt to connect to an available serial port."""
        try:
            # 检查是否为回环模式
            if config.port == "LOOP_BACK":
                logger.info("Using LOOP_BACK mode")
                self.is_loopback = True
                return True

            # 如果已经连接，直接返回
            if self.serial_port and self.serial_port.is_open:
                logger.debug("Using existing serial connection")
                return True

            # 关闭可能存在的连接
            if self.serial_port:
                try:
                    self.serial_port.close()
                except Exception:
                    pass
                self.serial_port = None

            # 尝试连接指定端口
            if config.port:
                logger.info(f"Attempting to connect to configured port: {config.port}")
                try:
                    self.serial_port = serial.Serial(
                        port=config.port,
                        baudrate=config.baud_rate,
                        bytesize=config.bytesize,
                        parity=config.parity,
                        stopbits=config.stopbits,
                        timeout=config.timeout,
                        write_timeout=config.timeout,
                        xonxoff=config.xonxoff,
                        rtscts=config.rtscts,
                        dsrdtr=config.dsrdtr,
                        inter_byte_timeout=config.inter_byte_timeout
                    )
                    self.session_ready = False
                    self.privileged_mode = False
                    logger.info(f"Connected to configured port: {config.port}")
                    return True
                except serial.SerialException as e:
                    if self._connect_with_win32_fallback(config.port):
                        return True
                    logger.error(f"Failed to connect to configured port {config.port}: {str(e)}")
                    raise ValueError(f"Serial port {config.port} not available: {str(e)}")

            # 搜索可用端口
            logger.info("No port configured, searching for available ports...")
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                logger.error("No serial ports found")
                raise ValueError("No serial ports available")

            logger.info(f"Found ports: {', '.join(p.device for p in ports)}")
            for port in ports:
                try:
                    self.serial_port = serial.Serial(
                        port=port.device,
                        baudrate=config.baud_rate,
                        bytesize=config.bytesize,
                        parity=config.parity,
                        stopbits=config.stopbits,
                        timeout=config.timeout,
                        write_timeout=config.timeout,
                        xonxoff=config.xonxoff,
                        rtscts=config.rtscts,
                        dsrdtr=config.dsrdtr,
                        inter_byte_timeout=config.inter_byte_timeout
                    )
                    self.session_ready = False
                    self.privileged_mode = False
                    logger.info(f"Connected to port: {port.device}")
                    return True
                except serial.SerialException:
                    if self._connect_with_win32_fallback(port.device):
                        return True
                    continue

            raise ValueError("Failed to connect to any available serial port")

        except Exception as e:
            logger.error(f"Unexpected error in connect: {str(e)}")
            raise ValueError(f"Connection error: {str(e)}")

    def send_command(self, command: Command, arguments: Dict[str, Any]) -> list[types.TextContent]:
        """Send a command to the serial port and return result according to MCP protocol."""
        try:
            # 确保连接
            if not self.is_loopback and (not self.serial_port or not self.serial_port.is_open):
                logger.info("No active connection, attempting to connect...")
                if not self.connect():
                    error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Failed to establish serial connection.\n"
                    error_msg += "Please check:\n"
                    error_msg += "1. Serial port is correctly configured in config.yaml\n"
                    error_msg += "2. Device is properly connected\n"
                    error_msg += "3. No other program is using the port"
                    return [types.TextContent(
                        type="text",
                        text=error_msg
                    )]

            # 准备命令
            cmd_str = command.command.format(**arguments)

            if not self.is_loopback and self._session_enabled():
                response_text = self._send_cli_command(cmd_str)
                if command.need_parse:
                    return [types.TextContent(
                        type="text",
                        text=response_text or "Command executed successfully."
                    )]
                return []

            # 确保命令以\r\n结尾
            cmd_str = cmd_str.rstrip() + '\r\n'  # 移除可能的空白字符，强制添加\r\n

            cmd_bytes = cmd_str.encode()
            logger.info(f"Sending command: {cmd_str.strip()}")
            logger.info(f"Command bytes ({len(cmd_bytes)} bytes): {' '.join([f'0x{b:02X}' for b in cmd_bytes])}")

            if self.is_loopback:
                # 回环模式：直接返回发送的命令和OK响应
                responses = [
                    cmd_str.encode(),  # 命令回显
                    f"{config.response_start_string}\r\n".encode()  # OK响应
                ]
            else:
                # 清空缓冲区
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()

                # 发送命令
                bytes_written = self.serial_port.write(cmd_bytes)
                logger.info(f"Wrote {bytes_written} bytes")
                self.serial_port.flush()

                # 等待一段时间确保命令被处理
                time.sleep(0.1)

                # 读取所有响应
                responses = []
                while self.serial_port.in_waiting:
                    response = self.serial_port.readline()
                    logger.info(f"Raw response: {response}")
                    if response:
                        responses.append(response)

            if not responses:
                logger.error("No response received within timeout")
                error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Command timeout - no response within {self.read_timeout} second(s)\n"
                error_msg += f"Command sent: {cmd_str.strip()}\n"
                error_msg += f"Command bytes ({len(cmd_bytes)} bytes): {' '.join([f'0x{b:02X}' for b in cmd_bytes])}\n"
                error_msg += "Please check:\n"
                error_msg += "1. Device is powered and responding\n"
                error_msg += "2. Baud rate matches device settings\n"
                error_msg += "3. Serial connection is stable\n"
                return [types.TextContent(
                    type="text",
                    text=error_msg
                )]

            # 解码第一行响应
            first_response = responses[0]
            first_line = first_response.decode().strip()
            logger.info(f"Decoded first response: {first_line}")

            # 检查是否有第二行响应
            if len(responses) > 1:
                second_response = responses[1]
                if second_response.startswith(config.response_start_string.encode()):  # 使用配置的应答开始字符串
                    if command.need_parse:
                        return [types.TextContent(
                            type="text",
                            text=second_response.decode().strip()
                        )]
                    return []

            # 如果响应不是预期的格式，返回详细的错误信息
            error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Command execution failed.\n"
            error_msg += f"Command sent: {cmd_str.strip()}\n"
            error_msg += f"Command bytes ({len(cmd_bytes)} bytes): {' '.join([f'0x{b:02X}' for b in cmd_bytes])}\n"
            error_msg += "Responses received:\n"
            for i, resp in enumerate(responses, 1):
                error_msg += f"{i}. Raw: {resp!r}\n   Decoded: {resp.decode().strip()}\n"
            error_msg += "\nPossible reasons:\n"
            error_msg += f"- Device echoed the command but did not send {config.response_start_string} response\n"
            error_msg += "- Command format may be incorrect\n"
            error_msg += "- Device may be in wrong mode\n"
            return [types.TextContent(
                type="text",
                text=error_msg
            )]

        except serial.SerialTimeoutException as e:
            logger.error(f"Serial timeout: {str(e)}")
            error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Command timeout - {str(e)}\n"
            error_msg += "Please check:\n"
            error_msg += "1. Device is powered and responding\n"
            error_msg += "2. Baud rate matches device settings\n"
            error_msg += "3. Device is not busy with other operations"
            return [types.TextContent(
                type="text",
                text=error_msg
            )]
        except serial.SerialException as e:
            logger.error(f"Serial error: {str(e)}")
            error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Serial communication failed - {str(e)}\n"
            error_msg += "Please check:\n"
            error_msg += "1. Serial port is correctly configured in config.yaml\n"
            error_msg += "2. Device is properly connected\n"
            error_msg += "3. No other program is using the port"
            return [types.TextContent(
                type="text",
                text=error_msg
            )]

    def close(self) -> None:
        """Close the serial port connection if open."""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                logger.info(f"Closed serial port connection: {self.serial_port.port}")
            except Exception as e:
                logger.error(f"Error closing port: {str(e)}")
            self.serial_port = None
        self.session_ready = False
        self.privileged_mode = False

serial_connection = SerialConnection()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for the MCP service."""
    logger.info("Listing available tools")
    tools = []

    tools.append(types.Tool(
        name="send_control_keys",
        description="Send raw control keys or raw bytes over the serial console, such as Ctrl+C, Ctrl+B, Ctrl+Q.",
        inputSchema={
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Control-key sequence, for example Ctrl+C or Ctrl+B,Ctrl+Q"},
                "repeat": {"type": "integer", "description": "How many times to send the sequence", "default": 1},
                "interval_seconds": {"type": "number", "description": "Delay between repeated sends", "default": 0.3},
                "expect_patterns": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"}
                    ],
                    "description": "Optional text patterns to wait for after sending"
                },
                "timeout_seconds": {"type": "number", "description": "How long to wait for console output after each send", "default": 1.0},
                "append_line_ending": {"type": "boolean", "description": "Append configured CRLF after the payload", "default": False},
                "reset_input": {"type": "boolean", "description": "Clear pending input before sending", "default": False},
            },
            "required": ["sequence"]
        },
        prompts=[
            "向当前设备发送 Ctrl+C",
            "向当前设备连续发送 Ctrl+B, Ctrl+Q 并等待 BootLoader 菜单",
            "在当前串口上发送控制键并等待 bootloader 提示符",
        ]
    ))

    tools.append(types.Tool(
        name="auto_factory_reset",
        description="Try to automate a BootLoader-based factory reset workflow, including control-key injection and post-boot cleanup.",
        inputSchema={
            "type": "object",
            "properties": {
                "profile": {
                    "type": "string",
                    "enum": ["router", "switch", "ws6008", "gateway"],
                    "description": "Reset workflow profile"
                },
                "warm_reboot": {"type": "boolean", "description": "Trigger a CLI reload before injecting bootloader keys", "default": True},
                "interrupt_sequence": {"type": "string", "description": "Override default boot interrupt keys"},
                "bootloader_entry_sequence": {"type": "string", "description": "Override boot-menu to bootloader keys, such as Ctrl+Q"},
                "bootloader_command": {"type": "string", "description": "Override bootloader command, such as delete config.text"},
                "bootloader_reboot_sequence": {"type": "string", "description": "Override bootloader reboot command, such as reboot"},
                "timeout_seconds": {"type": "number", "description": "Max time to wait for bootloader interception", "default": 180.0},
            },
            "required": ["profile"]
        },
        prompts=[
            "自动通过 BootLoader 恢复当前路由器出厂设置",
            "自动通过 Ctrl+B 和 Ctrl+Q 进入 bootloader 并恢复当前交换机出厂设置",
            "对当前 WS6008 执行自动 BootLoader 重置",
        ]
    ))
    
    for cmd_id, command in config.commands.items():
        param_names = re.findall(r'\{(\w+)\}', command.command)
        properties = {name: {"type": "string"} for name in param_names}
        
        tools.append(types.Tool(
            name=cmd_id,
            description=f"Execute {cmd_id} command",
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": param_names
            },
            prompts=command.prompts
        ))
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool execution requests according to MCP protocol."""
    logger.info(f"Tool call received - Name: {name}, Arguments: {arguments}")
    
    try:
        if arguments is None:
            arguments = {}

        if name == "send_control_keys":
            result = serial_connection.send_control_keys(
                sequence=str(arguments.get("sequence", "")),
                repeat=int(arguments.get("repeat", 1)),
                interval_seconds=float(arguments.get("interval_seconds", 0.3)),
                expect_patterns=_normalize_patterns(arguments.get("expect_patterns")),
                timeout_seconds=float(arguments.get("timeout_seconds", 1.0)),
                append_line_ending=_as_bool(arguments.get("append_line_ending", False)),
                reset_input=_as_bool(arguments.get("reset_input", False)),
            )
            text = (
                f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Raw key sequence sent.\n"
                f"Matched pattern: {result.get('matched_pattern') or 'none'}\n"
                f"Transcript:\n{result.get('transcript') or '(no output)'}"
            )
            return [types.TextContent(type="text", text=text)]

        if name == "auto_factory_reset":
            result_text = serial_connection.auto_factory_reset(
                profile_name=str(arguments.get("profile", "")),
                warm_reboot=_as_bool(arguments.get("warm_reboot", True)),
                interrupt_sequence=arguments.get("interrupt_sequence"),
                bootloader_entry_sequence=arguments.get("bootloader_entry_sequence"),
                bootloader_command=arguments.get("bootloader_command"),
                bootloader_reboot_sequence=arguments.get("bootloader_reboot_sequence"),
                timeout_seconds=float(arguments.get("timeout_seconds", 180.0)),
            )
            return [types.TextContent(
                type="text",
                text=f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Auto factory reset workflow finished.\n\n{result_text}"
            )]

        if name not in config.commands:
            error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Error: Unknown tool '{name}'\n"
            error_msg += "Please check:\n"
            error_msg += "1. Tool name is correct\n"
            error_msg += "2. Tool is configured in config.yaml"
            return [types.TextContent(
                type="text",
                text=error_msg
            )]
        command = config.commands[name]
        
        # 发送命令并返回 MCP 格式的响应
        return serial_connection.send_command(command, arguments)

    except Exception as e:
        logger.error(f"Error handling tool call: {str(e)}")
        error_msg = f"[{PROJECT_DISPLAY_NAME} v{VERSION}] Error: {str(e)}\n"
        error_msg += "Please check:\n"
        error_msg += "1. Configuration is correct\n"
        error_msg += "2. Device is functioning properly"
        return [types.TextContent(
            type="text",
            text=error_msg
        )]

async def main(config_name: str = None) -> None:
    """Run the MCP server.
    
    Args:
        config_name: Optional configuration name. If not provided, uses default config.yaml
    """
    logger.info(f"Starting {PROJECT_DISPLAY_NAME} server")
    
    # 处理配置文件名
    if config_name and config_name != "default":
        if not config_name.lower().endswith((".yaml", ".yml")):
            config_name = f"{config_name}_config.yaml"
    else:
        config_name = DEFAULT_CONFIG_FILES[0]
        
    # 加载配置
    global config
    config = Config.load(config_name)
    serial_connection.refresh_config()
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=PROJECT_IDENTIFIER,
                    server_version=VERSION,
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        serial_connection.close()

if __name__ == "__main__":
    config_name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(config_name))
