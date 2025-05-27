from mcp.server.fastmcp import FastMCP
import random
import requests
from crawl4ai import AsyncWebCrawler

mcp = FastMCP("Echo Server")

@mcp.tool()
async def get_current_weather(city: str) -> str:
    print(f"[debug-server] get_current_weather({city})")
    endpoint = "https://wttr.in"
    response = requests.get(f"{endpoint}/{city}")
    return response.text



@mcp.tool()
async def crawl_website(url: str) -> str:
    print(f"[debug-server] crawl_website({url})")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown

if __name__ == "__main__":
    mcp.run(transport="streamable-http")