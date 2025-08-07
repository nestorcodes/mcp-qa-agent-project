#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del webhook
"""

import requests
import json
import time

# Configuración
CLIENT_URL = "http://localhost:8021"
SERVER_URL = "http://localhost:8020"
API_KEY = "demo-key"

def test_server_webhook():
    """Prueba el webhook del servidor"""
    print("🔧 Probando webhook del servidor...")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/test-webhook",
            headers={"x-api-key": API_KEY}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Servidor webhook exitoso: {result}")
            return True
        else:
            print(f"❌ Error en servidor webhook: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando al servidor: {str(e)}")
        return False

def test_client_webhook():
    """Prueba el webhook del cliente"""
    print("🔧 Probando webhook del cliente...")
    
    try:
        response = requests.post(
            f"{CLIENT_URL}/test-webhook",
            headers={"x-api-key": API_KEY}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cliente webhook exitoso: {result}")
            return True
        else:
            print(f"❌ Error en cliente webhook: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando al cliente: {str(e)}")
        return False

def test_client_conversation():
    """Prueba una conversación completa en el cliente"""
    print("🔧 Probando conversación en el cliente...")
    
    try:
        # Mensaje inicial
        response = requests.post(
            f"{CLIENT_URL}/webhook",
            headers={"x-api-key": API_KEY},
            json={
                "message": "Hola, me llamo Juan Pérez y trabajo como Gerente en ABC Company",
                "convo_id": "test_conversation_001",
                "files": []
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Conversación iniciada: {result['reply'][:100]}...")
            return True
        else:
            print(f"❌ Error en conversación: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en conversación: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de webhook...")
    print("=" * 50)
    
    # Probar servidor
    server_success = test_server_webhook()
    print()
    
    # Probar cliente
    client_success = test_client_webhook()
    print()
    
    # Probar conversación
    conversation_success = test_client_conversation()
    print()
    
    # Resumen
    print("=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"Servidor webhook: {'✅ EXITOSO' if server_success else '❌ FALLIDO'}")
    print(f"Cliente webhook: {'✅ EXITOSO' if client_success else '❌ FALLIDO'}")
    print(f"Conversación: {'✅ EXITOSO' if conversation_success else '❌ FALLIDO'}")
    
    if all([server_success, client_success, conversation_success]):
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los logs para más detalles.")

if __name__ == "__main__":
    main() 