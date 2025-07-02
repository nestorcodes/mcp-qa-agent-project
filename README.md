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

# Client API Configuration
CLIENT_API_HOST=0.0.0.0
CLIENT_API_PORT=8001

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# QA API Key for server authentication
QA_API_KEY=your_qa_api_key_here

# QA API Key for client API authentication
QA_API_KEY_CLIENT=your_qa_api_key_client_here
```

**Environment Variables:**
- `SERVER_HOST`: Host address for the server (default: 0.0.0.0)
- `SERVER_PORT`: Port for the server (default: 8000)
- `CLIENT_HOST`: Host address for client to connect to server (default: localhost)
- `CLIENT_PORT`: Port for client to connect to server (default: 8000)
- `CLIENT_API_HOST`: Host address for the QA Agent API (default: 0.0.0.0)
- `CLIENT_API_PORT`: Port for the QA Agent API (default: 8001)
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `QA_API_KEY`: API key for server authentication (required)
- `QA_API_KEY_CLIENT`: API key for client API authentication (required)

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

### Option 1: Terminal Client (Original)
1. In a new terminal, navigate to the client directory:
```bash
cd client
```

2. Start the client:
```bash
python main.py
```

The client will connect to the server using the host and port from your `.env` file.

### Option 2: API Client (New)
1. In a new terminal, navigate to the client directory:
```bash
cd client
```

2. Start the API server:
```bash
python main.py
```

The QA Agent API will start on `http://localhost:8001` (or the configured host/port).

## QA Agent API Endpoints

The QA Agent API provides the following endpoints:

### GET `/`
Returns API information and available endpoints.

**Response:**
```json
{
  "message": "QA Quality Assurance API",
  "version": "1.0.0",
  "endpoints": {
    "/process-prompt": "POST - Process a QA prompt and return results",
    "/health": "GET - Health check endpoint"
  }
}
```

### GET `/health`
Health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "healthy",
  "qa_agent_initialized": true
}
```

### POST `/process-prompt`
Process a QA prompt and return test results.

**Headers:**
```
X-API-Key: your_qa_api_key_client_here
```

**Request Body:**
```json
{
  "prompt": "Test the website https://example.com for any broken links or content issues"
}
```

**Response:**
```json
{
  "status": "passed",
  "console_logs": "Website analysis completed successfully. No broken links found..."
}
```

**Status Values:**
- `"passed"`: No bugs or critical issues detected
- `"failed"`: Bugs, errors, or critical issues detected

## Testing the API

You can test the API using the provided test script:

```bash
python test_api_client.py
```

Or using curl:

```bash
# Health check
curl http://localhost:8001/health

# Process a prompt
curl -X POST http://localhost:8001/process-prompt \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_qa_api_key_client_here" \
  -d '{"prompt": "Test the website https://example.com for any broken links or content issues"}'
```

## Links 
https://modelcontextprotocol.io/introduction
https://langchain-ai.github.io/langgraph/agents/mcp/#use-mcp-tools
https://openai.github.io/openai-agents-python/mcp/
https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#2-create-a-stategraph
https://github.com/jlowin/fastmcp
https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/?h=history
https://langchain-ai.github.io/langgraph/agents/agents/#5-add-memory


