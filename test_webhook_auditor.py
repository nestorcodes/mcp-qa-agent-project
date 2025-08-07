#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del webhook del agente auditor
"""

import requests
import json
import time

# Configuración
AUDITOR_URL = "http://localhost:8020"
API_KEY = "demo-key"  # Cambiar según tu configuración

def test_webhook_functionality():
    """Prueba la funcionalidad del webhook"""
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("🧪 INICIANDO PRUEBAS DEL WEBHOOK DEL AUDITOR")
    print("=" * 50)
    
    # Test 1: Primera llamada con información completa
    print("\n📋 TEST 1: Primera llamada con información completa")
    document_1 = """
    Información del Cliente:
    Nombre: Juan Carlos
    Apellido: Rodríguez
    Empresa: TechCorp Solutions
    Teléfono: +1-555-123-4567
    
    Documento de análisis de procesos:
    Nuestro proceso actual de facturación tiene varios problemas:
    - Retrasos en el procesamiento de facturas
    - Errores manuales en la entrada de datos
    - Falta de integración con el sistema de inventario
    """
    
    response = requests.post(
        f"{AUDITOR_URL}/document-analyzer",
        headers=headers,
        json={"document_content": document_1}
    )
    
    if response.status_code == 200:
        print("✅ Test 1 exitoso")
        result = response.json()
        print(f"📊 Análisis: {result['analysis'][:200]}...")
    else:
        print(f"❌ Test 1 falló: {response.status_code} - {response.text}")
    
    time.sleep(2)  # Pausa entre llamadas
    
    # Test 2: Segunda llamada (debería enviar new=0)
    print("\n📋 TEST 2: Segunda llamada (new=0)")
    document_2 = """
    Información adicional:
    El departamento de ventas reporta que el sistema actual
    no permite un seguimiento adecuado de los leads.
    Necesitamos mejorar la integración con el CRM.
    """
    
    response = requests.post(
        f"{AUDITOR_URL}/document-analyzer",
        headers=headers,
        json={"document_content": document_2}
    )
    
    if response.status_code == 200:
        print("✅ Test 2 exitoso")
        result = response.json()
        print(f"📊 Análisis: {result['analysis'][:200]}...")
    else:
        print(f"❌ Test 2 falló: {response.status_code} - {response.text}")
    
    time.sleep(2)
    
    # Test 3: Verificar estado de la conversación
    print("\n📋 TEST 3: Verificar estado de la conversación")
    response = requests.get(
        f"{AUDITOR_URL}/conversation-state",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Test 3 exitoso")
        state = response.json()
        print(f"📊 Estado: {json.dumps(state, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Test 3 falló: {response.status_code} - {response.text}")
    
    # Test 4: Resetear conversación
    print("\n📋 TEST 4: Resetear conversación")
    response = requests.post(
        f"{AUDITOR_URL}/reset-conversation",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Test 4 exitoso")
        result = response.json()
        print(f"📊 Resultado: {result}")
    else:
        print(f"❌ Test 4 falló: {response.status_code} - {response.text}")
    
    # Test 5: Nueva llamada después del reset (debería enviar new=1)
    print("\n📋 TEST 5: Nueva llamada después del reset (new=1)")
    document_3 = """
    Información del nuevo cliente:
    Nombre: María Elena
    Apellido: González
    Empresa: InnovateSoft
    Teléfono: +52-55-9876-5432
    
    Análisis de requerimientos para automatización.
    """
    
    response = requests.post(
        f"{AUDITOR_URL}/document-analyzer",
        headers=headers,
        json={"document_content": document_3}
    )
    
    if response.status_code == 200:
        print("✅ Test 5 exitoso")
        result = response.json()
        print(f"📊 Análisis: {result['analysis'][:200]}...")
    else:
        print(f"❌ Test 5 falló: {response.status_code} - {response.text}")
    
    print("\n" + "=" * 50)
    print("🏁 PRUEBAS COMPLETADAS")

if __name__ == "__main__":
    try:
        test_webhook_functionality()
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor auditor.")
        print("   Asegúrate de que el servidor esté ejecutándose en http://localhost:8020")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}") 