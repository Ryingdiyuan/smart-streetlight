import json
import os
import sys
import time
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


class SmokeTest:
    def __init__(self) -> None:
        self.failed = 0
        self.device_id: int | None = None
        self.device_code = f"TEST-SL-{int(time.time())}"

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        expected_status: int | tuple[int, ...] = 200,
    ) -> tuple[int, Any]:
        url = f"{BASE_URL}{path}"
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=body, headers=headers, method=method)
        expected = (
            expected_status
            if isinstance(expected_status, tuple)
            else (expected_status,)
        )

        try:
            with urlopen(request, timeout=10) as response:
                status_code = response.status
                response_body = response.read().decode("utf-8")
        except HTTPError as error:
            status_code = error.code
            response_body = error.read().decode("utf-8", errors="replace")
        except URLError as error:
            raise RuntimeError(f"request failed: {error}") from error

        parsed_body: Any = None
        if response_body:
            try:
                parsed_body = json.loads(response_body)
            except json.JSONDecodeError:
                parsed_body = response_body

        if status_code not in expected:
            raise AssertionError(
                f"{method} {path} expected {expected}, got {status_code}, body={parsed_body}"
            )
        return status_code, parsed_body

    def run_step(self, name: str, func) -> None:
        try:
            func()
        except Exception as error:
            self.failed += 1
            print(f"FAIL {name}: {error}")
        else:
            print(f"PASS {name}")

    def test_health(self) -> None:
        _, body = self.request("GET", "/api/health")
        assert body.get("status") == "ok"

    def test_create_device(self) -> None:
        payload = {
            "device_code": self.device_code,
            "device_name": "冒烟测试路灯",
            "location": "测试区域",
            "status": "offline",
        }
        _, body = self.request("POST", "/api/devices", payload=payload, expected_status=201)
        self.device_id = int(body["id"])
        assert body["device_code"] == self.device_code

    def require_device_id(self) -> int:
        if self.device_id is None:
            raise RuntimeError("device_id is not available")
        return self.device_id

    def test_list_devices(self) -> None:
        _, body = self.request("GET", "/api/devices")
        assert isinstance(body, list)
        assert any(item.get("device_code") == self.device_code for item in body)

    def test_get_device(self) -> None:
        device_id = self.require_device_id()
        _, body = self.request("GET", f"/api/devices/{device_id}")
        assert body["id"] == device_id

    def test_create_light_data(self) -> None:
        device_id = self.require_device_id()
        payload = {
            "light_intensity": 120,
            "lamp_status": "off",
            "voltage": 220.5,
            "reported_at": datetime.utcnow().isoformat(),
        }
        _, body = self.request(
            "POST",
            f"/api/devices/{device_id}/light-data",
            payload=payload,
            expected_status=201,
        )
        assert body["device_id"] == device_id
        assert "suggested_action" in body

    def test_latest_light(self) -> None:
        device_id = self.require_device_id()
        _, body = self.request("GET", f"/api/devices/{device_id}/latest-light")
        assert body["device_id"] == device_id

    def test_light_history(self) -> None:
        device_id = self.require_device_id()
        query = urlencode({"limit": 20})
        _, body = self.request("GET", f"/api/devices/{device_id}/light-history?{query}")
        assert isinstance(body, list)
        assert len(body) >= 1

    def test_get_threshold(self) -> None:
        device_id = self.require_device_id()
        _, body = self.request("GET", f"/api/devices/{device_id}/threshold")
        assert body["device_id"] == device_id

    def test_update_threshold(self) -> None:
        device_id = self.require_device_id()
        payload = {
            "low_threshold": 100,
            "high_threshold": 300,
            "enabled": True,
        }
        _, body = self.request("PUT", f"/api/devices/{device_id}/threshold", payload=payload)
        assert body["low_threshold"] == 100
        assert body["high_threshold"] == 300

    def test_create_command(self) -> None:
        device_id = self.require_device_id()
        payload = {"command": "TURN_ON"}
        _, body = self.request(
            "POST",
            f"/api/devices/{device_id}/commands",
            payload=payload,
            expected_status=201,
        )
        assert body["device_id"] == device_id
        assert body["command"] == "TURN_ON"

    def test_list_commands(self) -> None:
        device_id = self.require_device_id()
        _, body = self.request("GET", f"/api/devices/{device_id}/commands?limit=20")
        assert isinstance(body, list)
        assert len(body) >= 1

    def test_list_alarms(self) -> None:
        _, body = self.request("GET", "/api/alarms?limit=20")
        assert isinstance(body, list)

    def run(self) -> int:
        print(f"Smoke test target: {BASE_URL}")
        steps = [
            ("GET /api/health", self.test_health),
            ("POST /api/devices", self.test_create_device),
            ("GET /api/devices", self.test_list_devices),
            ("GET /api/devices/{id}", self.test_get_device),
            ("POST /api/devices/{id}/light-data", self.test_create_light_data),
            ("GET /api/devices/{id}/latest-light", self.test_latest_light),
            ("GET /api/devices/{id}/light-history", self.test_light_history),
            ("GET /api/devices/{id}/threshold", self.test_get_threshold),
            ("PUT /api/devices/{id}/threshold", self.test_update_threshold),
            ("POST /api/devices/{id}/commands", self.test_create_command),
            ("GET /api/devices/{id}/commands", self.test_list_commands),
            ("GET /api/alarms", self.test_list_alarms),
        ]

        for name, func in steps:
            self.run_step(name, func)

        if self.failed:
            print(f"Smoke test finished with {self.failed} failure(s)")
            return 1

        print("Smoke test finished successfully")
        return 0


if __name__ == "__main__":
    sys.exit(SmokeTest().run())
