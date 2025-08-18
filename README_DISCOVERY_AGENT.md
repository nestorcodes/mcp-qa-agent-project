# Agente de Discovery para Entrevistas a Empleados

## Descripción

El **Agente de Discovery** es un agente inteligente especializado en entrevistar empleados y colaboradores para entender sus roles, funciones y procesos diarios dentro de la compañía. Este agente está diseñado para realizar entrevistas estructuradas que permitan descubrir información detallada sobre los procesos operativos de la empresa.

## Características Principales

### 🎯 Objetivos del Agente
1. **Presentación clara** del propósito de la entrevista
2. **Recopilación de datos básicos** del empleado (nombre, puesto, papel en la compañía)
3. **Discovery profundo** sobre procesos diarios y cómo se ejecutan
4. **Profundización** en detalles específicos de cada proceso
5. **Envío automático** de información al webhook externo

### 🔄 Flujo de Entrevista

#### **ETAPA 1: PRESENTACIÓN Y DATOS BÁSICOS (3 preguntas)**
1. **Presentación**: Saludo y explicación del propósito
2. **Nombre**: Captura del nombre completo del empleado
3. **Puesto**: Captura del cargo o posición en la empresa
4. **Papel en la compañía**: Entendimiento del área de responsabilidad

#### **ETAPA 2: DISCOVERY DE PROCESOS DIARIOS (7 preguntas)**
5. **Procesos principales**: ¿Qué procesos realizas en tu día a día?
6. **Detalles de ejecución**: ¿Cómo ejecutas paso a paso estos procesos?
7. **Coordinación**: ¿Cómo se coordina con otros departamentos?
8. **Puntos de mejora**: ¿Qué aspectos podrían ser más eficientes?
9. **Herramientas y sistemas**: ¿Qué herramientas utilizas?
10. **Colaboración**: ¿Cómo te comunicas con otros equipos?
11. **Cierre**: ¿Hay algo más que quieras compartir?

### 🧠 Técnicas de Profundización

El agente utiliza técnicas inteligentes para profundizar en los detalles:
- **"¿Cómo exactamente?"** para entender procesos paso a paso
- **"¿Cuánto tiempo toma?"** para medir eficiencia
- **"¿Cuál es el rol de cada persona?"** para entender coordinación
- **"¿Cómo te ayuda esa herramienta?"** para entender sistemas

## API Endpoints

### 🔌 Discovery Webhook
```
POST /discovery-webhook
```
**Descripción**: Endpoint principal para interactuar con el agente de discovery

**Body**:
```json
{
  "message": "Mensaje del empleado",
  "convo_id": "ID único de conversación",
  "files": ["archivos en base64 (opcional)"]
}
```

**Response**:
```json
{
  "reply": "Respuesta del agente",
  "convo_id": "ID de conversación",
  "context": "Contexto completo de la entrevista",
  "next_question": "Siguiente pregunta a realizar",
  "stage": "Etapa actual de la entrevista"
}
```

### 📊 Discovery Analysis
```
GET /discovery-analysis/{convo_id}
```
**Descripción**: Obtiene el análisis completo de una entrevista específica

**Response**:
```json
{
  "convo_id": "ID de conversación",
  "context": "Contexto completo",
  "stage": "Etapa actual",
  "employee_info": {
    "nombre": "Nombre del empleado",
    "puesto": "Puesto o cargo",
    "papel_empresa": "Papel en la compañía",
    "procesos_principales": "Procesos que realiza",
    "detalles_ejecucion": "Detalles de ejecución",
    "coordinacion": "Información de coordinación",
    "areas_mejora": "Áreas de mejora identificadas",
    "herramientas_sistemas": "Herramientas utilizadas",
    "colaboracion": "Procesos de colaboración"
  },
  "progress": "Progreso de la entrevista (0-9)"
}
```

### 📋 Discovery Conversations
```
GET /discovery-conversations
```
**Descripción**: Lista todas las entrevistas de discovery activas

**Response**:
```json
{
  "discovery_conversations": {
    "convo_id": {
      "stage": "Etapa actual",
      "employee_name": "Nombre del empleado",
      "position": "Puesto",
      "papel_empresa": "Papel en la compañía",
      "last_updated": "Última actualización",
      "progress": "Progreso de la entrevista"
    }
  }
}
```

## Uso del Agente

### 🚀 Iniciar una Entrevista

1. **Crear ID de conversación único**
2. **Enviar primer mensaje** al endpoint `/discovery-webhook`
3. **Seguir el flujo** de preguntas y respuestas
4. **Mantener el contexto** usando el mismo `convo_id`

### 📝 Ejemplo de Uso

```python
import requests

# Configuración
BASE_URL = "http://localhost:8021"
API_KEY = "tu-api-key"
HEADERS = {"x-api-key": API_KEY}

# Iniciar entrevista
convo_id = "entrevista_001"
response = requests.post(
    f"{BASE_URL}/discovery-webhook",
    json={
        "message": "Hola, quiero participar en la entrevista",
        "convo_id": convo_id,
        "files": []
    },
    headers=HEADERS
)

# Procesar respuesta
result = response.json()
print(f"Respuesta: {result['reply']}")
print(f"Etapa: {result['stage']}")
```

## Configuración

### 🔧 Variables de Entorno

```bash
# API Key de OpenAI
OPENAI_API_KEY=tu-openai-api-key

# URL del servidor auditor
AUDITOR_SERVER_URL=http://localhost:8020

# API Key del servidor auditor
AUDITOR_API_KEY=demo-key

# URL del webhook externo
WEBHOOK_URL=https://tu-webhook-url.com/webhook

# Puerto del cliente
AUDITOR_CLIENT_PORT=8021

# Host del cliente
AUDITOR_CLIENT_HOST=0.0.0.0
```

### 🏃‍♂️ Ejecutar el Servidor

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python client/main_auditor.py
```

## Pruebas

### 🧪 Script de Prueba

El archivo `test_discovery_agent.py` incluye pruebas completas del agente:

```bash
python test_discovery_agent.py
```

### ✅ Casos de Prueba

El script de prueba simula una entrevista completa con:
- **Empleado**: María González
- **Puesto**: Analista de Recursos Humanos
- **Procesos**: Reclutamiento, onboarding, evaluación de desempeño
- **Herramientas**: Workday, LinkedIn, Excel
- **Colaboración**: Coordinación con gerentes y otros departamentos

## Estructura del Código

### 🏗️ Clase DiscoveryAgent

```python
class DiscoveryAgent:
    def __init__(self):
        # Inicialización del modelo LLM y herramientas
        
    def send_to_webhook(self, employee_info: dict):
        # Envío de información al webhook externo
        
    def get_conversation_stage(self, context: dict):
        # Determinación de la etapa actual
        
    def extract_information(self, message: str, context: dict):
        # Extracción de información del mensaje
        
    def get_next_question(self, stage: str, context: dict):
        # Generación de la siguiente pregunta
        
    def process_message(self, message: str, convo_id: str, files: List[str]):
        # Procesamiento principal del mensaje
```

### 🔄 Flujo de Procesamiento

1. **Recepción** del mensaje del empleado
2. **Extracción** de información relevante
3. **Determinación** de la etapa actual
4. **Generación** de la siguiente pregunta
5. **Envío** al webhook cuando sea apropiado
6. **Actualización** del contexto de la conversación

## Integración con Webhook

### 📤 Envío Automático

El agente envía información al webhook externo cuando:
- Se completa la información básica (nombre, puesto, papel)
- Se completa toda la entrevista de discovery

### 📊 Datos Enviados

```json
{
  "nombre": "Nombre del empleado",
  "puesto": "Puesto o cargo",
  "papel_empresa": "Papel en la compañía",
  "procesos_principales": "Procesos que realiza",
  "detalles_ejecucion": "Detalles de ejecución",
  "coordinacion": "Información de coordinación",
  "areas_mejora": "Áreas de mejora identificadas",
  "herramientas_sistemas": "Herramientas utilizadas",
  "colaboracion": "Procesos de colaboración",
  "tipo_entrevista": "discovery_empleado"
}
```

## Ventajas del Agente

### 🎯 **Enfoque Especializado**
- Diseñado específicamente para entrevistas a empleados
- Preguntas estructuradas y progresivas
- Técnicas de profundización inteligentes

### 🧠 **Inteligencia Artificial**
- Modelo GPT-4 para respuestas contextuales
- Memoria persistente de conversaciones
- Adaptación dinámica a las respuestas del empleado

### 📊 **Gestión de Datos**
- Captura estructurada de información
- Envío automático a sistemas externos
- Seguimiento del progreso de la entrevista

### 🔄 **Flexibilidad**
- Manejo de archivos adjuntos
- Personalización de preguntas según contexto
- Extensibilidad para nuevos tipos de entrevistas

## Casos de Uso

### 🏢 **Auditoría de Procesos**
- Entrevistar empleados sobre sus procesos diarios
- Identificar áreas de mejora y automatización
- Mapear flujos de trabajo y coordinación

### 👥 **Gestión del Cambio**
- Entender el impacto de nuevos sistemas
- Identificar resistencias y necesidades de capacitación
- Evaluar la adopción de herramientas

### 📈 **Optimización Operativa**
- Descubrir cuellos de botella en procesos
- Identificar oportunidades de automatización
- Mejorar la coordinación entre departamentos

## Contribución

### 🛠️ Desarrollo

Para contribuir al desarrollo del agente:

1. **Fork** del repositorio
2. **Crear** rama para nueva funcionalidad
3. **Implementar** cambios
4. **Probar** con el script de pruebas
5. **Crear** Pull Request

### 🧪 Pruebas

- Ejecutar `test_discovery_agent.py` antes de cambios
- Verificar que todas las etapas funcionen correctamente
- Comprobar el envío al webhook
- Validar la extracción de información

## Soporte

### 📞 Contacto

Para soporte técnico o preguntas sobre el agente:
- Revisar la documentación de la API
- Ejecutar las pruebas para verificar funcionamiento
- Verificar la configuración de variables de entorno

### 🐛 Reportar Problemas

Al reportar problemas, incluir:
- Descripción detallada del problema
- Pasos para reproducir
- Logs de error
- Configuración del entorno
- Versión del código

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2024  
**Desarrollado por**: ComparaSoftware QA Team
