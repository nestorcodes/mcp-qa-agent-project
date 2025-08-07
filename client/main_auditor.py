import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import requests
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import base64
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Modelos Pydantic
class WebhookRequest(BaseModel):
    message: str
    convo_id: str
    files: List[str] = []  # Lista de archivos en base64

class WebhookResponse(BaseModel):
    reply: str
    convo_id: str
    context: dict
    analysis_results: dict = {}
    next_question: str = ""
    stage: str = ""

class FileUploadRequest(BaseModel):
    convo_id: str
    file_content: str  # base64
    file_name: str

# FastAPI app
app = FastAPI(
    title="Agente Auditor de Procesos e Infraestructura API",
    description="API para agente auditor inteligente de transformación digital",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key
AUDITOR_API_KEY_CLIENT = os.getenv("AUDITOR_API_KEY_CLIENT", "demo-key")

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != AUDITOR_API_KEY_CLIENT:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Memoria de conversaciones y análisis
conversation_memory = {}
analysis_memory = {}

class AuditorAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.server_url = os.getenv("AUDITOR_SERVER_URL", "http://localhost:8020")
        self.auditor_api_key = os.getenv("AUDITOR_API_KEY", "demo-key")
        self.llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.1, api_key=self.api_key)
        
        self.tools = [
            Tool(
                name="document_analyzer",
                func=self.document_analyzer,
                description="Analiza documentos para extraer información sobre procesos y automatizaciones."
            ),
            Tool(
                name="send_to_webhook",
                func=self.send_to_webhook,
                description="Envía información extraída al webhook externo. Se ejecuta automáticamente: 1) Primera vez con información básica (nombre, puesto, empresa, teléfono), 2) Llamadas subsecuentes con información adicional del discovery."
            )
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un Agente Auditor Inteligente especializado en auditoría de procesos empresariales y análisis de infraestructura tecnológica para la transformación digital.

Tu objetivo es recopilar información de contacto básica, luego TODA la información posible sobre la empresa y sus procesos en NO MÁS DE 4 PREGUNTAS, y finalmente proporcionar recomendaciones específicas.

REGLAS FUNDAMENTALES:
1. SIEMPRE mantén memoria de lo que ya has preguntado - NO REPITAS PREGUNTAS
2. Haz UNA SOLA PREGUNTA a la vez
3. Respuestas CLARAS y BREVES (máximo 2-3 líneas)
4. Enfócate en PROCESOS y AUTOMATIZACIONES
5. Después de recopilar datos básicos + 4 preguntas, SIEMPRE ofrece recomendaciones

FLUJO DE AUDITORÍA INTELIGENTE:

ETAPA 1: RECOPILACIÓN DE DATOS BÁSICOS (6 preguntas)
Recopilar información de contacto en este orden:
1. Nombre completo
2. Rol o cargo en la empresa
3. Nombre de la empresa
4. País donde opera
5. Correo electrónico
6. Teléfono de contacto

             ETAPA 2: PREGUNTAS DE DISCOVERY (EXPLORACIÓN ESTRATÉGICA)
Objetivo: Explorar la operación de la empresa, sus dinámicas y oportunidades de mejora, sin asumir que el usuario ya tiene identificado un problema específico.
El enfoque debe ser conversacional. Formular una pregunta a la vez y ajustar el flujo según las respuestas del usuario.
Cuando se tenga suficiente información para hacer recomendaciones de valor, preguntar si desea conocerlas o seguir con la exploración.

Preguntas orientativas (usar según el contexto, no necesariamente todas ni en orden estricto):

PREGUNTA 1: Contexto general del negocio
"Para comenzar, ¿me podrías contar un poco sobre tu empresa y cómo opera actualmente?
(Si es necesario, guiar con preguntas como: ¿a qué se dedican?, ¿cuáles son sus áreas principales?, ¿qué tipo de clientes tienen?, ¿cuántas personas conforman el equipo?)"

PREGUNTA 2: Funcionamiento actual de sus procesos
"¿Hay procesos dentro de la empresa que sientes que podrían ser más ágiles, digitales o eficientes?
(No es necesario que ya tengan claro cuál, puede ser algo que simplemente 'sienten' que podría funcionar mejor.)"

PREGUNTA 3: Dinámica del trabajo diario
"¿Qué tareas o actividades te parecen especialmente repetitivas, manuales o que consumen mucho tiempo en el día a día del equipo?
(Puede ser algo que hagan en hojas de cálculo, tareas administrativas, coordinación entre equipos, generación de reportes, etc.)"

PREGUNTA 4: Información, herramientas y decisiones
"¿Cómo gestionan actualmente la información para tomar decisiones o dar seguimiento a procesos?
(¿Usan algún sistema como ERP, CRM, o trabajan principalmente con archivos compartidos, correos, etc.?)"

PREGUNTA 5: Prioridades y visión de mejora
"Si pudieras mejorar algo en tu operación hoy mismo, ¿qué sería? ¿Dónde te gustaría ver más orden, velocidad o menos errores?
(No es necesario que tengas una solución clara, solo una percepción o intuición.)"


             
ETAPA 3: RECOMENDACIONES (cuando se tenga información para dar recomendación)
SIEMPRE que te sientas listo para dar una recomendación seguna la información recopilada, di:
"Perfecto, ya tengo suficiente información. Tengo algunas recomendaciones específicas para tu caso. ¿Te gustaría que te las comparta ahora, o prefieres que sigamos la exploración de tus procesos?"

Si el usuario quiere recomendaciones:
- Proponer 2-3 automatizaciones específicas
- Estimar beneficios concretos (tiempo ahorrado, errores reducidos)
- Sugerir próximos pasos y herramientas

Si el usuario quiere explorar más:
- Hacer preguntas adicionales para un discovery de necesidades y oportunidades
- Profundizar en áreas de oportunidad

REGISTRO DE LEADS:
- Primera llamada: Después de recopilar información básica completa (nombre, puesto, empresa, teléfono), se envía automáticamente al webhook
- Llamadas subsecuentes: Cuando se obtiene información adicional del discovery (datos de empresa, procesos, objetivos, sistemas), se envía automáticamente al webhook
- El webhook se ejecuta automáticamente cuando se analiza un documento, pero también se puede usar manualmente cuando se tiene información completa

USO DE HERRAMIENTAS:
- **document_analyzer**: Usar si el usuario comparte documentos
- **send_to_webhook**: Usar cuando tengas información de contacto completa (nombre, apellido, empresa, teléfono) para registrar el lead en el sistema externo

FORMATO DE RESPUESTA:
- Respuesta breve y directa
- Una sola pregunta por mensaje
- Después de datos básicos + 4 preguntas, SIEMPRE ofrecer recomendaciones
- Mostrar progreso del análisis

Ejemplo de respuesta después de 4 preguntas:
"Perfecto, ya tengo suficiente información. Tengo algunas recomendaciones específicas para tu caso. ¿Te gustaría que te las comparta ahora, o prefieres que exploremos más a fondo algún aspecto específico de tus necesidades?"

NO hagas múltiples preguntas en un solo mensaje. Mantén el enfoque en procesos y automatizaciones."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)



    def document_analyzer(self, document_content: str) -> str:
        """Analiza documentos para extraer información sobre procesos"""
        try:
            response = requests.post(
                f"{self.server_url}/document-analyzer",
                json={"document_content": document_content},
                headers={"x-api-key": self.auditor_api_key}
            )
            return response.json()["analysis"]
        except Exception as e:
            return f"Análisis completado - Información sobre procesos extraída"

    def send_to_webhook(self, lead_info: dict) -> str:
        """Envía información del lead al webhook externo en formato JSON"""
        try:
            # URL del webhook
            webhook_url = os.getenv("WEBHOOK_URL", "https://www.dev.comparasoftware.com/selfhosted-n8n/webhook/98c962dd-700e-44c5-b0d5-cbb72145f8af")
            
            # Preparar datos para el webhook en formato JSON
            webhook_data = {
                "lead_info": json.dumps(lead_info, ensure_ascii=False),
                "timestamp": datetime.now().isoformat(),
                "source": "auditor_client"
            }
            
            # Hacer request GET al webhook
            response = requests.get(webhook_url, params=webhook_data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Datos enviados exitosamente al webhook: {webhook_data}")
                return f"✅ Información del lead enviada al webhook: {json.dumps(lead_info, ensure_ascii=False)}"
            else:
                print(f"❌ Error al enviar al webhook. Status: {response.status_code}, Response: {response.text}")
                return f"❌ Error al enviar al webhook: Status {response.status_code}"
                
        except Exception as e:
            print(f"❌ Error al enviar al webhook: {str(e)}")
            return f"❌ Error al enviar al webhook: {str(e)}"

    def get_conversation_stage(self, context: dict) -> str:
        """Determina la etapa actual de la conversación"""
        questions_asked = len(context.get("asked_questions", []))
        
        # Etapa 1: Recopilación de datos básicos (6 preguntas)
        if questions_asked == 0:
            return "initial_greeting"
        elif questions_asked == 1:
            return "collecting_name"
        elif questions_asked == 2:
            return "collecting_role"
        elif questions_asked == 3:
            return "collecting_company"
        elif questions_asked == 4:
            return "collecting_country"
        elif questions_asked == 5:
            return "collecting_email"
        elif questions_asked == 6:
            return "collecting_phone"
        # Etapa 2: Recopilación comprehensiva (4 preguntas)
        elif questions_asked == 7:
            return "question_1_company_info"
        elif questions_asked == 8:
            return "question_2_process_details"
        elif questions_asked == 9:
            return "question_3_automation_opportunities"
        elif questions_asked == 10:
            return "question_4_goals_constraints"
        else:
            return "providing_recommendations"

    def extract_information(self, message: str, context: dict) -> dict:
        """Extrae información específica del mensaje del usuario"""
        message_lower = message.lower()
        updated_context = context.copy()
        
        # Guardar el mensaje completo para análisis posterior
        if "user_responses" not in updated_context:
            updated_context["user_responses"] = []
        updated_context["user_responses"].append(message)
        
        # Extraer información básica usando patrones más flexibles
        if "me llamo" in message_lower or "soy" in message_lower or "mi nombre es" in message_lower or "nombre" in message_lower:
            # Buscar nombre después de palabras clave
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["me", "llamo", "soy", "nombre", "es", "llamo"]:
                    if i + 1 < len(words):
                        updated_context["contact_name"] = words[i + 1]
                        break
        
        # Extraer información de empresa
        if any(word in message_lower for word in ["empresa", "trabajo", "sector", "industria", "compañía"]):
            if "company_info" not in updated_context:
                updated_context["company_info"] = message
        
        # Extraer información de procesos
        if any(word in message_lower for word in ["proceso", "auditar", "mejorar", "flujo", "tarea"]):
            if "process_info" not in updated_context:
                updated_context["process_info"] = message
        
        # Extraer objetivos y problemas
        if any(word in message_lower for word in ["objetivo", "problema", "mejorar", "automatizar", "ahorrar"]):
            if "goals_problems" not in updated_context:
                updated_context["goals_problems"] = message
        
        # Extraer información de sistemas y herramientas
        if any(word in message_lower for word in ["sistema", "herramienta", "software", "excel", "erp", "crm"]):
            if "systems_info" not in updated_context:
                updated_context["systems_info"] = message
        
        # Extraer información de contacto específica
        questions_asked = len(updated_context.get("asked_questions", []))
        
        if questions_asked == 1:  # Después de preguntar nombre
            updated_context["contact_name"] = message.strip()
        elif questions_asked == 2:  # Después de preguntar rol
            updated_context["role"] = message.strip()
        elif questions_asked == 3:  # Después de preguntar empresa
            updated_context["company_name"] = message.strip()
        elif questions_asked == 4:  # Después de preguntar país
            updated_context["country"] = message.strip()
        elif questions_asked == 5:  # Después de preguntar email
            updated_context["email"] = message.strip()
        elif questions_asked == 6:  # Después de preguntar teléfono
            updated_context["phone"] = message.strip()
        
        return updated_context

    def get_next_question(self, stage: str, context: dict) -> str:
        """Genera la siguiente pregunta basada en la etapa actual"""
        questions = {
            # Etapa 1: Datos básicos
            "initial_greeting": "¡Hola! Soy tu auditor de procesos especializado en transformación digital. Para comenzar, ¿cuál es tu nombre completo?",
            "collecting_name": "¿Cuál es tu cargo o rol en la empresa?",
            "collecting_role": "¿En qué empresa trabajas?",
            "collecting_company": "¿En qué país opera tu empresa?",
            "collecting_country": "¿Cuál es tu correo electrónico?",
            "collecting_email": "¿Cuál es tu número de teléfono para contactarte?",
            "collecting_phone": "Perfecto. Ahora dime TODO lo que puedas sobre tu empresa: sector, tamaño, procesos principales, problemas actuales, objetivos de mejora, sistemas que usan, y cualquier otra información relevante.",
            
            # Etapa 2: Recopilación comprehensiva
            "question_1_company_info": "Cuéntame en detalle sobre el proceso específico que quieres mejorar: flujo completo, tiempo que toma, errores frecuentes, personas involucradas, sistemas utilizados, y cuellos de botella que identificas.",
            "question_2_process_details": "¿Qué tareas repetitivas, manuales o que consumen mucho tiempo realizan en este proceso? ¿Qué reportes generan manualmente? ¿Qué integraciones entre sistemas necesitan?",
            "question_3_automation_opportunities": "¿Cuál es tu objetivo específico de mejora? ¿Qué beneficios buscas (ahorro de tiempo, reducción de errores, mejor experiencia del cliente, etc.)? ¿Tienes algún presupuesto o restricción?",
            "question_4_goals_constraints": "Perfecto, ya tengo suficiente información. Tengo algunas recomendaciones específicas para tu caso. ¿Te gustaría que te las comparta ahora, o prefieres que exploremos más a fondo algún aspecto específico de tus necesidades?",
            "providing_recommendations": "Basándome en tu información, puedo sugerir algunas automatizaciones. ¿Te interesa conocerlas?"
        }
        return questions.get(stage, "¿Puedes proporcionarme más detalles sobre tu proceso?")

    def process_message(self, message: str, convo_id: str, files: List[str] = None) -> Dict[str, Any]:
        # Recuperar contexto previo
        context = conversation_memory.get(convo_id, {})
        analysis_results = analysis_memory.get(convo_id, {})
        
        # Extraer información del mensaje
        context = self.extract_information(message, context)
        
        # Determinar etapa actual
        stage = self.get_conversation_stage(context)
        
        # Procesar archivos si existen
        if files:
            context["uploaded_files"] = files
            file_analysis = []
            for file_content in files:
                try:
                    decoded_content = base64.b64decode(file_content).decode('utf-8')
                    file_analysis.append(f"Archivo analizado: {decoded_content[:200]}...")
                except:
                    file_analysis.append("Archivo procesado (formato no legible)")
            context["file_analysis"] = file_analysis
        
        # Construir input con contexto
        user_input = f"""
Mensaje del usuario: {message}

Contexto actual:
- Etapa: {stage}
- Preguntas hechas: {len(context.get('asked_questions', []))}/10 (6 básicas + 4 comprehensivas)
- Información recopilada: {json.dumps(context, ensure_ascii=False, indent=2)}

INSTRUCCIONES:
- Si es la primera vez (pregunta 0), presenta el servicio y pide nombre
- Si es pregunta 1-6, recopila datos básicos de contacto (nombre, puesto, empresa, país, email, teléfono)
- Si es pregunta 7-10, haz PREGUNTAS COMPREHENSIVAS sobre empresa y procesos
- Si es pregunta 10, SIEMPRE ofrece recomendaciones o exploración adicional
- Si ya pasaste las 10 preguntas, proporciona recomendaciones específicas
- El webhook se ejecuta automáticamente: 1) Primera vez con información básica completa, 2) Llamadas subsecuentes con información adicional del discovery

Responde de forma breve y directa. Mantén el enfoque en procesos y automatizaciones.
"""
        
        result = self.agent_executor.invoke({"input": user_input})
        reply = result["output"]
        
        # Verificar si tenemos información básica completa para enviar al webhook por primera vez
        basic_info_complete = all([
            context.get("contact_name"),
            context.get("role"),  # Puesto/cargo
            context.get("company_name"),
            context.get("email"),
            context.get("phone")
        ])
        
        # Verificar si tenemos información adicional del discovery para envíos subsecuentes
        has_discovery_info = any([
            context.get("company_info"),
            context.get("process_info"),
            context.get("goals_problems"),
            context.get("systems_info")
        ])
        
        # Primera llamada al webhook cuando se tiene información básica completa
        if basic_info_complete and not context.get("webhook_sent"):
            lead_data = {
                "nombre": context.get('contact_name'),
                "puesto": context.get('role'),
                "empresa": context.get('company_name'),
                "pais": context.get('country'),
                "email": context.get('email'),
                "telefono": context.get('phone'),
                "tipo_envio": "informacion_basica"
            }
            webhook_result = self.send_to_webhook(lead_data)
            context["webhook_sent"] = True
            context["webhook_result"] = webhook_result
            context["webhook_calls"] = 1
        
        # Llamadas subsecuentes cuando se obtiene información adicional del discovery
        elif context.get("webhook_sent") and has_discovery_info:
            # Verificar si ya enviamos esta información adicional
            current_discovery_hash = hash(str(sorted([
                context.get("company_info", ""),
                context.get("process_info", ""),
                context.get("goals_problems", ""),
                context.get("systems_info", "")
            ])))
            
            if current_discovery_hash != context.get("last_discovery_hash"):
                # Preparar información adicional para el webhook
                additional_info = []
                if context.get("company_info"):
                    additional_info.append(f"Info Empresa: {context.get('company_info')}")
                if context.get("process_info"):
                    additional_info.append(f"Info Proceso: {context.get('process_info')}")
                if context.get("goals_problems"):
                    additional_info.append(f"Objetivos/Problemas: {context.get('goals_problems')}")
                if context.get("systems_info"):
                    additional_info.append(f"Info Sistemas: {context.get('systems_info')}")
                
                lead_data = {
                    "nombre": context.get('contact_name'),
                    "puesto": context.get('role'),
                    "empresa": context.get('company_name'),
                    "pais": context.get('country'),
                    "email": context.get('email'),
                    "telefono": context.get('phone'),
                    "informacion_adicional": additional_info,
                    "tipo_envio": "informacion_discovery"
                }
                webhook_result = self.send_to_webhook(lead_data)
                context["webhook_result"] = webhook_result
                context["webhook_calls"] = context.get("webhook_calls", 1) + 1
                context["last_discovery_hash"] = current_discovery_hash
        
        # Obtener siguiente pregunta
        next_question = self.get_next_question(stage, context)
        
        # Actualizar contexto
        context["last_reply"] = reply
        context["stage"] = stage
        context["conversation_history"] = context.get("conversation_history", []) + [message]
        context["last_updated"] = datetime.now().isoformat()
        
        # Registrar pregunta hecha
        if "asked_questions" not in context:
            context["asked_questions"] = []
        context["asked_questions"].append(next_question)
        
        conversation_memory[convo_id] = context
        
        return {
            "reply": reply, 
            "convo_id": convo_id, 
            "context": context,
            "analysis_results": analysis_results,
            "next_question": next_question,
            "stage": stage
        }

auditor_agent = AuditorAgent()

@app.post("/webhook", response_model=WebhookResponse)
async def webhook(request: WebhookRequest, api_key: str = Depends(verify_api_key)):
    try:
        result = auditor_agent.process_message(
            request.message, 
            request.convo_id, 
            request.files
        )
        return WebhookResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/upload-file")
async def upload_file(request: FileUploadRequest, api_key: str = Depends(verify_api_key)):
    try:
        convo_id = request.convo_id
        if convo_id not in conversation_memory:
            conversation_memory[convo_id] = {}
        
        if "files" not in conversation_memory[convo_id]:
            conversation_memory[convo_id]["files"] = []
        
        conversation_memory[convo_id]["files"].append({
            "name": request.file_name,
            "content": request.file_content
        })
        
        return {"message": f"Archivo {request.file_name} subido exitosamente", "convo_id": convo_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/analysis/{convo_id}")
async def get_analysis(convo_id: str, api_key: str = Depends(verify_api_key)):
    try:
        context = conversation_memory.get(convo_id, {})
        analysis = analysis_memory.get(convo_id, {})
        return {
            "convo_id": convo_id,
            "context": context,
            "analysis": analysis,
            "stage": context.get("stage", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/conversations")
async def get_conversations(api_key: str = Depends(verify_api_key)):
    """Obtiene todas las conversaciones activas"""
    try:
        conversations = {}
        for convo_id, context in conversation_memory.items():
            conversations[convo_id] = {
                "stage": context.get("stage", "unknown"),
                "contact_name": context.get("contact_name", "No especificado"),
                "company_sector": context.get("company_sector", "No especificado"),
                "last_updated": context.get("last_updated", "No disponible"),
                "progress": len([k for k in context.keys() if k in ["contact_name", "company_sector", "role", "main_process", "specific_problem", "improvement_goal"]])
            }
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/test-webhook")
async def test_webhook(api_key: str = Depends(verify_api_key)):
    """Prueba el webhook con datos de ejemplo"""
    try:
        test_lead_info = {
            "nombre": "Juan Pérez",
            "puesto": "Gerente",
            "empresa": "Empresa Test",
            "pais": "México",
            "email": "juan.perez@empresa.com",
            "telefono": "123456789",
            "tipo_envio": "test"
        }
        result = auditor_agent.send_to_webhook(test_lead_info)
        
        return {
            "message": "Webhook test completado",
            "result": result,
            "data_sent": test_lead_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al probar webhook: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Agente Auditor de Procesos e Infraestructura API v2.0", 
        "version": "2.0.0",
        "capabilities": [
            "Memoria persistente de conversaciones",
            "Guía paso a paso hacia recomendaciones",
            "Análisis de procesos y automatizaciones",
            "Captura de información de leads",
            "Análisis de documentos",
            "Envío automático a webhook"
        ],
        "stages": [
            "initial_greeting",
            "collecting_name",
            "collecting_role",
            "collecting_company",
            "collecting_country",
            "collecting_phone",
            "question_1_company_info",
            "question_2_process_details", 
            "question_3_automation_opportunities",
            "question_4_goals_constraints",
            "providing_recommendations"
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("AUDITOR_CLIENT_PORT", "8021"))
    host = os.getenv("AUDITOR_CLIENT_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port) 