"""MCP server entry point."""

import glob
from pathlib import Path
from fastmcp import FastMCP

from src.config import ReadConfig, WriteConfig
from src.scraper import ScrapeComponents


def ReadDocs():
    """Reads the documentation of the MCP server,
    including details about the configuration file.
    """

    readmePath = Path(__file__).parent / "DOCS.md"
    with open(readmePath, "r", encoding="utf-8") as file:
        return file.read()


def ReadNewWebsiteGuide(step: int = 0) -> str:
    """Reads the guide to configure a new website. Start with step 0."""
    
    guidePath = Path(__file__).parent / "src" / "guide" / f"{step}_*.md"
    with open(glob.glob(str(guidePath))[0], "r", encoding="utf-8") as file:
        return file.read()


mcp = FastMCP(
    name="Electric Components Scraper",
    dependencies=["fastmcp", "selenium", "requests", "html2text", "ddgs"],
)

# MCP tools
mcp.tool("scrape_components")(ScrapeComponents)
mcp.tool("read_config")(ReadConfig)
mcp.tool("write_config")(WriteConfig)
mcp.tool("read_docs")(ReadDocs)
mcp.tool("read_new_website_guide")(ReadNewWebsiteGuide)

# server entry point
if __name__ == "__main__":
    mcp.run()
