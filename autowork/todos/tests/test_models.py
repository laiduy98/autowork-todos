from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from todos.models import Category, Todo


class CategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_category(self):
        category = Category.objects.create(name="Work", user=self.user)
        self.assertEqual(category.name, "Work")
        self.assertEqual(category.user, self.user)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

    def test_category_name_unique_per_user(self):
        Category.objects.create(name="Work", user=self.user)
        with self.assertRaises(Exception):
            Category.objects.create(name="Work", user=self.user)

    def test_same_name_different_user(self):
        user2 = User.objects.create_user(username="user2", password="testpass123")
        Category.objects.create(name="Work", user=self.user)
        category2 = Category.objects.create(name="Work", user=user2)
        self.assertEqual(category2.name, "Work")

    def test_category_str(self):
        category = Category.objects.create(name="Work", user=self.user)
        self.assertEqual(str(category), "Work")


class TodoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_todo_defaults(self):
        todo = Todo.objects.create(title="Buy milk", user=self.user)
        self.assertEqual(todo.title, "Buy milk")
        self.assertEqual(todo.status, "todo")
        self.assertEqual(todo.priority, "medium")
        self.assertFalse(todo.is_deleted)
        self.assertIsNone(todo.deleted_at)
        self.assertIsNone(todo.category)
        self.assertIsNone(todo.due_date)
        self.assertIsNotNone(todo.created_at)

    def test_todo_with_all_fields(self):
        category = Category.objects.create(name="Shopping", user=self.user)
        due = timezone.now() + timezone.timedelta(days=1)
        todo = Todo.objects.create(
            title="Buy milk",
            description="2 liters of whole milk",
            status="in_progress",
            priority="high",
            due_date=due,
            category=category,
            user=self.user,
        )
        self.assertEqual(todo.description, "2 liters of whole milk")
        self.assertEqual(todo.status, "in_progress")
        self.assertEqual(todo.priority, "high")
        self.assertEqual(todo.category, category)

    def test_todo_soft_delete(self):
        todo = Todo.objects.create(title="Buy milk", user=self.user)
        todo.is_deleted = True
        todo.deleted_at = timezone.now()
        todo.save()
        todo.refresh_from_db()
        self.assertTrue(todo.is_deleted)
        self.assertIsNotNone(todo.deleted_at)

    def test_todo_str(self):
        todo = Todo.objects.create(title="Buy milk", user=self.user)
        self.assertEqual(str(todo), "Buy milk")

    def test_category_cascade_set_null(self):
        category = Category.objects.create(name="Shopping", user=self.user)
        todo = Todo.objects.create(
            title="Buy milk", category=category, user=self.user
        )
        category.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.category)
