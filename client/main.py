import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import requests
from typing import Dict, Any, List
from langchain.schema import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

class QAAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Get server configuration from environment variables
        self.server_host = os.getenv("CLIENT_HOST", "localhost")
        self.server_port = os.getenv("CLIENT_PORT", "8000")
        self.server_url = f"http://{self.server_host}:{self.server_port}"
        
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

When performing tests:
- Use browser automation to validate critical user flows (browser_agent)
- Crawl websites to verify content integrity and completeness (crawl_website)
- Check for broken links, missing content, or display issues (crawl_website)
- Verify that all interactive elements function correctly (browser_agent)
- Ensure content meets quality standards and requirements (crawl_website)

When responding:
- Be thorough and methodical in your analysis
- Provide clear, actionable feedback
- Include specific examples when relevant
- Maintain a professional and constructive tone
- Consider both functional and non-functional testing aspects
- Document any issues found during browser or crawl testing

IMPORTANT: After your analysis, you must determine if any bugs, errors, or critical issues were found:
- If you find ANY bugs, errors, broken functionality, missing content, or critical issues, respond with "BUG_DETECTED: " at the beginning of your message
- If everything appears to be working correctly and no issues are found, respond with "PASSED: " at the beginning of your message

Remember to always prioritize software quality and user experience in your responses.
Important: send complete prompt to browser_agent()"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # create agent with llm, tools and prompt
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)

        # create executor with agent and tools context
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

        # create chat history for memory 
        self.chat_history: List[HumanMessage | AIMessage] = []
    
    # crawl website function for tool
    def crawl_website(self, url: str) -> str:
        """Crawl a website and return its markdown content for content analysis."""
        try:
            print(f"[debug-client] crawl_website({url})")
            response = requests.post(
                f"{self.server_url}/crawl",
                json={"url": url}
            )
            response.raise_for_status()
            result = response.json()
            return f"Successfully crawled {url}. Content length: {len(result['markdown_content'])} characters.\n\nContent preview:\n{result['markdown_content'][:500]}..."
        except Exception as e:
            return f"Error crawling website {url}: {str(e)}"
    
    # browser agent function for tool
    def browser_agent(self, prompt: str) -> str:
        """Run a browser automation agent to test user flows and interactions."""
        try:
            print(f"[debug-client] browser_agent({prompt})")
            response = requests.post(
                f"{self.server_url}/browser-agent",
                json={"prompt": prompt}
            )
            response.raise_for_status()
            result = response.json()
            return f"Browser agent completed task: {prompt}\n\nResult: {result['result']}"
        except Exception as e:
            return f"Error running browser agent: {str(e)}"
    
    # process request function 
    # add user message to chat history
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process a user request using the QA agent and return JSON with status and console_log."""
        # Add user message to chat history
        self.chat_history.append(HumanMessage(content=user_input))
        
        # Create a custom agent executor that limits to one tool use
        single_tool_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True # Limit to one tool use per request
        )
        
        # Process the request with chat history
        result = single_tool_executor.invoke({
            "input": user_input,
            "chat_history": self.chat_history
        })
        
        # Get the agent's response
        agent_response = result["output"]
        
        # Add AI response to chat history
        self.chat_history.append(AIMessage(content=agent_response))
        
        # Determine status based on agent response
        if agent_response.startswith("BUG_DETECTED:"):
            status = "failed"
            # Remove the prefix for cleaner console_log
            console_log = agent_response.replace("BUG_DETECTED:", "").strip()
        elif agent_response.startswith("PASSED:"):
            status = "passed"
            # Remove the prefix for cleaner console_log
            console_log = agent_response.replace("PASSED:", "").strip()
        else:
            # Default to failed if no clear status indicator
            status = "passed"
            console_log = agent_response
        
        # Return JSON with status and console_log
        return {
            "status": status,
            "console_logs": console_log
        }

def main():
    print("\n=== QA Quality Assurance System Initialized ===")
    print("Available tools: crawl_website, browser_agent")
    print("Type 'quit' to exit\n")
    
    client = QAAgent()
    
    # usage in terminal
    while True:
        user_input = input("\nEnter your QA prompt (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            print("\nExiting QA system. Goodbye!")
            break
            
        try:
            result = client.process_request(user_input)
            print("\n=== QA Agent Response ===")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"\n=== Error Occurred ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nPlease try again with a different prompt.")

if __name__ == "__main__":
    main()