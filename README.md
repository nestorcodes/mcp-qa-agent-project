# MCP QA agent with OpenAI Integration



1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
    
```

3. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Server

1. Navigate to the server directory:
```bash
cd server
```

2. Start the server:
```bash
python main_mcp.py
```

The server will start on `http://localhost:8000`




## Running the Client

1. In a new terminal, navigate to the client directory:
```bash
cd client
```

2. Start the client:
```bash
python main_mcp.py
```

## Links 
https://modelcontextprotocol.io/introduction
https://langchain-ai.github.io/langgraph/agents/mcp/#use-mcp-tools
https://openai.github.io/openai-agents-python/mcp/
https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#2-create-a-stategraph
https://github.com/jlowin/fastmcp
https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/?h=history
https://langchain-ai.github.io/langgraph/agents/agents/#5-add-memory


