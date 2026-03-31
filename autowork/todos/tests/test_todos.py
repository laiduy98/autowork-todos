from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from todos.models import Category, Todo


class TodoAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="testpass123")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.category = Category.objects.create(name="Work", user=self.user)

    def _create_todo(self, **kwargs):
        defaults = {"title": "Test todo", "user": self.user}
        defaults.update(kwargs)
        return Todo.objects.create(**defaults)

    # --- List ---
    def test_list_todos(self):
        self._create_todo(title="Todo 1")
        self._create_todo(title="Todo 2")
        response = self.client.get("/api/todos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_excludes_soft_deleted(self):
        self._create_todo(title="Active")
        self._create_todo(title="Deleted", is_deleted=True, deleted_at=timezone.now())
        response = self.client.get("/api/todos/")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Active")

    def test_list_only_own_todos(self):
        user2 = User.objects.create_user(username="user2", password="testpass123")
        self._create_todo(title="My todo")
        Todo.objects.create(title="Their todo", user=user2)
        response = self.client.get("/api/todos/")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "My todo")

    # --- Create ---
    def test_create_todo(self):
        response = self.client.post(
            "/api/todos/",
            {"title": "Buy milk", "priority": "high", "category": self.category.pk},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Buy milk")
        self.assertEqual(response.data["priority"], "high")

    def test_create_todo_default_values(self):
        response = self.client.post("/api/todos/", {"title": "Simple todo"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "todo")
        self.assertEqual(response.data["priority"], "medium")

    def test_create_todo_with_other_users_category(self):
        user2 = User.objects.create_user(username="user2", password="testpass123")
        cat2 = Category.objects.create(name="Secret", user=user2)
        response = self.client.post(
            "/api/todos/", {"title": "Todo", "category": cat2.pk}
        )
        self.assertEqual(response.status_code, 400)

    # --- Retrieve ---
    def test_retrieve_todo(self):
        todo = self._create_todo(title="Buy milk")
        response = self.client.get(f"/api/todos/{todo.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Buy milk")

    def test_retrieve_other_users_todo(self):
        user2 = User.objects.create_user(username="user2", password="testpass123")
        todo = Todo.objects.create(title="Secret", user=user2)
        response = self.client.get(f"/api/todos/{todo.pk}/")
        self.assertEqual(response.status_code, 404)

    # --- Update ---
    def test_update_todo(self):
        todo = self._create_todo(title="Old title")
        response = self.client.patch(
            f"/api/todos/{todo.pk}/", {"title": "New title", "status": "done"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "New title")
        self.assertEqual(response.data["status"], "done")

    # --- Soft Delete ---
    def test_soft_delete_todo(self):
        todo = self._create_todo()
        response = self.client.delete(f"/api/todos/{todo.pk}/")
        self.assertEqual(response.status_code, 204)
        todo.refresh_from_db()
        self.assertTrue(todo.is_deleted)
        self.assertIsNotNone(todo.deleted_at)

    # --- Trash ---
    def test_trash_lists_deleted_todos(self):
        self._create_todo(title="Active")
        self._create_todo(title="Deleted", is_deleted=True, deleted_at=timezone.now())
        response = self.client.get("/api/todos/trash/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Deleted")

    # --- Restore ---
    def test_restore_todo(self):
        todo = self._create_todo(is_deleted=True, deleted_at=timezone.now())
        response = self.client.post(f"/api/todos/{todo.pk}/restore/")
        self.assertEqual(response.status_code, 200)
        todo.refresh_from_db()
        self.assertFalse(todo.is_deleted)
        self.assertIsNone(todo.deleted_at)

    # --- Permanent Delete ---
    def test_permanent_delete(self):
        todo = self._create_todo(is_deleted=True, deleted_at=timezone.now())
        response = self.client.delete(f"/api/todos/{todo.pk}/permanent-delete/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Todo.objects.filter(pk=todo.pk).exists())


class TodoFilterTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="testpass123")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def _create_todo(self, **kwargs):
        defaults = {"title": "Test todo", "user": self.user}
        defaults.update(kwargs)
        return Todo.objects.create(**defaults)

    def test_filter_by_status(self):
        self._create_todo(title="Active", status="todo")
        self._create_todo(title="Done", status="done")
        response = self.client.get("/api/todos/", {"status": "done"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Done")

    def test_filter_by_priority(self):
        self._create_todo(title="Low", priority="low")
        self._create_todo(title="High", priority="high")
        response = self.client.get("/api/todos/", {"priority": "high"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "High")

    def test_search_by_title(self):
        self._create_todo(title="Buy milk")
        self._create_todo(title="Walk dog")
        response = self.client.get("/api/todos/", {"search": "milk"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Buy milk")

    def test_ordering(self):
        self._create_todo(title="Low", priority="low")
        self._create_todo(title="High", priority="high")
        response = self.client.get("/api/todos/", {"ordering": "-priority"})
        self.assertEqual(response.data["results"][0]["title"], "Low")
