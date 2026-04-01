import asyncio
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PACKAGE_ROOT, "src")
CONFIG_PATH = os.path.join(PACKAGE_ROOT, "NSM-DEBUG_MCP.example.yaml")

sys.path.insert(0, SRC_DIR)

from nsm_debug_mcp import server as s


def main():
    s.config = s.Config.load(CONFIG_PATH)
    s.serial_connection.refresh_config()
    tools = asyncio.run(s.handle_list_tools())
    for tool in tools:
        print(tool.name)


if __name__ == "__main__":
    main()