import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"
#BASE_URL = "https://qontrolserver.fliends.com"
# Client API base URL
CLIENT_BASE_URL = "http://localhost:8001"
#CLIENT_BASE_URL = "https://qontrolclient.fliends.com"
# Get API key from environment
API_KEY = os.getenv("QA_API_KEY")
if not API_KEY:
    print("⚠️  Warning: QA_API_KEY not found in environment variables")
    print("   Please set QA_API_KEY in your .env file or environment")
    API_KEY = "your_api_key_here"  # Fallback for testing

# Get Client API key from environment
CLIENT_API_KEY = os.getenv("QA_API_KEY_CLIENT")
if not CLIENT_API_KEY:
    print("⚠️  Warning: QA_API_KEY_CLIENT not found in environment variables")
    print("   Please set QA_API_KEY_CLIENT in your .env file or environment")
    CLIENT_API_KEY = "your_client_api_key_here"  # Fallback for testing

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# Headers for Client API requests
CLIENT_HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": CLIENT_API_KEY
}




def test_root():
    response = requests.get(f"{BASE_URL}/", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    print("✅ Test root endpoint passed")

def test_crawl():
    url = "https://comparasoftware.com/perfex-crm"
    payload = {"url": url}
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "markdown_content" in data
    assert "url" in data
    assert data["url"] == url
    print("✅ Test crawl endpoint passed")
    print(data)

def test_browser_agent():
    prompt = "login in comparasoftware with user: provider password: provider"
    payload = {"prompt": prompt}
    response = requests.post(f"{BASE_URL}/browser-agent", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "prompt" in data
    assert "model_actions" in data
    assert "screenshots" in data
    assert data["prompt"] == prompt
    print("✅ Test browser agent endpoint passed")
    print(f"Model Actions: {data['model_actions']}")
    print(f"Screenshots: {data['screenshots']}")
    print(data)

def test_youtube_transcript():
    # Example YouTube video URL
    video_url = "https://www.youtube.com/watch?v=ffyKY3Dj5ZE"
    payload = {"url": video_url, "translate_code": "es"}
    response = requests.post(f"{BASE_URL}/youtube-transcript", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "url" in data
    assert data["url"] == video_url
    print("✅ Test youtube transcript endpoint passed")
    print(f"Transcript length: {len(data['transcript'])} characters")
    print(data)

def test_process_prompt():
    """Test the QA Agent API process-prompt endpoint"""
    # prompt = "Entra al contenido de comparasoftware.com y analiza si hay algun error de ortografia o contenido que no sea correcto"
    prompt = "Entra a https://www.comparasoftware.com/ii y analiza si hay algun bug en el contenido."
    payload = {"prompt": prompt}
    
    # Test with valid API key
    response = requests.post(f"{CLIENT_BASE_URL}/process-prompt", json=payload, headers=CLIENT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "console_logs" in data
    assert "model_actions" in data
    assert "screenshots" in data
    assert data["status"] in ["passed", "failed"]
    print("✅ Test process-prompt endpoint passed (with valid API key)")
    print(f"Status: {data['status']}")
    print(f"Console logs length: {len(data['console_logs'])} characters")
    print(f"Model Actions: {data['model_actions']}")
    print(f"Screenshots: {data['screenshots']}")
    print(data)

def test_process_prompt_no_auth():
    """Test the QA Agent API process-prompt endpoint without authentication (should fail)"""
    prompt = "Test the website https://example.com for any broken links or content issues"
    payload = {"prompt": prompt}
    
    # Test without API key (should fail)
    response = requests.post(f"{CLIENT_BASE_URL}/process-prompt", json=payload, headers={"Content-Type": "application/json"})
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid API key" in data["detail"]
    print("✅ Test process-prompt endpoint passed (no auth - correctly rejected)")

def test_process_prompt_wrong_auth():
    """Test the QA Agent API process-prompt endpoint with wrong API key (should fail)"""
    prompt = "Test the website https://example.com for any broken links or content issues"
    payload = {"prompt": prompt}
    
    # Test with wrong API key (should fail)
    wrong_headers = {
        "Content-Type": "application/json",
        "X-API-Key": "wrong_api_key"
    }
    response = requests.post(f"{CLIENT_BASE_URL}/process-prompt", json=payload, headers=wrong_headers)
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid API key" in data["detail"]
    print("✅ Test process-prompt endpoint passed (wrong auth - correctly rejected)")

def test_client_health():
    """Test the QA Agent API health endpoint"""
    response = requests.get(f"{CLIENT_BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "qa_agent_initialized" in data
    assert data["status"] == "healthy"
    print("✅ Test client health endpoint passed")

def test_client_root():
    """Test the QA Agent API root endpoint"""
    response = requests.get(f"{CLIENT_BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "authentication" in data
    assert "endpoints" in data
    print("✅ Test client root endpoint passed")

def test_asesor_webhook_curl():
    """Test the Asesor Agent webhook endpoint using curl-like request"""
    import subprocess
    import json
    
    url = "http://localhost:8021/webhook"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "demo-key"
    }
    convo_id = "prueba123"
    print("\n--- Asesor Agent Interactive Chat ---")
    print("Type 'exit' to end the conversation.")
    
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            print("Ending chat.")
            break

        payload = {
            "message": user_message,
            "convo_id": convo_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            
            if "reply" in data:
                print(f"Asesor: {data['reply']}")
            else:
                print("Asesor: No reply received.")
            
            if "convo_id" in data:
                convo_id = data["convo_id"] # Update convo_id if returned

        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to asesor client server.")
            print("   Make sure the asesor client is running on localhost:8011")
            break
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
            break
        except Exception as e:
            print(f"❌ Error testing asesor webhook: {str(e)}")
            break
    print("✅ Asesor Agent interactive chat ended.")

def test_auditor_webhook_curl():
    """Test the Auditor Agent webhook endpoint using curl-like request"""
    import subprocess
    import json
    
    url = "http://localhost:8021/webhook"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "demo-key"
    }
    convo_id = "auditor_test_123"
    print("\n--- Auditor Agent Interactive Chat ---")
    print("Type 'exit' to end the conversation.")
    print("Type 'status' to see conversation status.")
    print("Type 'reset' to start a new conversation.")
    
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            print("Ending chat.")
            break
        elif user_message.lower() == 'status':
            try:
                response = requests.get(f"http://localhost:8021/analysis/{convo_id}", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Status: {data.get('stage', 'unknown')}")
                    print(f"Progress: {data.get('context', {}).get('progress', 0)}/6")
                    print(f"Contact: {data.get('context', {}).get('contact_name', 'Not specified')}")
                    print(f"Company: {data.get('context', {}).get('company_sector', 'Not specified')}")
                else:
                    print("Could not get status.")
            except Exception as e:
                print(f"Error getting status: {e}")
            continue
        elif user_message.lower() == 'reset':
            convo_id = f"auditor_test_{int(datetime.now().timestamp())}"
            print(f"New conversation ID: {convo_id}")
            continue

        payload = {
            "message": user_message,
            "convo_id": convo_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "reply" in data:
                print(f"Auditor: {data['reply']}")
                if data.get("stage"):
                    print(f"[Stage: {data['stage']}]")
            else:
                print("Auditor: No reply received.")
            
            if "convo_id" in data:
                convo_id = data["convo_id"]

        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to auditor client server.")
            print("   Make sure the auditor client is running on localhost:8021")
            break
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
            break
        except Exception as e:
            print(f"❌ Error testing auditor webhook: {str(e)}")
            break
    print("✅ Auditor Agent interactive chat ended.")

def show_menu():
    print("\n🧪 API Test Menu")
    print("=" * 50)
    print("Server API Tests (localhost:8000):")
    print("1. Test root endpoint (/)")
    print("2. Test crawl endpoint (/crawl)")
    print("3. Test browser agent endpoint (/browser-agent)")
    print("4. Test youtube transcript endpoint (/youtube-transcript)")
    print()
    print("Client API Tests (localhost:8001):")
    print("5. Test client health endpoint (/health)")
    print("6. Test client root endpoint (/)")
    print("7. Test process-prompt endpoint (/process-prompt)")
    print("8. Test process-prompt without auth (should fail)")
    print("9. Test process-prompt with wrong auth (should fail)")
    print()
    print("Agent Tests:")
    print("10. Test asesor webhook (curl-like)")
    print("11. Test auditor webhook (curl-like)")
    print()
    print("12. Run all server tests")
    print("13. Run all client tests")
    print("14. Run all tests")
    print("0. Exit")
    print("=" * 50)

def run_test(choice):
    if choice == 1:
        test_root()
    elif choice == 2:
        test_crawl()
    elif choice == 3:
        test_browser_agent()
    elif choice == 4:
        test_youtube_transcript()
    elif choice == 5:
        test_client_health()
    elif choice == 6:
        test_client_root()
    elif choice == 7:
        test_process_prompt()
    elif choice == 8:
        test_process_prompt_no_auth()
    elif choice == 9:
        test_process_prompt_wrong_auth()
    elif choice == 10:
        test_asesor_webhook_curl()
    elif choice == 11:
        test_auditor_webhook_curl()
    elif choice == 12:
        print("Running all server tests...")
        test_root()
        test_crawl()
        test_browser_agent()
        test_youtube_transcript()
    elif choice == 13:
        print("Running all client tests...")
        test_client_health()
        test_client_root()
        test_process_prompt()
        test_process_prompt_no_auth()
        test_process_prompt_wrong_auth()
    elif choice == 14:
        print("Running all tests...")
        print("\n--- Server Tests ---")
        test_root()
        test_crawl()
        test_browser_agent()
        test_youtube_transcript()
        print("\n--- Client Tests ---")
        test_client_health()
        test_client_root()
        test_process_prompt()
        test_process_prompt_no_auth()
        test_process_prompt_wrong_auth()
        print("\n--- Agent Tests ---")
        test_asesor_webhook_curl()
        test_auditor_webhook_curl()
    else:
        print("❌ Invalid choice. Please select a number between 0-14.")

if __name__ == "__main__":
    print("🧪 Starting API tests...\n")
    print(f"Server API URL: {BASE_URL}")
    print(f"Client API URL: {CLIENT_BASE_URL}")
    print(f"Asesor Client API URL: http://localhost:8011")
    print(f"Auditor Client API URL: https://diticlient.fliends.com")
    print()
    
    while True:
        show_menu()
        try:
            choice = int(input("Enter your choice (0-14): "))
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            
            if 1 <= choice <= 14:
                try:
                    run_test(choice)
                    print("\n✨ Test(s) completed successfully!")
                except AssertionError as e:
                    print(f"\n❌ Test failed: {str(e)}")
                except requests.exceptions.ConnectionError:
                    print("\n❌ Error: Could not connect to the server.")
                    print("   Make sure the server is running on the correct URL")
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        print("\n❌ Error: Invalid or missing API key.")
                        print("   Please check your API key environment variables.")
                    else:
                        print(f"\n❌ HTTP Error: {e.response.status_code} - {e.response.text}")
                except Exception as e:
                    print(f"\n❌ Unexpected error: {str(e)}")
            else:
                print("❌ Invalid choice. Please select a number between 0-14.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        
        input("\nPress Enter to continue...")