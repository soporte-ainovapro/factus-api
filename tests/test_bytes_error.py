import httpx
import asyncio

BASE_URL = "http://127.0.0.1:8000/api"

async def test_bytes_error():
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_data = {"username": "admin", "password": "admin123"}
        response = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code != 200:
            print("Login failed")
            return
        token = response.json()["access_token"]
        
        # 2. Send invalid JSON parsing
        invalid_json_payload = b'{"document":"01","numbering_range_id":8,"reference_code":"FAC-1772977760297"}'
        
        headers = {
            "Authorization": f"Bearer {token}",
            "x-factus-token": "mock-token",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{BASE_URL}/invoices/",
            content=invalid_json_payload,  # Sending as raw bytes with no structure satisfying the BaseModel
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_bytes_error())
