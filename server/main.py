from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Quality Assurance Agent Server", version="1.0.0")

class CrawlRequest(BaseModel):
    url: str

class CrawlResponse(BaseModel):
    markdown_content: str
    url: str

class BrowserAgentRequest(BaseModel):
    prompt: str

class BrowserAgentResponse(BaseModel):
    result: str
    prompt: str

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website and return its markdown content
    """
    try:
        print(f"[debug-server] crawl_website({request.url})")
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=request.url)
            return CrawlResponse(
                markdown_content=result.markdown,
                url=request.url
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error crawling website: {str(e)}")

@app.post("/browser-agent", response_model=BrowserAgentResponse)
async def browser_agent(request: BrowserAgentRequest):
    """
    Run a browser agent with the given prompt
    """
    try:
        print(f"[debug-server] browser_agent({request.prompt})")
        llm = ChatOpenAI(model="gpt-4o")
        agent = Agent(
            task=request.prompt,
            llm=llm
        )
        result = await agent.run()
        print(result.final_result())
        return BrowserAgentResponse(
            result=result.final_result(),
            prompt=request.prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running browser agent: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Quality Assurance Agent Server",
        "version": "1.0.0",
        "endpoints": {
            "crawl": "/crawl - POST - Crawl a website",
            "browser_agent": "/browser-agent - POST - Run browser agent"
        }
    }



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)