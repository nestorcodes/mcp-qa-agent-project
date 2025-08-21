# Agente de Discovery para Entrevistas a Empleados

## Descripción

El **Agente de Discovery** es un agente inteligente especializado en entrevistar empleados y colaboradores para entender sus roles, funciones y procesos diarios dentro de la compañía. Este agente está diseñado para realizar entrevistas estructuradas que permitan descubrir información detallada sobre los procesos operativos de la empresa.

## Características Principales

### 🎯 Objetivos del Agente
1. **Presentación clara** del propósito de la entrevista
2. **Recopilación de datos básicos** del empleado (nombre, rol, descripción del rol)
3. **Discovery dinámico** sobre procesos diarios y cómo se ejecutan
4. **Profundización adaptativa** en detalles específicos de cada proceso
5. **Envío automático** de información al webhook externo

### 🔄 Flujo de Entrevista

#### **ETAPA 1: PRESENTACIÓN Y DATOS BÁSICOS (3 preguntas fijas)**
1. **Presentación**: Saludo y explicación del propósito
2. **Nombre**: Captura del nombre completo del empleado
3. **Rol**: Captura del cargo o posición en la empresa
4. **Descripción del rol**: Entendimiento de las responsabilidades y área de trabajo

#### **ETAPA 2: DISCOVERY DINÁMICO DE PROCESOS (Preguntas adaptativas)**
5. **Procesos principales**: ¿Qué procesos realizas en tu día a día?
6. **Profundización dinámica**: Preguntas adaptativas basadas en las respuestas del empleado:
   - Detalles de ejecución paso a paso
   - Herramientas utilizadas y tiempo requerido
   - Personas involucradas y coordinación
   - Dificultades y áreas de mejora
   - Sistemas y aplicaciones
   - Colaboración con otros equipos

### 🧠 Técnicas de Profundización Dinámica

El agente utiliza técnicas inteligentes para profundizar en los detalles de forma adaptativa:
- **Escucha activa** de cada respuesta para hacer preguntas específicas
- **Adaptación dinámica** de preguntas según la información descubierta
- **Profundización contextual** en procesos importantes o complejos
- **Exploración de herramientas**, tiempo, coordinación, problemas y mejoras
- **Enfoque en ejecución paso a paso** de cada proceso

### 🔍 Ejemplos de Preguntas Dinámicas

- Si menciona un proceso específico: "¿Podrías explicarme paso a paso cómo ejecutas [PROCESO]?"
- Si menciona tiempo: "¿Cuánto tiempo toma cada paso de este proceso?"
- Si menciona personas: "¿Quiénes están involucrados y cuál es el rol de cada uno?"
- Si menciona herramientas: "¿Cómo te ayuda específicamente [HERRAMIENTA] en este proceso?"
- Si menciona coordinación: "¿Cómo se coordina este proceso con otros departamentos?"
- Si menciona problemas: "¿Qué dificultades encuentras en este proceso?"
- Si menciona mejoras: "¿Qué te gustaría mejorar en este proceso?"

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

```python
# Ejecutar pruebas
python test_discovery_agent.py

# O probar endpoint específico
curl -X POST "http://localhost:8021/discovery-webhook" \
  -H "x-api-key: demo-key" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, quiero participar en la entrevista",
    "convo_id": "test_001",
    "files": []
  }'
```

### 📊 Estructura de Respuesta

```json
{
  "reply": "Respuesta del agente",
  "convo_id": "ID de conversación",
  "context": "Contexto de la entrevista",
  "next_question": "Siguiente pregunta a realizar",
  "stage": "Etapa actual de la entrevista"
}
```

### 📋 Información Capturada

```json
{
  "nombre": "Nombre del empleado",
  "rol": "Rol o cargo en la empresa",
  "descripcion_rol": "Descripción del rol y responsabilidades",
  "tipo_entrevista": "discovery_empleado"
}
```

## Ventajas del Agente

### 🎯 **Enfoque Especializado**
- Diseñado específicamente para entrevistas a empleados
- Preguntas estructuradas en la fase inicial
- Discovery dinámico y adaptativo en la fase de profundización

### 🧠 **Inteligencia Artificial**
- Modelo GPT-4 para respuestas contextuales
- Memoria persistente de conversaciones
- Adaptación dinámica a las respuestas del empleado

### 📊 **Gestión de Datos**
- Captura estructurada de información básica
- Discovery dinámico sin estructura rígida
- Envío automático a sistemas externos
- Seguimiento del progreso de la entrevista

### 🔄 **Flexibilidad**
- Manejo de archivos adjuntos
- Personalización de preguntas según contexto
- Extensibilidad para nuevos tipos de entrevistas
- Adaptación dinámica a las respuestas del empleado

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

Para ejecutar las pruebas:

```bash
# Pruebas unitarias
python -m pytest test_discovery_agent.py

# Pruebas de integración
python test_webhook_auditor.py
```

## Changelog

### v2.0.0 - Discovery Dinámico
- **Nuevo**: Flujo simplificado con solo 3 preguntas básicas
- **Nuevo**: Discovery dinámico y adaptativo
- **Mejorado**: Preguntas contextuales basadas en respuestas
- **Optimizado**: Mejor manejo de memoria y contexto

### v1.0.0 - Versión Inicial
- Implementación básica del agente de discovery
- Flujo estructurado de preguntas
- Envío automático a webhook
- Gestión de memoria de conversaciones
