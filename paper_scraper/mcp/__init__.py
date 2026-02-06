"""MCP (Model Context Protocol) server for Paper Scraper.

Enables AI agents like Claude Code to interact with the Paper Scraper API.
"""

from paper_scraper.mcp.server import create_mcp_app

__all__ = ["create_mcp_app"]
