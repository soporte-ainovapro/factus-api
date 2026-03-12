import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000/api"

payload = {
    "document": "01",
    "numbering_range_id": 8,
    "reference_code": "FAC-001",
    "observation": "Prueba de factura",
    "payment_method_code": "10",
    "payment_form": "1",
    "customer": {
        "identification_document_id": 3,
        "identification": "123456789",
        "names": "Juan Perez",
        "address": "Calle 123",
        "email": "juan@example.com",
        "phone": "3001234567",
        "municipality_id": 980,
        "legal_organization_id": 2,
        "tribute_id": 21
    },
    "items": [
        {
            "code_reference": "PROD-001",
            "name": "Producto de prueba",
            "quantity": 1,
            "price": "10000.00",
            "discount_rate": "0.00",
            "tax_rate": "19.00",
            "unit_measure_id": 70,
            "standard_code_id": 1,
            "is_excluded": 0,
            "tribute_id": 1
        }
    ]
}

async def test_payload():
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_data = {"username": "admin", "password": "admin123"}
        response = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code != 200:
            print("Login failed")
            return
        token = response.json()["access_token"]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "x-factus-token": "mock-token",
            "Content-Type": "application/json"
        }
        
        # We send as a correct json object to test if Pydantic validates it well
        response = await client.post(
            f"{BASE_URL}/invoices/",
            json=payload,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception:
            print(f"Response (text): {response.text}")

if __name__ == "__main__":
    asyncio.run(test_payload())
