from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class PublicPageTests(SimpleTestCase):
    def test_home_renders_shared_frontend_template_and_stylesheet(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "UniSport Buddy")
        self.assertContains(response, "/static/css/site.css")

    def test_liveness_does_not_require_a_database(self):
        self.assertEqual(self.client.get(reverse("health-live")).json(), {"status": "ok"})

    def test_health_routes_do_not_accept_writes(self):
        for name in ("health-live", "health-ready"):
            with self.subTest(name=name):
                self.assertEqual(self.client.post(reverse(name)).status_code, 405)


class ReadinessTests(TestCase):
    def test_readiness_checks_postgres(self):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})

    def test_database_failure_returns_503_without_leaking_details(self):
        with patch("core.views.connection.cursor", side_effect=OperationalError("private detail")):
            response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "private detail", status_code=503)
