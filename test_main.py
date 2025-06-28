import requests
import json

BASE_URL = "http://localhost:8000"

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

if __name__ == "__main__":
    print("🧪 Starting API tests...\n")
    try:
        #test_root()
        # test_crawl()
        test_browser_agent()
        print("\n✨ All tests passed successfully!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")