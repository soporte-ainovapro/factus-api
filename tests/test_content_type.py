import httpx
import asyncio

BASE_URL = "http://127.0.0.1:8000/api"

async def test():
    async with httpx.AsyncClient() as client:
        # Login
        login_data = {"username": "admin", "password": "admin123"}
        response = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        token = response.json().get("access_token")
        
        payload = b'{"document": "01", "customer": {"identification_document_id": 3, "identification": "123"}, "items": [{"code_reference": "ref", "name": "item"}]}'
        
        print("Testing Content-Type: text/plain")
        headers1 = {
            "Authorization": f"Bearer {token}",
            "x-factus-token": "mock-token",
            "Content-Type": "text/plain"
        }
        r1 = await client.post(f"{BASE_URL}/invoices/", content=payload, headers=headers1)
        print(f"text/plain -> {r1.status_code}")
        print(r1.text)

        print("\nTesting missing Content-Type")
        headers2 = {
            "Authorization": f"Bearer {token}",
            "x-factus-token": "mock-token"
        }
        r2 = await client.post(f"{BASE_URL}/invoices/", content=payload, headers=headers2)
        print(f"missing -> {r2.status_code}")
        print(r2.text)

if __name__ == "__main__":
    asyncio.run(test())
