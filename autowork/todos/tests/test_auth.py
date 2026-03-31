from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class RegisterViewTest(APITestCase):
    def test_register_success(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "newuser", "email": "new@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_username(self):
        User.objects.create_user(username="existing", password="testpass123")
        response = self.client.post(
            "/api/auth/register/",
            {"username": "existing", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 400)

    def test_register_missing_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "newuser"},
        )
        self.assertEqual(response.status_code, 400)


class LoginViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_login_success(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "nobody", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 400)


class LogoutViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_logout_success(self):
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_unauthenticated(self):
        self.client.credentials()
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 401)
