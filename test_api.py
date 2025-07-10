import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_BASE = os.getenv("OPENROUTER_API_BASE")
MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME")

def test_openrouter():
    if not API_KEY:
        print("❌ Missing API key.")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": "Hello! What is 2 + 2?"}],
        "max_tokens": 50,
        "temperature": 0.0
    }

    try:
        response = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        message = result["choices"][0]["message"]["content"]
        print("✅ Response:", message)
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                print("Details:", e.response.json())
            except:
                print("Raw Response:", e.response.text)

if __name__ == "__main__":
    test_openrouter()
