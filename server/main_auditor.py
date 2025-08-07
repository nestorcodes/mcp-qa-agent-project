import os
from fastapi import FastAPI, HTTPException, Request, status, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from typing import List, Dict, Any
import re
import requests
import json
from datetime import datetime

load_dotenv()

app = FastAPI(title="Agente Auditor Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("AUDITOR_API_KEY", "demo-key")
WEBHOOK_URL = "https://www.dev.comparasoftware.com/selfhosted-n8n/webhook/98c962dd-700e-44c5-b0d5-cbb72145f8af"

def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

# Modelos Pydantic
class ZohoRequest(BaseModel):
    query: str

class ZohoResponse(BaseModel):
    data: str

class DocumentAnalyzerRequest(BaseModel):
    document_content: str

class DocumentAnalyzerResponse(BaseModel):
    analysis: str

class AuditorService:
    def __init__(self):
        self.conversation_state = {
            "is_first_call": True,
            "extracted_data": {
                "name": None,
                "lastname": None,
                "company": None,
                "phone": None
            },
            "additional_data": {}
        }

    def send_to_webhook(self, data: Dict[str, Any]) -> bool:
        """Envía datos al webhook especificado"""
        try:
            # Agregar timestamp y metadata
            data["timestamp"] = datetime.now().isoformat()
            data["source"] = "auditor_server"
            
            # Hacer request GET al webhook
            response = requests.get(WEBHOOK_URL, params=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Datos enviados exitosamente al webhook: {data}")
                return True
            else:
                print(f"❌ Error al enviar al webhook. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ Timeout al enviar al webhook después de 10 segundos")
            return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Error de conexión al webhook: {WEBHOOK_URL}")
            return False
        except Exception as e:
            print(f"❌ Error al enviar al webhook: {str(e)}")
            return False

    def extract_contact_info(self, document_content: str) -> Dict[str, Any]:
        """Extrae información de contacto del documento"""
        content_lower = document_content.lower()
        
        # Patrones para extraer información
        patterns = {
            "name": [
                r"nombre[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"name[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"señor[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"sr[.\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"señora[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"sra[.\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)"
            ],
            "lastname": [
                r"apellido[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"lastname[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)",
                r"surname[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)"
            ],
            "company": [
                r"empresa[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s\d\-\.]+)",
                r"company[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s\d\-\.]+)",
                r"compañía[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s\d\-\.]+)",
                r"organización[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s\d\-\.]+)",
                r"organization[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ\s\d\-\.]+)"
            ],
            "phone": [
                r"teléfono[:\s]+([\d\-\+\(\)\s]+)",
                r"phone[:\s]+([\d\-\+\(\)\s]+)",
                r"celular[:\s]+([\d\-\+\(\)\s]+)",
                r"mobile[:\s]+([\d\-\+\(\)\s]+)",
                r"(\+\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}"
            ]
        }
        
        extracted = {}
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, document_content, re.IGNORECASE)
                if matches:
                    # Tomar el primer match y limpiarlo
                    value = matches[0].strip()
                    if value and len(value) > 1:  # Evitar valores muy cortos
                        extracted[field] = value
                        break
        
        return extracted

    def zoho_lookup(self, lead_data: str) -> str:
        """Envía datos del lead a Zoho CRM (simulado)"""
        # Simulación de envío de lead a Zoho
        return f"[Zoho Simulado] Lead registrado: {lead_data}"

    def analyze_document(self, document_content: str) -> str:
        """Analiza documentos y archivos"""
        # Extraer información de contacto
        contact_info = self.extract_contact_info(document_content)
        
        # Actualizar el estado de la conversación
        for key, value in contact_info.items():
            if key in self.conversation_state["extracted_data"] and value:
                self.conversation_state["extracted_data"][key] = value
        
        # Preparar datos para el webhook
        webhook_data = {
            "new": 1 if self.conversation_state["is_first_call"] else 0,
            "name": self.conversation_state["extracted_data"]["name"] or "No encontrado",
            "lastname": self.conversation_state["extracted_data"]["lastname"] or "No encontrado", 
            "company": self.conversation_state["extracted_data"]["company"] or "No encontrado",
            "phone": self.conversation_state["extracted_data"]["phone"] or "No encontrado"
        }
        
        # Agregar datos adicionales si los tenemos
        if contact_info:
            webhook_data.update(contact_info)
        
        # Enviar al webhook
        webhook_success = self.send_to_webhook(webhook_data)
        
        # Marcar que ya no es la primera llamada
        if self.conversation_state["is_first_call"]:
            self.conversation_state["is_first_call"] = False
        
        # Extraer información relevante del documento
        content_lower = document_content.lower()
        
        # Detectar patrones comunes
        patterns = {
            "procesos": ["proceso", "flujo", "workflow", "procedimiento"],
            "sistemas": ["sistema", "software", "aplicación", "plataforma"],
            "métricas": ["kpi", "métrica", "indicador", "performance"],
            "problemas": ["problema", "error", "falla", "incidente", "retraso"],
            "costos": ["costo", "presupuesto", "gasto", "inversión"]
        }
        
        findings = {}
        for category, keywords in patterns.items():
            matches = []
            for keyword in keywords:
                if keyword in content_lower:
                    # Extraer contexto alrededor de la palabra clave
                    context = self._extract_context(document_content, keyword)
                    matches.extend(context)
            if matches:
                findings[category] = list(set(matches))[:3]  # Máximo 3 por categoría
        
        analysis = f"""
📄 ANÁLISIS DE DOCUMENTO

🔍 HALLAZGOS PRINCIPALES:
"""
        
        for category, items in findings.items():
            analysis += f"\n{category.upper()}:\n"
            for item in items:
                analysis += f"• {item}\n"
        
        if not findings:
            analysis += "\nNo se encontraron patrones específicos en el documento."
        
        # Agregar información sobre el webhook
        webhook_status = "✅ Enviado exitosamente" if webhook_success else "❌ Error al enviar"
        analysis += f"""

📊 RESUMEN EJECUTIVO:
• Documento analizado: {len(document_content)} caracteres
• Patrones identificados: {len(findings)} categorías
• Información relevante extraída para análisis posterior

🌐 WEBHOOK STATUS: {webhook_status}
• Datos enviados: {json.dumps(webhook_data, indent=2, ensure_ascii=False)}

💡 RECOMENDACIONES:
• Utilizar esta información para complementar el análisis de procesos
• Considerar los hallazgos en las propuestas de automatización
• Validar los datos con el equipo operativo
        """
        
        return analysis.strip()

    def _extract_context(self, text: str, keyword: str, context_chars: int = 100) -> List[str]:
        """Extrae contexto alrededor de una palabra clave"""
        contexts = []
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            
            # Extraer contexto
            context_start = max(0, pos - context_chars)
            context_end = min(len(text), pos + len(keyword) + context_chars)
            context = text[context_start:context_end].strip()
            
            if context:
                contexts.append(context)
            
            start = pos + len(keyword)
            
            if len(contexts) >= 3:  # Máximo 3 contextos
                break
        
        return contexts

# Instancia del servicio
auditor_service = AuditorService()

@app.post("/zoho-lookup", response_model=ZohoResponse)
async def zoho_lookup(request: ZohoRequest, _: None = Depends(verify_api_key)):
    try:
        data = auditor_service.zoho_lookup(request.query)
        return ZohoResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Zoho lookup: {str(e)}")

@app.post("/document-analyzer", response_model=DocumentAnalyzerResponse)
async def document_analyzer(request: DocumentAnalyzerRequest, _: None = Depends(verify_api_key)):
    try:
        analysis = auditor_service.analyze_document(request.document_content)
        return DocumentAnalyzerResponse(analysis=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis de documento: {str(e)}")

@app.post("/reset-conversation")
async def reset_conversation(_: None = Depends(verify_api_key)):
    """Resetea el estado de la conversación"""
    try:
        auditor_service.conversation_state = {
            "is_first_call": True,
            "extracted_data": {
                "name": None,
                "lastname": None,
                "company": None,
                "phone": None
            },
            "additional_data": {}
        }
        return {"message": "Estado de conversación reseteado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al resetear conversación: {str(e)}")

@app.get("/conversation-state")
async def get_conversation_state(_: None = Depends(verify_api_key)):
    """Obtiene el estado actual de la conversación"""
    try:
        return auditor_service.conversation_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado: {str(e)}")

@app.post("/test-webhook")
async def test_webhook(_: None = Depends(verify_api_key)):
    """Prueba el webhook con datos de ejemplo"""
    try:
        test_data = {
            "new": 1,
            "name": "Juan",
            "lastname": "Pérez",
            "company": "Empresa Test",
            "phone": "123456789",
            "test": True
        }
        
        success = auditor_service.send_to_webhook(test_data)
        
        return {
            "message": "Webhook test completado",
            "success": success,
            "data_sent": test_data,
            "webhook_url": WEBHOOK_URL
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al probar webhook: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Agente Auditor Server API", 
        "version": "1.0.0",
        "services": [
            "zoho-lookup",
            "document-analyzer",
            "reset-conversation",
            "conversation-state",
            "test-webhook"
        ],
        "webhook": {
            "url": WEBHOOK_URL,
            "method": "GET",
            "required_fields": ["name", "lastname", "company", "phone"],
            "new_parameter": "1 for first call, 0 for subsequent calls"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("AUDITOR_SERVER_PORT", "8020"))
    host = os.getenv("AUDITOR_SERVER_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port) 