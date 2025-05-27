import os
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

class MCPClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
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
                description="Crawls a website and returns its content in markdown format"
            )
        ]

        # define main prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant that can crawl websites and analyze their content."),
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
        try:
            response = requests.post(
                "http://localhost:8000/crawl",
                json={"url": url}
            )
            response.raise_for_status()
            return response.json()["markdown_content"]
        except Exception as e:
            return f"Error crawling website: {str(e)}"
    
    # process request function 
    # add user message to chat history
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process a user request using the agent."""
        # Add user message to chat history
        self.chat_history.append(HumanMessage(content=user_input))
        
        # Process the request with chat history
        result = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": self.chat_history
        })
        
        # Add AI response to chat history
        self.chat_history.append(AIMessage(content=result["output"]))
        
        return result

def main():
    client = MCPClient()
    
    # usage in terminal
    while True:
        user_input = input("\nEnter your prompt (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        try:
            result = client.process_request(user_input)
            print("\nResult:", result["output"])
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 