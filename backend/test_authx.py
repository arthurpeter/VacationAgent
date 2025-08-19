"""Test script to verify AuthX implementation."""
import asyncio
import httpx
import json

async def test_auth_endpoints():
    """Test the authentication endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.json()}")
        
        # Test registration
        print("\n2. Testing user registration...")
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await client.post(f"{base_url}/auth/register", json=user_data)
        print(f"Registration: {response.status_code}")
        if response.status_code == 201:
            user_info = response.json()
            print(f"User created: {user_info['username']} - {user_info['email']}")
        else:
            print(f"Registration failed: {response.text}")
        
        # Test login
        print("\n3. Testing user login...")
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = await client.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print(f"Login successful! Token type: {tokens['token_type']}")
            
            # Test protected endpoint
            print("\n4. Testing protected endpoint...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(f"{base_url}/protected", headers=headers)
            print(f"Protected endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"Protected data: {response.json()}")
            else:
                print(f"Protected endpoint failed: {response.text}")
                
            # Test getting current user info
            print("\n5. Testing /auth/me endpoint...")
            response = await client.get(f"{base_url}/auth/me", headers=headers)
            print(f"User info: {response.status_code}")
            if response.status_code == 200:
                print(f"User data: {response.json()}")
            else:
                print(f"User info failed: {response.text}")
        else:
            print(f"Login failed: {response.text}")

if __name__ == "__main__":
    print("AuthX Authentication Test")
    print("=" * 50)
    asyncio.run(test_auth_endpoints())
