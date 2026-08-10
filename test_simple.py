import unittest
import requests
import json
BASE_URL = "http://localhost:8001"
class TestSendItAPI(unittest.TestCase):
    def test_01_register(self):
        response = requests.post(
            f"{BASE_URL}/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "test123",
                "full_name": "Test User",
                "role": "staff"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "testuser")
        print("✅ Registration passed")
    def test_02_login(self):
        # First register
        requests.post(f"{BASE_URL}/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "test123",
            "full_name": "Login User",
            "role": "staff"
        })
        # Then login
        response = requests.post(
            f"{BASE_URL}/login",
            data={"username": "logintest", "password": "test123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        print("✅ Login passed")
    def test_03_health(self):
        response = requests.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        print("✅ Health check passed")
if __name__ == "__main__":
    unittest.main(verbosity=2)
