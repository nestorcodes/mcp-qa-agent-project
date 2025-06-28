from mcp.server.fastmcp import FastMCP
import random
import requests
from crawl4ai import AsyncWebCrawler
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
import asyncio

load_dotenv()

mcp = FastMCP("Quality Assurance Agent Server")

# Global crawler instance
crawler = None
crawler_lock = asyncio.Lock()

async def get_crawler():
    """Get or create the global crawler instance"""
    global crawler
    async with crawler_lock:
        if crawler is None:
            crawler = AsyncWebCrawler()
            await crawler.start()
        return crawler

@mcp.tool()
async def crawl_website(url: str) -> str:
    print(f"[debug-server] crawl_website({url})")
    try:
        crawler_instance = await get_crawler()
        result = await crawler_instance.arun(url=url)
        return result.markdown
    except Exception as e:
        print(f"[debug-server] Error crawling website: {str(e)}")
        raise e

@mcp.tool()
async def browser_agent(prompt: str) -> str:
    print(f"[debug-server] browser_agent({prompt})")
    try:
        llm = ChatOpenAI(model="gpt-4o")
        agent = Agent(
            task=prompt,
            llm=llm,
        )
        result = await agent.run()
        print(result)
        return result.final_result()
    except Exception as e:
        print(f"[debug-server] Error running browser agent: {str(e)}")
        raise e

# Cleanup function for when the MCP server shuts down
async def cleanup():
    global crawler
    if crawler:
        await crawler.close()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")