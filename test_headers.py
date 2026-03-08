import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test():
    # Login
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    token = response.json()["access_token"]
    
    payload = b'{"document": "01", "customer": {"identification_document_id": 3, "identification": "123"}, "items": [{"code_reference": "ref", "name": "item"}]}'
    
    print("Testing Content-Type: application/json; charset=utf-8")
    headers1 = {
        "Authorization": f"Bearer {token}",
        "x-factus-token": "mock-token",
        "Content-Type": "application/json; charset=utf-8"
    }
    r1 = requests.post(f"{BASE_URL}/invoices/", data=payload, headers=headers1)
    print(f"application/json; charset=utf-8 -> {r1.status_code}")
    print(r1.text)

if __name__ == "__main__":
    test()
