"""测试登录"""
import urllib.request
import json

url = "http://127.0.0.1:8000/api/auth/login"
data = {"username": "admin", "password": "admin123"}
json_data = json.dumps(data).encode("utf-8")

req = urllib.request.Request(
    url,
    data=json_data,
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req, timeout=10) as f:
        resp = json.loads(f.read().decode("utf-8"))
        print("[+] 登录成功！")
        print(f"    用户: {resp['user']['username']}")
        print(f"    角色: {resp['user']['role']}")
        print(f"    Token: {resp['access_token'][:30]}...")
except Exception as e:
    print(f"[-] 登录失败: {e}")
    import traceback
    traceback.print_exc()
