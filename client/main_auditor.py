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
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=self.api_key)
        
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

Tu objetivo es recopilar información de contacto básica, luego explorar la empresa y sus procesos en 4 PREGUNTAS DE DISCOVERY, y finalmente proporcionar recomendaciones específicas.

REGLAS FUNDAMENTALES:
1. SIEMPRE mantén memoria de lo que ya has preguntado - NO REPITAS PREGUNTAS
2. Haz UNA SOLA PREGUNTA a la vez
3. Respuestas CLARAS y BREVES (máximo 2-3 líneas)
4. Enfócate en PROCESOS y AUTOMATIZACIONES
5. Después de recopilar datos básicos + 4 preguntas de discovery, SIEMPRE ofrece recomendaciones

FLUJO DE AUDITORÍA INTELIGENTE:

ETAPA 1: RECOPILACIÓN DE DATOS BÁSICOS (6 preguntas)
Recopilar información de contacto en este orden:
1. Nombre completo
2. Rol o cargo en la empresa
3. Nombre de la empresa
4. País donde opera
5. Correo electrónico
6. Teléfono de contacto

ETAPA 2: DISCOVERY DE PROCESOS Y NECESIDADES (4 preguntas)
Objetivo: Explorar la operación de la empresa, sus dinámicas y oportunidades de mejora.

PREGUNTA 1: Contexto general del negocio
"Para comenzar con el análisis, ¿me podrías contar un poco sobre tu empresa y cómo opera actualmente?"

PREGUNTA 2: Procesos actuales
"¿Hay procesos dentro de la empresa que sientes que podrían ser más ágiles, digitales o eficientes?"

PREGUNTA 3: Puntos de dolor
"¿Qué tareas o actividades te parecen especialmente repetitivas, manuales o que consumen mucho tiempo en el día a día del equipo?"

PREGUNTA 4: Sistemas y gestión de información
"¿Cómo gestionan actualmente la información para tomar decisiones o dar seguimiento a procesos?"

ETAPA 3: RECOMENDACIONES
Después de completar el discovery, SIEMPRE ofrecer:
"Perfecto, ya tengo suficiente información sobre tu empresa y procesos. Tengo algunas recomendaciones específicas para tu caso. ¿Te gustaría que te las comparta ahora, o prefieres que exploremos más a fondo algún aspecto específico de tus necesidades?"

REGISTRO DE LEADS:
- Primera llamada: Después de recopilar información básica completa (nombre, puesto, empresa, país, email, teléfono)
- Segunda llamada: Después de completar el discovery completo (4 preguntas adicionales)

USO DE HERRAMIENTAS:
- **document_analyzer**: Usar si el usuario comparte documentos
- **send_to_webhook**: Se ejecuta automáticamente cuando se tiene información completa

FORMATO DE RESPUESTA:
- Respuesta breve y directa
- Una sola pregunta por mensaje
- Después de datos básicos + 4 preguntas de discovery, SIEMPRE ofrecer recomendaciones
- Mostrar progreso del análisis

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
            webhook_url = os.getenv("WEBHOOK_URL", "https://www.dev.comparasoftware.com/selfhosted-n8n/webhook/b266d5b5-833d-492c-8730-4063ed75f5d0")
            
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
        # Etapa 2: Discovery de procesos y necesidades (4 preguntas)
        elif questions_asked == 7:
            return "discovery_business_context"
        elif questions_asked == 8:
            return "discovery_current_processes"
        elif questions_asked == 9:
            return "discovery_pain_points"
        elif questions_asked == 10:
            return "discovery_goals_systems"
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
        
        # Extraer información específica basada en la pregunta actual
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
        elif questions_asked == 7:  # Discovery: contexto del negocio
            updated_context["company_info"] = message.strip()
        elif questions_asked == 8:  # Discovery: procesos actuales
            updated_context["process_info"] = message.strip()
        elif questions_asked == 9:  # Discovery: puntos de dolor
            updated_context["goals_problems"] = message.strip()
        elif questions_asked == 10:  # Discovery: sistemas y objetivos
            updated_context["systems_info"] = message.strip()
        
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
            "discovery_business_context": "Para comenzar con el análisis, ¿me podrías contar un poco sobre tu empresa y cómo opera actualmente?",
            "discovery_current_processes": "¿Hay procesos dentro de la empresa que sientes que podrían ser más ágiles, digitales o eficientes?",
            "discovery_pain_points": "¿Qué tareas o actividades te parecen especialmente repetitivas, manuales o que consumen mucho tiempo en el día a día del equipo?",
            "discovery_goals_systems": "¿Cómo gestionan actualmente la información para tomar decisiones o dar seguimiento a procesos?",
            "providing_recommendations": "Perfecto, ya tengo suficiente información sobre tu empresa y procesos. Tengo algunas recomendaciones específicas para tu caso. ¿Te gustaría que te las comparta ahora, o prefieres que exploremos más a fondo algún aspecto específico de tus necesidades?"
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
- Preguntas hechas: {len(context.get('asked_questions', []))}/11 (6 básicas + 4 discovery + 1 recomendaciones)
- Información recopilada: {json.dumps(context, ensure_ascii=False, indent=2)}

INSTRUCCIONES:
- Si es la primera vez (pregunta 0), presenta el servicio y pide nombre
- Si es pregunta 1-6, recopila datos básicos de contacto (nombre, puesto, empresa, país, email, teléfono)
- Si es pregunta 7-10, haz PREGUNTAS DE DISCOVERY sobre empresa, procesos y necesidades
- Si es pregunta 11, SIEMPRE ofrece recomendaciones o exploración adicional
- Si ya pasaste las 11 preguntas, proporciona recomendaciones específicas
- El webhook se ejecuta automáticamente: 1) Primera vez con información básica completa, 2) Segunda vez después del discovery completo

Responde de forma breve y directa. Mantén el enfoque en procesos y automatizaciones.
"""
        
        result = self.agent_executor.invoke({"input": user_input})
        reply = result["output"]
        
        # Verificar si tenemos información básica completa para enviar al webhook por primera vez
        basic_info_complete = all([
            context.get("contact_name"),
            context.get("role"),  # Puesto/cargo
            context.get("company_name"),
            context.get("country"),
            context.get("email"),
            context.get("phone")
        ])
        
        # Primera llamada al webhook cuando se tiene información básica completa
        if basic_info_complete and not context.get("webhook_basic_sent"):
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
            context["webhook_basic_sent"] = True
            context["webhook_result"] = webhook_result
            context["webhook_calls"] = 1
        
        # Segunda llamada al webhook cuando se completa el discovery (después de la pregunta 11)
        elif context.get("webhook_basic_sent") and len(context.get("asked_questions", [])) > 11 and not context.get("webhook_discovery_sent"):
            # Preparar información adicional del discovery
            discovery_info = []
            if context.get("company_info"):
                discovery_info.append(f"Info Empresa: {context.get('company_info')}")
            if context.get("process_info"):
                discovery_info.append(f"Info Proceso: {context.get('process_info')}")
            if context.get("goals_problems"):
                discovery_info.append(f"Objetivos/Problemas: {context.get('goals_problems')}")
            if context.get("systems_info"):
                discovery_info.append(f"Info Sistemas: {context.get('systems_info')}")
            
            lead_data = {
                "nombre": context.get('contact_name'),
                "puesto": context.get('role'),
                "empresa": context.get('company_name'),
                "pais": context.get('country'),
                "email": context.get('email'),
                "telefono": context.get('phone'),
                "informacion_adicional": discovery_info,
                "tipo_envio": "informacion_discovery"
            }
            webhook_result = self.send_to_webhook(lead_data)
            context["webhook_discovery_sent"] = True
            context["webhook_result"] = webhook_result
            context["webhook_calls"] = context.get("webhook_calls", 1) + 1
        
        # Obtener siguiente pregunta
        next_question = self.get_next_question(stage, context)
        
        # Si acabamos de completar el discovery (pregunta 10), mostrar pregunta de recomendaciones
        if len(context.get("asked_questions", [])) == 10 and stage == "discovery_goals_systems":
            next_question = self.get_next_question("providing_recommendations", context)
        
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

class DiscoveryAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.server_url = os.getenv("AUDITOR_SERVER_URL", "http://localhost:8020")
        self.auditor_api_key = os.getenv("AUDITOR_API_KEY", "demo-key")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=self.api_key)
        
        self.tools = [
            Tool(
                name="send_to_webhook",
                func=self.send_to_webhook,
                description="Envía información del empleado entrevistado al webhook externo."
            )
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un Agente de Discovery especializado en entrevistar empleados y colaboradores para entender sus roles, funciones y procesos diarios dentro de la compañía.

Tu objetivo es:
1. Hacer una presentación clara del propósito de la entrevista
2. Recopilar datos básicos del empleado (nombre, rol, descripción del rol)
3. Realizar discovery dinámico sobre sus procesos diarios y cómo los ejecuta

REGLAS FUNDAMENTALES:
1. SIEMPRE mantén memoria de lo que ya has preguntado - NO REPITAS PREGUNTAS
2. Haz UNA SOLA PREGUNTA a la vez
3. Respuestas CLARAS y BREVES (máximo 2-3 líneas)
4. Enfócate en PROCESOS DIARIOS y CÓMO se ejecutan
5. Haz preguntas de profundización dinámicas basadas en las respuestas del empleado
6. Adapta tus preguntas según la información que vayas descubriendo

FLUJO DE ENTREVISTA:

ETAPA 1: PRESENTACIÓN Y DATOS BÁSICOS (3 preguntas fijas)
1. Presentación: "Hola, soy un agente de discovery que está entrevistando a empleados para entender mejor los procesos y roles dentro de la compañía. ¿Me podrías contar tu nombre completo?"
2. Rol: "¿Cuál es tu rol o cargo en la empresa?"
3. Descripción del rol: "¿Podrías darme una pequeña descripción de tu rol y qué responsabilidades tienes?"

ETAPA 2: DISCOVERY DINÁMICO DE PROCESOS (Preguntas adaptativas)
Objetivo: Entender qué hace el empleado en su día a día y cómo ejecuta sus procesos.

Después de las 3 preguntas básicas, comienza a hacer preguntas de discovery:
- Pregunta sobre procesos principales: "Cuéntame, ¿qué procesos o tareas principales realizas en tu día a día?"
- Basándote en su respuesta, haz preguntas de profundización específicas:
  * Si menciona un proceso específico: "¿Podrías explicarme paso a paso cómo ejecutas [PROCESO]? ¿Qué herramientas usas y cuánto tiempo toma?"
  * Si menciona tiempo: "¿Cuánto tiempo toma cada paso de este proceso?"
  * Si menciona personas: "¿Quiénes están involucrados en este proceso y cuál es el rol de cada uno?"
  * Si menciona herramientas: "¿Cómo te ayuda específicamente [HERRAMIENTA] en este proceso?"
  * Si menciona coordinación: "¿Cómo se coordina este proceso con otros departamentos?"
  * Si menciona problemas: "¿Qué dificultades encuentras en este proceso?"
  * Si menciona mejoras: "¿Qué te gustaría mejorar en este proceso?"

TÉCNICAS DE PROFUNDIZACIÓN DINÁMICA:
- Escucha atentamente cada respuesta y haz preguntas específicas sobre lo que mencionen
- No sigas un script fijo, adapta tus preguntas según la información que vayas descubriendo
- Profundiza en los procesos que parezcan más importantes o complejos
- Pregunta sobre herramientas, tiempo, coordinación, problemas y mejoras
- Mantén el enfoque en entender los procesos paso a paso

FORMATO DE RESPUESTA:
- Respuesta breve y directa
- Una sola pregunta por mensaje
- Después de cada respuesta del empleado, haz una pregunta de profundización relacionada
- Muestra interés genuino en los detalles de los procesos
- Adapta tus preguntas según lo que hayas descubierto

NO hagas múltiples preguntas en un solo mensaje. Mantén el enfoque en entender los procesos diarios y cómo se ejecutan de forma dinámica y adaptativa."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def send_to_webhook(self, employee_info: dict) -> str:
        """Envía información del empleado entrevistado al webhook externo"""
        try:
            webhook_url = os.getenv("WEBHOOK_URL", "https://www.dev.comparasoftware.com/selfhosted-n8n/webhook/b266d5b5-833d-492c-8730-4063ed75f5d0")
            
            webhook_data = {
                "employee_info": json.dumps(employee_info, ensure_ascii=False),
                "timestamp": datetime.now().isoformat(),
                "source": "discovery_agent"
            }
            
            response = requests.get(webhook_url, params=webhook_data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Datos del empleado enviados exitosamente al webhook: {webhook_data}")
                return f"✅ Información del empleado enviada al webhook: {json.dumps(employee_info, ensure_ascii=False)}"
            else:
                print(f"❌ Error al enviar al webhook. Status: {response.status_code}, Response: {response.text}")
                return f"❌ Error al enviar al webhook: Status {response.status_code}"
                
        except Exception as e:
            print(f"❌ Error al enviar al webhook: {str(e)}")
            return f"❌ Error al enviar al webhook: {str(e)}"

    def get_conversation_stage(self, context: dict) -> str:
        """Determina la etapa actual de la entrevista"""
        questions_asked = len(context.get("asked_questions", []))
        
        if questions_asked == 0:
            return "presentation"
        elif questions_asked == 1:
            return "collecting_name"
        elif questions_asked == 2:
            return "collecting_role"
        elif questions_asked == 3:
            return "collecting_role_description"
        else:
            return "discovery_dynamic"

    def extract_information(self, message: str, context: dict) -> dict:
        """Extrae información específica del mensaje del empleado"""
        message_lower = message.lower()
        updated_context = context.copy()
        
        if "user_responses" not in updated_context:
            updated_context["user_responses"] = []
        updated_context["user_responses"].append(message)
        
        questions_asked = len(updated_context.get("asked_questions", []))
        
        if questions_asked == 1:  # Después de preguntar nombre
            updated_context["employee_name"] = message.strip()
        elif questions_asked == 2:  # Después de preguntar rol
            updated_context["role"] = message.strip()
        elif questions_asked == 3:  # Después de preguntar descripción del rol
            updated_context["role_description"] = message.strip()
        # Para las preguntas de discovery dinámico, no extraemos información específica
        # ya que el agente debe adaptarse dinámicamente
        
        return updated_context

    def get_next_question(self, stage: str, context: dict) -> str:
        """Genera la siguiente pregunta basada en la etapa actual"""
        questions = {
            "presentation": "Hola, soy un agente de discovery que está entrevistando a empleados para entender mejor los procesos y roles dentro de la compañía. ¿Me podrías contar tu nombre completo?",
            "collecting_name": "¿Cuál es tu rol o cargo en la empresa?",
            "collecting_role": "¿Podrías darme una pequeña descripción de tu rol y qué responsabilidades tienes?",
            "collecting_role_description": "Cuéntame, ¿qué procesos o tareas principales realizas en tu día a día?",
            "discovery_dynamic": "Basándome en lo que me has contado, ¿podrías explicarme más detalles sobre uno de estos procesos? ¿Cómo lo ejecutas paso a paso?"
        }
        return questions.get(stage, "¿Puedes proporcionarme más detalles sobre ese proceso?")

    def process_message(self, message: str, convo_id: str, files: List[str] = None) -> Dict[str, Any]:
        # Recuperar contexto previo
        context = conversation_memory.get(convo_id, {})
        
        # Extraer información del mensaje
        context = self.extract_information(message, context)
        
        # Determinar etapa actual
        stage = self.get_conversation_stage(context)
        
        # Construir input con contexto
        user_input = f"""
Mensaje del empleado: {message}

Contexto actual:
- Etapa: {stage}
- Preguntas hechas: {len(context.get('asked_questions', []))}
- Información recopilada: {json.dumps(context, ensure_ascii=False, indent=2)}

INSTRUCCIONES:
- Si es la primera vez (pregunta 0), presenta el servicio y pide nombre
- Si es pregunta 1-3, recopila datos básicos (nombre, rol, descripción del rol)
- Si es pregunta 4 o más, haz PREGUNTAS DE DISCOVERY DINÁMICAS sobre procesos diarios
- Adapta tus preguntas según las respuestas del empleado
- Profundiza en los procesos que mencionen, preguntando sobre herramientas, tiempo, coordinación, etc.
- Haz preguntas de profundización específicas basadas en lo que vayas descubriendo

Responde de forma breve y directa. Mantén el enfoque en procesos diarios y su ejecución de forma dinámica.
"""
        
        result = self.agent_executor.invoke({"input": user_input})
        reply = result["output"]
        
        # Verificar si tenemos información básica completa para enviar al webhook
        basic_info_complete = all([
            context.get("employee_name"),
            context.get("role"),
            context.get("role_description")
        ])
        
        # Enviar al webhook cuando se tiene información básica completa
        if basic_info_complete and not context.get("webhook_sent"):
            employee_data = {
                "nombre": context.get('employee_name'),
                "rol": context.get('role'),
                "descripcion_rol": context.get('role_description'),
                "tipo_entrevista": "discovery_empleado"
            }
            webhook_result = self.send_to_webhook(employee_data)
            context["webhook_sent"] = True
            context["webhook_result"] = webhook_result
        
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
            "next_question": next_question,
            "stage": stage
        }

# Instanciar el agente de discovery
discovery_agent = DiscoveryAgent()

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

@app.post("/discovery-webhook", response_model=WebhookResponse)
async def discovery_webhook(request: WebhookRequest, api_key: str = Depends(verify_api_key)):
    """Endpoint para el agente de discovery que entrevista empleados"""
    try:
        result = discovery_agent.process_message(
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

@app.get("/discovery-analysis/{convo_id}")
async def get_discovery_analysis(convo_id: str, api_key: str = Depends(verify_api_key)):
    """Obtiene el análisis de una entrevista de discovery específica"""
    try:
        context = conversation_memory.get(convo_id, {})
        return {
            "convo_id": convo_id,
            "context": context,
            "stage": context.get("stage", "unknown"),
            "employee_info": {
                "nombre": context.get("employee_name", "No especificado"),
                "puesto": context.get("position", "No especificado"),
                "papel_empresa": context.get("role_responsibility", "No especificado"),
                "procesos_principales": context.get("main_processes", "No especificado"),
                "detalles_ejecucion": context.get("process_execution_details", "No especificado"),
                "coordinacion": context.get("coordination_details", "No especificado"),
                "areas_mejora": context.get("improvement_areas", "No especificado"),
                "herramientas_sistemas": context.get("tools_systems", "No especificado"),
                "colaboracion": context.get("collaboration_processes", "No especificado")
            },
            "progress": len([k for k in context.keys() if k in ["employee_name", "position", "role_responsibility", "main_processes", "process_execution_details", "coordination_details", "improvement_areas", "tools_systems", "collaboration_processes"]])
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

@app.get("/discovery-conversations")
async def get_discovery_conversations(api_key: str = Depends(verify_api_key)):
    """Obtiene todas las entrevistas de discovery activas"""
    try:
        discovery_conversations = {}
        for convo_id, context in conversation_memory.items():
            # Solo incluir conversaciones que tengan información de empleado
            if context.get("employee_name") or context.get("position"):
                discovery_conversations[convo_id] = {
                    "stage": context.get("stage", "unknown"),
                    "employee_name": context.get("employee_name", "No especificado"),
                    "position": context.get("position", "No especificado"),
                    "papel_empresa": context.get("role_responsibility", "No especificado"),
                    "last_updated": context.get("last_updated", "No disponible"),
                    "progress": len([k for k in context.keys() if k in ["employee_name", "position", "role_responsibility", "main_processes", "process_execution_details", "coordination_details", "improvement_areas", "tools_systems", "collaboration_processes"]])
                }
        return {"discovery_conversations": discovery_conversations}
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
            "Envío automático a webhook",
            "Agente de Discovery para entrevistas a empleados"
        ],
        "agents": {
            "auditor": {
                "description": "Agente auditor de procesos empresariales",
                "endpoint": "/webhook",
                "stages": [
                    "initial_greeting",
                    "collecting_name",
                    "collecting_role",
                    "collecting_company",
                    "collecting_country",
                    "collecting_email",
                    "collecting_phone",
                    "discovery_business_context",
                    "discovery_current_processes", 
                    "discovery_pain_points",
                    "discovery_goals_systems",
                    "providing_recommendations"
                ]
            },
            "discovery": {
                "description": "Agente de discovery para entrevistar empleados",
                "endpoint": "/discovery-webhook",
                "stages": [
                    "presentation",
                    "collecting_name",
                    "collecting_role",
                    "collecting_role_description",
                    "discovery_dynamic"
                ]
            }
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("AUDITOR_CLIENT_PORT", "8021"))
    host = os.getenv("AUDITOR_CLIENT_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port) 