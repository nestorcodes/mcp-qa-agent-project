import requests
import json

# BASE_URL = "http://localhost:8000"
BASE_URL = "http://64.227.81.67:5001"


def test_root():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    print("✅ Test root endpoint passed")

def test_crawl():
    url = "https://www.comparasoftware.com"
    payload = {"url": url}
    response = requests.post(f"{BASE_URL}/crawl", json=payload)
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
    response = requests.post(f"{BASE_URL}/browser-agent", json=payload)
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
    response = requests.post(f"{BASE_URL}/youtube-transcript", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "url" in data
    assert data["url"] == video_url
    print("✅ Test youtube transcript endpoint passed")
    print(f"Transcript length: {len(data['transcript'])} characters")
    print(data)

def show_menu():
    print("\n🧪 API Test Menu")
    print("=" * 30)
    print("1. Test root endpoint (/)")
    print("2. Test crawl endpoint (/crawl)")
    print("3. Test browser agent endpoint (/browser-agent)")
    print("4. Test youtube transcript endpoint (/youtube-transcript)")
    print("5. Run all tests")
    print("0. Exit")
    print("=" * 30)

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
        print("Running all tests...")
        test_root()
        test_crawl()
        test_browser_agent()
        test_youtube_transcript()
    else:
        print("❌ Invalid choice. Please select a number between 0-5.")

if __name__ == "__main__":
    print("🧪 Starting API tests...\n")
    
    while True:
        show_menu()
        try:
            choice = int(input("Enter your choice (0-5): "))
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            
            if 1 <= choice <= 5:
                try:
                    run_test(choice)
                    print("\n✨ Test(s) completed successfully!")
                except AssertionError as e:
                    print(f"\n❌ Test failed: {str(e)}")
                except requests.exceptions.ConnectionError:
                    print("\n❌ Error: Could not connect to the server. Make sure the server is running on http://localhost:8000")
                except Exception as e:
                    print(f"\n❌ Unexpected error: {str(e)}")
            else:
                print("❌ Invalid choice. Please select a number between 0-5.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        
        input("\nPress Enter to continue...")