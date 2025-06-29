from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import uvicorn
import os
import asyncio

load_dotenv()

app = FastAPI(title="Quality Assurance Agent Server", version="1.0.0")

# Global crawler instance
crawler = None
crawler_lock = asyncio.Lock()

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

class YouTubeTranscriptRequest(BaseModel):
    url: str

class YouTubeTranscriptResponse(BaseModel):
    transcript: list
    video_id: str
    url: str
    language: str

async def get_crawler():
    """Get or create the global crawler instance"""
    global crawler
    async with crawler_lock:
        if crawler is None:
            crawler = AsyncWebCrawler()
            await crawler.start()
        return crawler

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website and return its markdown content
    """
    try:
        print(f"[debug-server] crawl_website({request.url})")
        crawler_instance = await get_crawler()
        result = await crawler_instance.arun(url=request.url)
        return CrawlResponse(
            markdown_content=result.markdown,
            url=request.url
        )
    except Exception as e:
        print(f"[debug-server] Error crawling website: {str(e)}")
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
        print(f"[debug-server] Error running browser agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running browser agent: {str(e)}")

@app.post("/youtube-transcript", response_model=YouTubeTranscriptResponse)
async def youtube_transcript(request: YouTubeTranscriptRequest):
    """
    Extract transcript from a YouTube video URL
    """
    try:
        print(f"[debug-server] youtube_transcript({request.url})")
        
        # Parse the URL
        parsed_url = urlparse(request.url)
        # Extract URL parameters
        query_params = parse_qs(parsed_url.query)
        # Get the 'v' parameter value
        video_id = query_params.get("v", [None])[0]
        
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL. Could not extract video ID.")
        
        # Fetch transcript
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        
        # Get raw data
        data = fetched_transcript.to_raw_data()
        
        # Process the transcript data to add end times
        for i in range(len(data) - 1):
            data[i]['end'] = data[i + 1]['start']
        
        # Last element: end = start + duration
        data[-1]['end'] = data[-1]['start'] + data[-1]['duration']
        
        return YouTubeTranscriptResponse(
            transcript=data,
            video_id=video_id,
            url=request.url,
            language=fetched_transcript.language_code
        )
    except Exception as e:
        print(f"[debug-server] Error extracting YouTube transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting YouTube transcript: {str(e)}")

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
            "browser_agent": "/browser-agent - POST - Run browser agent",
            "youtube_transcript": "/youtube-transcript - POST - Extract YouTube video transcript"
        }
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the server shuts down"""
    global crawler
    if crawler:
        await crawler.close()

if __name__ == "__main__":
    # Get host and port from environment variables with defaults
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port)