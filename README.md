# MCP QA Agent Project - Agentes Inteligentes

Este proyecto incluye múltiples agentes inteligentes basados en OpenAI y LangChain para diferentes propósitos empresariales.

## 🤖 Agentes Disponibles

### 1. Agente QA (Original)
- **Propósito**: Sistema de preguntas y respuestas inteligente
- **Archivos**: `client/main.py`, `server/main.py`
- **Puertos**: Cliente 8001, Servidor 8000

### 2. Agente Asesor (Nuevo)
- **Propósito**: Asesoría virtual para comparación de software empresarial
- **Archivos**: `client/main_asesor.py`, `server/main_asesor.py`
- **Puertos**: Cliente 8011, Servidor 8010

### 3. Agente Auditor (Nuevo) ⭐
- **Propósito**: Auditoría de procesos e infraestructura tecnológica para transformación digital
- **Archivos**: `client/main_auditor.py`, `server/main_auditor.py`
- **Puertos**: Cliente 8021, Servidor 8020
- **Documentación**: Ver [README_AUDITOR.md](README_AUDITOR.md)

## 🚀 Configuración del Entorno

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

# Configuración del Agente Asesor
ASESOR_API_KEY=demo-key
ASESOR_API_KEY_CLIENT=demo-key
ASESOR_SERVER_URL=http://localhost:8010
ASESOR_SERVER_HOST=0.0.0.0
ASESOR_SERVER_PORT=8010
ASESOR_CLIENT_HOST=0.0.0.0
ASESOR_CLIENT_PORT=8011

# Configuración del Agente Auditor
AUDITOR_API_KEY=demo-key
AUDITOR_API_KEY_CLIENT=demo-key
AUDITOR_SERVER_URL=http://localhost:8020
AUDITOR_SERVER_HOST=0.0.0.0
AUDITOR_SERVER_PORT=8020
AUDITOR_CLIENT_HOST=0.0.0.0
AUDITOR_CLIENT_PORT=8021
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

## 🏃‍♂️ Ejecución de los Agentes

### Agente QA (Original)

#### Servidor QA
```bash
cd server
python main.py
```
Servidor en: `http://localhost:8000`

#### Cliente QA
```bash
cd client
python main.py
```
Cliente API en: `http://localhost:8001`

### Agente Asesor

#### Servidor Asesor
```bash
cd server
python main_asesor.py
```
Servidor en: `http://localhost:8010`

#### Cliente Asesor
```bash
cd client
python main_asesor.py
```
Cliente API en: `http://localhost:8011`

### Agente Auditor ⭐

#### Servidor Auditor
```bash
cd server
python main_auditor.py
```
Servidor en: `http://localhost:8020`

#### Cliente Auditor
```bash
cd client
python main_auditor.py
```
Cliente API en: `http://localhost:8021`

## 🧪 Pruebas

### Pruebas del Agente Auditor
```bash
python test_auditor.py
```

Este script prueba todas las funcionalidades del agente auditor:
- Análisis de procesos
- Evaluación de infraestructura
- Análisis de documentos
- Propuestas de automatización
- Cálculo de ROI
- Roadmaps de proyecto
- Conversación completa
- Subida de archivos

The QA Agent API will start on `http://localhost:8001` (or the configured host/port).

## 🎯 Capacidades del Agente Auditor

El **Agente Auditor Inteligente** es una solución revolucionaria que combina las capacidades de múltiples roles tradicionales:

### 🧩 Roles que Combina
- **Business Analyst**: Análisis de procesos y propuestas de mejora
- **Process Improvement Specialist**: Detección de ineficiencias y optimización
- **Organizational Development Consultant**: Análisis de cultura y dinámicas organizacionales
- **Internal Auditor**: Evaluación de controles y riesgos
- **Digital Transformation Manager**: Liderazgo en transformación tecnológica
- **Change Management Consultant**: Gestión del cambio organizacional

### 🔍 Funcionalidades Principales
- **Análisis de Procesos**: Detección de cuellos de botella y oportunidades de mejora
- **Evaluación de Infraestructura**: Auditoría tecnológica y recomendaciones de modernización
- **Análisis de Documentos**: Procesamiento inteligente de archivos y extracción de insights
- **Propuestas de Automatización**: Identificación de procesos candidatos y tecnologías recomendadas
- **Cálculo de ROI**: Análisis financiero completo con proyecciones a 3 años
- **Roadmaps de Proyectos**: Planificación detallada de implementación por fases

### 💡 Beneficios Clave
- **Rapidez**: Análisis completo en minutos, no meses
- **Escalabilidad**: Capacidad de auditar múltiples procesos simultáneamente
- **Precisión**: Análisis basado en datos y patrones reconocidos
- **Accionabilidad**: Propuestas concretas con roadmap de implementación
- **ROI Medible**: Cálculos precisos de beneficios y ahorros esperados

## 📞 Soporte y Documentación

- **Documentación del Agente Auditor**: [README_AUDITOR.md](README_AUDITOR.md)
- **Pruebas Automatizadas**: `python test_auditor.py`
- **API Documentation**: Disponible en los endpoints de cada agente
- **Ejemplos de Uso**: Incluidos en los scripts de prueba

---

**¿Listo para transformar tu organización?** 🚀

El Agente Auditor Inteligente está diseñado para ser tu compañero estratégico en la transformación digital, proporcionando insights profundos y propuestas accionables en cuestión de minutos.

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


