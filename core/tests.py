import datetime

import pytz
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class MetropolisBaseTests(TestCase):
    def setUp(self):
        self.client = Client()

    def adduser(self):
        User = get_user_model()
        self.assertEqual(User.objects.count(), 0)  # Assuming no users initially

        User.objects.create_superuser(
            username="testuser",
            email="testing@maclyonsden.com",
            password="verysecure",
        )

        # Check if the user has been created
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(
            User.objects.get(username="testuser").email,
            "testing@maclyonsden.com",
        )
        # test login
        self.assertTrue(self.client.login(username="testuser", password="verysecure"))

    def test_sanity(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Metropolis"
        )  # Changed assertRegex to assertContains

    def test_check_ok(self):
        urls = [
            "/api/version",
            "/api/v3/staff",
            "/api/v3/feeds",
            "/api/v3/banners",
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)  # Updated assertion

    def authenticate(self):
        self.adduser()
        response = self.client.post(
            content_type="application/json",
            path="/api/auth/token",
            data={
                "username": "testuser",
                "password": "verysecure",
            },
        )
        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        headers = {"Authorization": f'Bearer {tokens["access"]}'}
        return headers

    def test_token_auth(self):
        headers = self.authenticate()
        response = self.client.get("/api/me", **headers)
        self.assertEqual(response.status_code, 200)

    def test_expo_notif_token(self):
        """fixme ken :)
        headers = self.authenticate()
        fake_tokens = ["fakeExpoToken1", "ExponentPushToken[fakeExpoToken2]"]
        for fake_token in fake_tokens:
            response1 = self.client.put(
                "/api/v3/notif/token", data={"expo_push_token": fake_token}, **headers
            )
            #self.assertEqual(response1.status_code, 200)  # Added assertion

            response2 = self.client.delete(
                "/api/v3/notif/token", data={"expo_push_token": fake_token}, **headers
            )
            self.assertEqual(response2.status_code, 200)  # Added assertion

        nonexistent_token = "nonexistentToken"
        response = self.client.delete(
            "/api/v3/notif/token",
            data={"expo_push_token": nonexistent_token},
            **headers,
        )
        self.assertEqual(response.status_code, 200)  # Added assertion
        """

    def test_all_list(self):
        headers = self.authenticate()
        cases = [
            {"type": "announcement"},
            {"type": "blog-post"},
            {"type": "exhibit"},
            {"type": "event"},
            {"type": "organization"},
            {"type": "user"},
            {"type": "tag"},
            {"type": "term"},
            {"type": "timetable"},
            {"type": "course"},
        ]
        for case in cases:
            response = self.client.get(f'/api/v3/obj/{case["type"]}', **headers)
            self.assertEqual(response.status_code, 200)  # Added assertion


class ChoicesTests(TestCase):
    def setUp(self):
        self.datetime = datetime.datetime(
            2024, 8, 1, 0, 0, 0, 0, pytz.utc
        )  # August 1, 2024
        self.expected = [
            (None, "Does not apply"),
            (2025, 2025),
            (2026, 2026),
            (2027, 2027),
            (2028, 2028),
        ]

    def test_calculate_graduating_year_choices(self):
        from core.models.choices import calculate_graduating_year_choices

        self.assertEqual(calculate_graduating_year_choices(), self.expected)
