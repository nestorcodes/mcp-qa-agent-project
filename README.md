# MCP QA agent with OpenAI Integration

## Environment Configuration

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
    pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `env_template.txt` to `.env` in the root directory
   - Update the values in `.env` with your configuration:

```bash
# Copy the template
cp env_template.txt .env

# Edit .env with your values
```

The `.env` file should contain:
```
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Client Configuration
CLIENT_HOST=localhost
CLIENT_PORT=8000

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

**Environment Variables:**
- `SERVER_HOST`: Host address for the server (default: 0.0.0.0)
- `SERVER_PORT`: Port for the server (default: 8000)
- `CLIENT_HOST`: Host address for client to connect to server (default: localhost)
- `CLIENT_PORT`: Port for client to connect to server (default: 8000)
- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Running the Server

1. Navigate to the server directory:
```bash
cd server
```

2. Start the server:
```bash
python main.py
```

The server will start using the host and port from your `.env` file (default: `http://localhost:8000`)

## Running the Client

1. In a new terminal, navigate to the client directory:
```bash
cd client
```

2. Start the client:
```bash
python main.py
```

The client will connect to the server using the host and port from your `.env` file.

## Links 
https://modelcontextprotocol.io/introduction
https://langchain-ai.github.io/langgraph/agents/mcp/#use-mcp-tools
https://openai.github.io/openai-agents-python/mcp/
https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#2-create-a-stategraph
https://github.com/jlowin/fastmcp
https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/?h=history
https://langchain-ai.github.io/langgraph/agents/agents/#5-add-memory


