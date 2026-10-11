"""Security regression tests. Run: python -m pytest test_security.py (or unittest)."""
import os
import unittest

os.environ.pop("APP_ENV", None)
os.environ["STAFF_API_KEY"] = "test-key-123"

from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

client = TestClient(app)
KEY = {"X-API-Key": "test-key-123"}
P = "/api/v1"


class TestSecurity(unittest.TestCase):
    def test_staff_endpoints_require_key(self):
        for path in ["/doctor/opd-queue", "/doctor/triage-alerts", "/doctor/patient-summary/x",
                     "/database/status", "/database/tables", "/abdm/fhir-bundle/x",
                     "/abdm/dpdp-audit/x", "/documents/session-documents/x"]:
            self.assertEqual(client.get(P + path).status_code, 401, path)
            self.assertEqual(client.get(P + path, headers={"X-API-Key": "wrong"}).status_code, 401, path)
        self.assertEqual(client.get(P + "/doctor/opd-queue", headers=KEY).status_code, 200)

    def test_v1_alias_also_protected(self):
        self.assertEqual(client.get("/v1/doctor/opd-queue").status_code, 401)

    def test_kiosk_still_public_and_validated(self):
        self.assertEqual(client.get(P + "/kiosk/complaints").status_code, 200)
        bad = {"name": "A", "age": 500, "gender": "M", "phone": "9876543210"}
        self.assertEqual(client.post(P + "/kiosk/start-session", json=bad).status_code, 422)
        bad = {"name": "A", "age": 30, "gender": "M", "phone": "<script>"}
        self.assertEqual(client.post(P + "/kiosk/start-session", json=bad).status_code, 422)
        ok = {"name": "<img src=x onerror=alert(1)>", "age": 30, "gender": "M", "phone": "9876543210"}
        r = client.post(P + "/kiosk/start-session", json=ok)
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()["session_id"]), 30)  # unguessable id

    def test_cors_not_wildcard(self):
        r = client.get("/api/health", headers={"Origin": "https://evil.example"})
        self.assertNotIn("access-control-allow-origin", {k.lower() for k in r.headers})

    def test_security_headers_and_no_store(self):
        r = client.get("/api/health")
        self.assertEqual(r.headers["x-content-type-options"], "nosniff")
        self.assertEqual(r.headers["x-frame-options"], "DENY")
        self.assertEqual(r.headers["cache-control"], "no-store")

    def test_websocket_requires_key(self):
        from starlette.websockets import WebSocketDisconnect
        with self.assertRaises(WebSocketDisconnect):
            with client.websocket_connect("/ws/live-feed"):
                pass
        with client.websocket_connect("/ws/live-feed?key=test-key-123") as ws:
            ws.send_text("hello")

    def test_oversized_input_rejected(self):
        r = client.post(P + "/kiosk/parse-voice", json={"transcript": "a" * 6000})
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
