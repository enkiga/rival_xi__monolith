from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app


class CORSTests(TestCase):
    def test_frontend_preflight_is_allowed(self):
        client = TestClient(app)

        response = client.options(
            "/api/v1/auth/otp/request",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )
        self.assertEqual(
            response.headers["access-control-allow-credentials"],
            "true",
        )
