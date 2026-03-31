from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from todos.models import Category


class CategoryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="testpass123")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    # --- List ---
    def test_list_categories(self):
        Category.objects.create(name="Work", user=self.user)
        Category.objects.create(name="Personal", user=self.user)
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_categories_unauthenticated(self):
        self.client.credentials()
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 401)

    def test_list_only_own_categories(self):
        user2 = User.objects.create_user(username="user2", password="testpass123")
        Category.objects.create(name="Work", user=self.user)
        Category.objects.create(name="Secret", user=user2)
        response = self.client.get("/api/categories/")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Work")

    # --- Create ---
    def test_create_category(self):
        response = self.client.post("/api/categories/", {"name": "Work"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Work")
        self.assertTrue(Category.objects.filter(name="Work", user=self.user).exists())

    def test_create_duplicate_category(self):
        Category.objects.create(name="Work", user=self.user)
        response = self.client.post("/api/categories/", {"name": "Work"})
        self.assertEqual(response.status_code, 400)

    # --- Retrieve ---
    def test_retrieve_category(self):
        category = Category.objects.create(name="Work", user=self.user)
        response = self.client.get(f"/api/categories/{category.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Work")

    def test_retrieve_other_users_category(self):
        user2 = User.objects.create_user(username="user2", password="testpass123")
        category = Category.objects.create(name="Secret", user=user2)
        response = self.client.get(f"/api/categories/{category.pk}/")
        self.assertEqual(response.status_code, 404)

    # --- Update ---
    def test_update_category(self):
        category = Category.objects.create(name="Work", user=self.user)
        response = self.client.patch(f"/api/categories/{category.pk}/", {"name": "Job"})
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, "Job")

    # --- Delete ---
    def test_delete_category(self):
        category = Category.objects.create(name="Work", user=self.user)
        response = self.client.delete(f"/api/categories/{category.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
