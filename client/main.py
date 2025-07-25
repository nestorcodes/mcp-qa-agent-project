import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import requests
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Load environment variables
load_dotenv()

# Pydantic model for request
class PromptRequest(BaseModel):
    prompt: str

# Pydantic model for response
class PromptResponse(BaseModel):
    status: str
    console_logs: str

# Create FastAPI app
app = FastAPI(
    title="QA Agent API",
    description="API for Quality Assurance agent that processes prompts and returns test results",
    version="1.0.0"
)

# Add CORS middleware to allow fetch requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get API key from environment
QA_API_KEY_CLIENT = os.getenv("QA_API_KEY_CLIENT")
if not QA_API_KEY_CLIENT:
    raise ValueError("QA_API_KEY_CLIENT not found in environment variables")

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify the API key from the request header."""
    if x_api_key != QA_API_KEY_CLIENT:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key

class QAAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Get server configuration from environment variables
        # Always use localhost for server connection to avoid connection issues
        self.server_host = os.getenv("CLIENT_HOST", "localhost")
        self.server_port = os.getenv("CLIENT_PORT", "8000")
        self.server_url = f"http://{self.server_host}:{self.server_port}"
        
        # QA API key for server authentication
        self.qa_api_key = os.getenv("QA_API_KEY")
        if not self.qa_api_key:
            raise ValueError("QA_API_KEY not found in environment variables")
        
        # create llm
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo-1106",
            temperature=0,
            api_key=self.api_key
        )

        # create tools with functions and description
        self.tools = [
            Tool(
                name="crawl_website",
                func=self.crawl_website,
                description="Crawls a website and returns its content in markdown format. Use this to analyze website content, structure, and verify content integrity."
            ),
            Tool(
                name="browser_agent",
                func=self.browser_agent,
                description="Runs a browser automation agent to test user flows, interactions, and validate critical functionality. Use this for testing user journeys and interactive elements."
            )
        ]

        # define main prompt for QA agent
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Quality Assurance agent specialized in software testing and quality control. Your primary responsibilities include:

1. Analyzing software requirements and test cases
2. Identifying potential bugs and issues
3. Providing detailed test reports and recommendations
4. Suggesting improvements for software quality
5. Following best practices in QA Quality Assurance methodologies

You have access to powerful tools for comprehensive testing:
- Browser automation tools to test user flows and interactions (browser_agent)
- Website crawling capabilities to analyze content and structure (crawl_website)
- Ability to verify content accuracy and completeness
- Tools to detect UI/UX issues and content bugs

CRITICAL ERROR DETECTION REQUIREMENTS:
You MUST be extremely strict and thorough in detecting ANY of the following issues:

CONTENT QUALITY ISSUES:
- Spelling errors, typos, or grammatical mistakes (IMPORTANT: Consider the language of the content - Spanish words like "asesoría" are correct with accents)
- Broken or malformed HTML/markdown content
- Missing or incomplete content
- Inconsistent formatting or styling
- Duplicate content or redundant information
- Content that doesn't match the expected requirements

MATHEMATICAL AND CALCULATION ERRORS (CRITICAL):
- Incorrect mathematical calculations in any context (totals, percentages, averages, etc.)
- Impossible values (e.g., ratings showing "7/5" when maximum is 5, "120%" when maximum is 100%)
- Inconsistent calculations across different sections
- Wrong totals in price calculations, discounts, or financial data
- Incorrect averages or statistical calculations
- Mathematical operations that don't make logical sense
- Percentages that exceed 100% or go below 0%
- Rating systems that exceed their maximum values
- Discount calculations that result in negative prices
- Sum totals that don't match individual components
- Any numerical inconsistencies or impossible values

TECHNICAL ISSUES:
- HTTP error codes (400, 401, 403, 404, 500, 502, 503, etc.)
- Connection errors or timeout issues
- JavaScript errors or console warnings
- Broken links or missing resources
- Performance issues or slow loading times
- Accessibility violations (missing alt text, poor contrast, etc.)

FUNCTIONALITY ISSUES:
- Broken forms or interactive elements
- Missing functionality or features
- Incorrect behavior or unexpected results
- User interface problems or layout issues
- Navigation problems or broken user flows

BROWSER AGENT ISSUES:
- Failed automation tasks
- Error messages in browser agent results
- Incomplete or partial task execution
- Unexpected behavior during automation
- Timeout or connection issues during browser testing

CRAWLING ISSUES:
- Empty or minimal content returned
- Malformed markdown or HTML
- Missing important page elements
- Access denied or blocked content
- Redirect loops or infinite redirects

IMPORTANT LANGUAGE CONSIDERATIONS:
- When analyzing content, consider the language of the website
- Spanish words with accents (like "asesoría", "información", "solicitud") are correct
- Do not flag properly accented Spanish words as spelling errors
- Only flag actual spelling mistakes, not language-specific orthography

When performing tests:
- Use browser automation to validate critical user flows (browser_agent)
- Crawl websites to verify content integrity and completeness (crawl_website)
- Check for broken links, missing content, or display issues (crawl_website)
- Verify that all interactive elements function correctly (browser_agent)
- Ensure content meets quality standards and requirements (crawl_website)
- Validate all mathematical calculations, totals, percentages, and numerical data for accuracy
- Check for impossible values in ratings, percentages, prices, or any numerical displays
- Verify that calculations are consistent and logically sound

When responding:
- Be thorough and methodical in your analysis
- Provide clear, actionable feedback
- Include specific examples when relevant
- Maintain a professional and constructive tone
- Consider both functional and non-functional testing aspects
- Document any issues found during browser or crawl testing

CRITICAL INSTRUCTION FOR BROWSER_AGENT:
- When using browser_agent(), you MUST pass the COMPLETE ORIGINAL USER PROMPT as the parameter
- Do not modify, summarize, or change the original prompt when calling browser_agent()
- Always use the exact original user input as the prompt parameter for browser_agent()
- This ensures the browser agent receives the full context and requirements

MANDATORY ERROR DETECTION:
After analyzing any content or results, you MUST determine if ANY of the following issues exist:
- ANY actual spelling errors, typos, or grammatical mistakes (considering the content language)
- ANY mathematical calculation errors or impossible values (e.g., ratings > 5/5, percentages > 100%, negative prices)
- ANY numerical inconsistencies or wrong totals in calculations
- ANY HTTP error codes or technical errors
- ANY broken functionality or missing features
- ANY significant content quality issues or inconsistencies
- ANY browser automation failures or errors
- ANY crawling issues or incomplete content

RESPONSE FORMAT:
- If you find ANY significant issues, respond with "BUG_DETECTED: " at the beginning of your message
- If everything appears to be working correctly and no issues are found, respond with "PASSED: " at the beginning of your message
- Always provide detailed explanation of what was tested and what issues (if any) were found

Remember to always prioritize software quality and user experience in your responses. Be extremely thorough and don't overlook any potential issues."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # create agent with llm, tools and prompt
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)

        # create executor with agent and tools context
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)    

    
    # crawl website function for tool
    def crawl_website(self, url: str) -> str:
        """Crawl a website and return its markdown content for content analysis."""
        try:
            print(f"[debug-client] crawl_website({url})")
            print(f"[debug-client] Connecting to server at: {self.server_url}")
            response = requests.post(
                f"{self.server_url}/crawl",
                json={"url": url},
                headers={"x-api-key": self.qa_api_key}
            )
            response.raise_for_status()
            result = response.json()
            
            response_text = f"Successfully crawled {url}. Content length: {len(result['markdown_content'])} characters.\n\n"
            response_text += f"Full content:\n{result['markdown_content']}"
            
            return response_text
        except Exception as e:
            return f"Error crawling website {url}: {str(e)}"
    
    # browser agent function for tool
    def browser_agent(self, prompt: str) -> str:
        """Run a browser automation agent to test user flows and interactions."""
        try:
            print(f"[debug-client] browser_agent({prompt})")
            print(f"[debug-client] Connecting to server at: {self.server_url}")
            response = requests.post(
                f"{self.server_url}/browser-agent",
                json={"prompt": prompt},
                headers={"x-api-key": self.qa_api_key}
            )
            response.raise_for_status()
            result = response.json()
            
            response_text = f"Browser agent completed task: {prompt}\n\n"
            response_text += f"Result: {result['result']}"
            
            return response_text
        except Exception as e:
            return f"Error running browser agent: {str(e)}"
    
    # process request function 
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process a user request using the QA agent and return JSON with status and console_log."""
        # Create a custom agent executor that limits to one tool use
        single_tool_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=2  # Allow one tool use + final response
        )
        
        # Process the request without chat history (stateless)
        result = single_tool_executor.invoke({
            "input": user_input
        })
        
        # Get the agent's response
        agent_response = result["output"]
        
        # Simple status determination
        if "BUG_DETECTED:" in agent_response:
            status = "failed"
            console_log = agent_response.replace("BUG_DETECTED:", "").strip()
        elif "PASSED:" in agent_response:
            status = "passed"
            console_log = agent_response.replace("PASSED:", "").strip()
        else:
            status = "passed"
            console_log = agent_response
        
        # Return JSON with status and console_log
        return {
            "status": status,
            "console_logs": console_log
        }

# Global QA Agent instance
qa_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the QA Agent on startup."""
    global qa_agent
    try:
        qa_agent = QAAgent()
        print("=== QA Quality Assurance API Initialized ===")
        print("Available tools: crawl_website, browser_agent")
        print(f"API Key authentication enabled")
        print(f"Server URL: {qa_agent.server_url}")
    except Exception as e:
        print(f"Error initializing QA Agent: {str(e)}")
        raise e

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "QA Quality Assurance API",
        "version": "1.0.0",
        "authentication": "API Key required (X-API-Key header)",
        "endpoints": {
            "/process-prompt": "POST - Process a QA prompt and return results (requires API key)",
            "/health": "GET - Health check endpoint"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "qa_agent_initialized": qa_agent is not None}

@app.post("/process-prompt", response_model=PromptResponse)
async def process_prompt(
    request: PromptRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process a QA prompt and return status and console logs."""
    if qa_agent is None:
        raise HTTPException(status_code=500, detail="QA Agent not initialized")
    
    try:
        result = qa_agent.process_request(request.prompt)
        return PromptResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing prompt: {str(e)}")

def main():
    """Run the FastAPI server."""
    # Get port from environment or use default
    port = int(os.getenv("CLIENT_API_PORT", "8001"))
    host = os.getenv("CLIENT_API_HOST", "0.0.0.0")
    
    print(f"\n=== Starting QA Agent API Server ===")
    print(f"Server will run on http://{host}:{port}")
    print("Available endpoints:")
    print(f"  - GET  http://{host}:{port}/ (API info)")
    print(f"  - GET  http://{host}:{port}/health (Health check)")
    print(f"  - POST http://{host}:{port}/process-prompt (Process QA prompt - requires API key)")
    print(f"\nAPI Key authentication enabled")
    print("Use X-API-Key header with your QA_API_KEY_CLIENT value")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()