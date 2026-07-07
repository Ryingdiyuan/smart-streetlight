"""通过API来初始化admin账号"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=== 调用 /auth/init-admin 接口 ===")
payload = {"username": "admin", "password": "admin123"}
try:
    response = requests.post(f"{BASE_URL}/api/auth/init-admin", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except Exception as e:
    print(f"请求出错: {e}")

print("\n=== 尝试登录 ===")
try:
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {json.dumps(login_response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"登录请求出错: {e}")
