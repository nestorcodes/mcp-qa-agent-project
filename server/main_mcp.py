from mcp.server.fastmcp import FastMCP
import random
import requests
from crawl4ai import AsyncWebCrawler
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Echo Server")



@mcp.tool()
async def crawl_website(url: str) -> str:
    print(f"[debug-server] crawl_website({url})")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown

@mcp.tool()
async def browser_use(task: str) -> str:
    print(f"[debug-server] browser_use({task})")
    llm = ChatOpenAI(model="gpt-4")
    agent = Agent(
        task="Entra a comparasoftware.com y compara los precios de los productos",
        llm=llm,
    )
    result = await agent.run()
    return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http")