# ====================================================
# Project: NSM-DEBUG_MCP
# Description: Visual Studio Code oriented MCP entrypoint.
# License: MIT License
# ====================================================
from . import server
import argparse
import asyncio


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='NSM-DEBUG_MCP Server')
    parser.add_argument(
        'config',
        nargs='?',
        default=None,
        help='YAML config path or config name'
    )
    parser.add_argument(
        '--config',
        dest='config_option',
        default=None,
        help='YAML config path or config name'
    )
    args = parser.parse_args()
    asyncio.run(server.main(args.config_option or args.config))


# Expose important items at package level
__version__ = "0.6.0"
__all__ = ['main', 'server']
