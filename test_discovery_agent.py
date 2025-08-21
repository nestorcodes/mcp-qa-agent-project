#!/usr/bin/env python3
"""
Script de prueba para el Discovery Agent modificado
Prueba el nuevo flujo: 3 preguntas básicas + discovery dinámico
"""

import requests
import json
import time
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:8021"
API_KEY = "demo-key"
HEADERS = {"x-api-key": API_KEY}

def test_discovery_agent():
    """Prueba el flujo completo del discovery agent"""
    
    print("🧪 INICIANDO PRUEBA DEL DISCOVERY AGENT")
    print("=" * 50)
    
    # ID único para la conversación
    convo_id = f"test_discovery_{int(time.time())}"
    
    # Simular respuestas del empleado
    employee_responses = [
        "Hola, quiero participar en la entrevista",
        "María González",
        "Analista de Recursos Humanos",
        "Me encargo del reclutamiento, onboarding de empleados y evaluación de desempeño. También manejo la comunicación con candidatos y coordino entrevistas con los gerentes.",
        "Mis procesos principales incluyen: 1) Revisar CVs y filtrar candidatos, 2) Coordinar entrevistas con gerentes, 3) Gestionar el proceso de onboarding, 4) Realizar evaluaciones de desempeño trimestrales, 5) Mantener actualizada la base de datos de empleados.",
        "Para el reclutamiento, primero reviso los CVs que llegan por Workday y LinkedIn. Luego filtro por experiencia y habilidades requeridas. Después coordino con el gerente del área para programar entrevistas. Todo el proceso toma entre 2-3 semanas.",
        "El proceso de onboarding es más complejo. Necesito coordinar con IT para acceso a sistemas, con el gerente para plan de trabajo, y con Recursos Humanos para documentación. A veces hay retrasos porque IT está ocupado con otras prioridades.",
        "Sí, me gustaría que el proceso de onboarding fuera más automatizado. Actualmente tengo que hacer seguimiento manual de cada paso y recordar a las personas cuando deben completar sus tareas.",
        "Uso Workday para gestión de empleados, LinkedIn para reclutamiento, Excel para seguimiento de procesos, y Outlook para comunicación. Workday es útil pero a veces es lento, y Excel requiere mucho trabajo manual.",
        "Me comunico principalmente por email y reuniones semanales. Con los gerentes tengo reuniones quincenales para revisar candidatos y con IT uso tickets del sistema. A veces hay malentendidos por falta de comunicación centralizada."
    ]
    
    print(f"📝 ID de conversación: {convo_id}")
    print(f"👤 Empleado de prueba: {employee_responses[1]} - {employee_responses[2]}")
    print()
    
    # Procesar cada respuesta
    for i, response in enumerate(employee_responses):
        print(f"🔄 Pregunta {i+1}: {response}")
        
        try:
            # Enviar respuesta al discovery agent
            result = requests.post(
                f"{BASE_URL}/discovery-webhook",
                json={
                    "message": response,
                    "convo_id": convo_id,
                    "files": []
                },
                headers=HEADERS
            )
            
            if result.status_code == 200:
                data = result.json()
                print(f"✅ Respuesta del agente: {data['reply']}")
                print(f"📊 Etapa: {data['stage']}")
                print(f"🔍 Siguiente pregunta: {data['next_question']}")
                
                # Verificar si se envió al webhook
                if data.get('context', {}).get('webhook_sent'):
                    print("📤 ✅ Información enviada al webhook")
                
            else:
                print(f"❌ Error en la respuesta: {result.status_code}")
                print(f"Detalle: {result.text}")
                break
                
        except Exception as e:
            print(f"❌ Error al procesar respuesta {i+1}: {str(e)}")
            break
        
        print("-" * 40)
        time.sleep(1)  # Pausa entre preguntas
    
    # Verificar información final
    print("\n📋 VERIFICANDO INFORMACIÓN FINAL")
    print("=" * 50)
    
    try:
        # Obtener conversaciones de discovery
        conversations = requests.get(
            f"{BASE_URL}/discovery-conversations",
            headers=HEADERS
        )
        
        if conversations.status_code == 200:
            data = conversations.json()
            if convo_id in data.get("discovery_conversations", {}):
                conv_info = data["discovery_conversations"][convo_id]
                print(f"✅ Conversación encontrada:")
                print(f"   - Nombre: {conv_info.get('employee_name')}")
                print(f"   - Puesto: {conv_info.get('position')}")
                print(f"   - Etapa: {conv_info.get('stage')}")
                print(f"   - Progreso: {conv_info.get('progress')}")
                print(f"   - Última actualización: {conv_info.get('last_updated')}")
            else:
                print("❌ Conversación no encontrada en el listado")
        else:
            print(f"❌ Error al obtener conversaciones: {conversations.status_code}")
            
    except Exception as e:
        print(f"❌ Error al verificar información final: {str(e)}")
    
    print("\n🎯 PRUEBA COMPLETADA")
    print("=" * 50)

def test_webhook_endpoint():
    """Prueba el endpoint de webhook"""
    
    print("\n🧪 PROBANDO ENDPOINT DE WEBHOOK")
    print("=" * 50)
    
    try:
        result = requests.post(
            f"{BASE_URL}/test-webhook",
            headers=HEADERS
        )
        
        if result.status_code == 200:
            data = result.json()
            print("✅ Webhook funcionando correctamente")
            print(f"📤 Datos enviados: {data.get('data_sent')}")
            print(f"📋 Resultado: {data.get('result')}")
        else:
            print(f"❌ Error en webhook: {result.status_code}")
            print(f"Detalle: {result.text}")
            
    except Exception as e:
        print(f"❌ Error al probar webhook: {str(e)}")

def test_api_status():
    """Prueba el estado de la API"""
    
    print("\n🧪 VERIFICANDO ESTADO DE LA API")
    print("=" * 50)
    
    try:
        result = requests.get(f"{BASE_URL}/")
        
        if result.status_code == 200:
            data = result.json()
            print("✅ API funcionando correctamente")
            print(f"📊 Versión: {data.get('version')}")
            print(f"🎯 Mensaje: {data.get('message')}")
            
            # Verificar información del discovery agent
            if "discovery" in data.get("agents", {}):
                discovery_info = data["agents"]["discovery"]
                print(f"🔍 Discovery Agent:")
                print(f"   - Descripción: {discovery_info.get('description')}")
                print(f"   - Endpoint: {discovery_info.get('endpoint')}")
                print(f"   - Etapas: {discovery_info.get('stages')}")
            else:
                print("❌ Información del discovery agent no encontrada")
                
        else:
            print(f"❌ Error en API: {result.status_code}")
            
    except Exception as e:
        print(f"❌ Error al verificar API: {str(e)}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL DISCOVERY AGENT MODIFICADO")
    print("=" * 60)
    
    # Verificar que la API esté funcionando
    test_api_status()
    
    # Probar el webhook
    test_webhook_endpoint()
    
    # Probar el flujo completo del discovery agent
    test_discovery_agent()
    
    print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
    print("=" * 60)
