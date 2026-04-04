import requests
try:
    r = requests.get("http://127.0.0.1:5000/api/health", timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")
except Exception as e:
    print(f"Error: {e}")
