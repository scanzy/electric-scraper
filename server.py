"""MCP server entry point."""

from fastmcp import FastMCP

from src.config import ReadConfig, WriteConfig
from src.scraper import ScrapeComponents


mcp = FastMCP(
    name="Electric Components Scraper",
    dependencies=["fastmcp", "selenium", "requests", "html2text"],
)

# MCP tools
mcp.tool("scrape_components")(ScrapeComponents)
mcp.tool("read_config")(ReadConfig)
mcp.tool("write_config")(WriteConfig)


# server entry point
if __name__ == "__main__":
    mcp.run()
