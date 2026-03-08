import httpx
import json
import asyncio

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_no_header():
    try:
        async with httpx.AsyncClient() as client:
            # 1. Login
            login_data = {"username": "admin", "password": "admin123"}
            response = await client.post(f"{BASE_URL}/auth/login", data=login_data)
            token = response.json()["access_token"]

            # 2. Create Invoice WITHOUT Content-Type header
            invoice_data = {
                "document": "01",
                "reference_code": "FAC-1772977296571",
                "customer": {
                    "identification_document_id": 3,
                    "identification": "123456789",
                    "legal_organization_id": 2,
                    "tribute_id": 21
                },
                "items": [
                    {
                        "code_reference": "PROD-001",
                        "name": "Prod",
                        "quantity": 1,
                        "price": "100.00",
                        "tax_rate": "19.00",
                        "unit_measure_id": 1,
                        "standard_code_id": 1,
                        "is_excluded": 0,
                        "tribute_id": 1
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "x-factus-token": "mock-token"
            }
            
            # Send as data (not json argument) and no Content-Type header
            response = await client.post(f"{BASE_URL}/invoices/", content=json.dumps(invoice_data), headers=headers)
            print(f"Status Code (No Header): {response.status_code}")
            print(f"Response (No Header): {json.dumps(response.json(), indent=2)}")

    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_no_header())
