import sys
import asyncio
import pathlib as pl

from fastmcp.client import Client

# adds the parent directory to the path
# this allows to run tests with the IDE play button
sys.path.append(str(pl.Path(__file__).parent.parent))


async def RunTests() -> None:
    """Run tests for database operations using MCP."""

    # run the MCP server in the background
    from server import mcp

    # create a client to connect to the MCP server
    async with Client(mcp) as mcpClient:

        await TestScrapeFromWebsite(mcpClient)
        await TestScrapeFromKeywords(mcpClient)
        await TestScrapeFromWebSearch(mcpClient)
        await TestScrapeNotFound(mcpClient)


async def TestScrapeFromWebsite(mcpClient: Client) -> None:
    result = await mcpClient.call_tool("scrape_components",
        {"manuCodes": ["428160212"], "hints": ["molex.com"], "files": [], "closeBrowser": True})
    print(result)


async def TestScrapeFromKeywords(mcpClient: Client) -> None:
    result = await mcpClient.call_tool("scrape_components",
        {"manuCodes": ["428160212"], "hints": ["molex"], "files": [], "closeBrowser": True})
    print(result)


async def TestScrapeFromWebSearch(mcpClient: Client) -> None:
    result = await mcpClient.call_tool("scrape_components",
        {"manuCodes": ["428160212"], "hints": ["connect"], "files": [], "closeBrowser": True})
    print(result)


async def TestScrapeNotFound(mcpClient: Client) -> None:
    result = await mcpClient.call_tool("scrape_components",
        {"manuCodes": ["missing"], "hints": ["molex"], "files": [], "closeBrowser": True})
    print(result)



if __name__ == "__main__":
    asyncio.run(RunTests())
