import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"
# BASE_URL = "http://64.227.81.67:5001"

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

# Client API base URL
CLIENT_BASE_URL = "http://localhost:8001"


def test_root():
    response = requests.get(f"{BASE_URL}/", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    print("✅ Test root endpoint passed")

def test_crawl():
    url = "https://www.comparasoftware.com"
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
    assert data["prompt"] == prompt
    print("✅ Test browser agent endpoint passed")
    print(data)

def test_youtube_transcript():
    # Example YouTube video URL
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
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
    prompt = "Entra al contenido de comparasoftware.com y analiza si hay algun error de ortografia o contenido que no sea correcto"
    payload = {"prompt": prompt}
    
    # Test with valid API key
    response = requests.post(f"{CLIENT_BASE_URL}/process-prompt", json=payload, headers=CLIENT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "console_logs" in data
    assert data["status"] in ["passed", "failed"]
    print("✅ Test process-prompt endpoint passed (with valid API key)")
    print(f"Status: {data['status']}")
    print(f"Console logs length: {len(data['console_logs'])} characters")
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
    print("10. Run all server tests")
    print("11. Run all client tests")
    print("12. Run all tests")
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
        print("Running all server tests...")
        test_root()
        test_crawl()
        test_browser_agent()
        test_youtube_transcript()
    elif choice == 11:
        print("Running all client tests...")
        test_client_health()
        test_client_root()
        test_process_prompt()
        test_process_prompt_no_auth()
        test_process_prompt_wrong_auth()
    elif choice == 12:
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
    else:
        print("❌ Invalid choice. Please select a number between 0-12.")

if __name__ == "__main__":
    print("🧪 Starting API tests...\n")
    print(f"Server API URL: {BASE_URL}")
    print(f"Client API URL: {CLIENT_BASE_URL}")
    print()
    
    while True:
        show_menu()
        try:
            choice = int(input("Enter your choice (0-12): "))
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            
            if 1 <= choice <= 12:
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
                print("❌ Invalid choice. Please select a number between 0-12.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        
        input("\nPress Enter to continue...")