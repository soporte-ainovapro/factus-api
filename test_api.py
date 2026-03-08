import httpx
import json
import asyncio

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_create_invoice():
    try:
        async with httpx.AsyncClient() as client:
            # 1. Login
            print("Logging in...")
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            # OAuth2PasswordRequestForm expects form-urlencoded
            response = await client.post(f"{BASE_URL}/auth/login", data=login_data)
            if response.status_code != 200:
                print(f"Login failed: {response.status_code} - {response.text}")
                return
            token = response.json().get("access_token")
            if not token:
                print("Login failed: No access_token in response")
                return
            print(f"Login successful. Token obtained.")

            # 2. Create Invoice
            print("Creating invoice...")
            invoice_data = {
                "document": "01",
                "numbering_range_id": 8,
                "reference_code": "FAC-1772977296571",
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
            
            headers = {
                "Authorization": f"Bearer {token}",
                "x-factus-token": "mock-token"
            }
            
            # Send as JSON object (httpx will set Content-Type: application/json)
            response = await client.post(f"{BASE_URL}/invoices/", json=invoice_data, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            # Now try to reproduce the error by sending it as a string
            print("\nAttempting to reproduce error by sending as a JSON string...")
            # We explicitly set Content-Type to application/json but send a string as the body
            json_string = json.dumps(invoice_data)
            response = await client.post(f"{BASE_URL}/invoices/", content=json_string, headers={"Authorization": f"Bearer {token}", "x-factus-token": "mock-token", "Content-Type": "application/json"})
            print(f"Status Code (string body): {response.status_code}")
            print(f"Response (string body): {json.dumps(response.json(), indent=2)}")

    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_invoice())
