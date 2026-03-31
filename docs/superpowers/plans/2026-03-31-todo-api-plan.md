# Todo API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a DRF-only Todo API with token auth, soft delete, filtering, and search.

**Architecture:** Single `todos` Django app inside the `autowork` project. DRF ViewSets with Routers for CRUD. Token auth via `rest_framework.authtoken`. SQLite database.

**Tech Stack:** Django 6.0, Django REST Framework, django-filter, SQLite

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Modify | Add djangorestframework + django-filter deps |
| `autowork/autowork/settings.py` | Modify | Add apps, DRF config |
| `autowork/autowork/urls.py` | Modify | Include todos urls |
| `autowork/todos/__init__.py` | Create | App init |
| `autowork/todos/apps.py` | Create | App config |
| `autowork/todos/models.py` | Create | Category + Todo models |
| `autowork/todos/admin.py` | Create | Register models in admin |
| `autowork/todos/permissions.py` | Create | IsOwner permission class |
| `autowork/todos/serializers.py` | Create | CategorySerializer + TodoSerializer |
| `autowork/todos/filters.py` | Create | TodoFilter with is_overdue |
| `autowork/todos/views.py` | Create | RegisterView, CategoryViewSet, TodoViewSet |
| `autowork/todos/urls.py` | Create | Router + auth URL patterns |
| `autowork/todos/tests/__init__.py` | Create | Tests package init |
| `autowork/todos/tests/test_models.py` | Create | Model tests |
| `autowork/todos/tests/test_auth.py` | Create | Auth endpoint tests |
| `autowork/todos/tests/test_categories.py` | Create | Category endpoint tests |
| `autowork/todos/tests/test_todos.py` | Create | Todo endpoint tests |

---

### Task 1: Project Setup — Dependencies, App, Settings

**Files:**
- Modify: `pyproject.toml`
- Create: `autowork/todos/__init__.py`, `autowork/todos/apps.py`
- Modify: `autowork/autowork/settings.py`

- [ ] **Step 1: Install dependencies**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice
uv add djangorestframework django-filter
```

Expected: Both packages installed, `pyproject.toml` updated.

- [ ] **Step 2: Create the todos Django app**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py startapp todos
```

Expected: `todos/` directory created with `__init__.py`, `apps.py`, `models.py`, `views.py`, `admin.py`, `tests.py`, `migrations/`.

- [ ] **Step 3: Delete the auto-generated `todos/tests.py` and create a tests package**

Run:
```bash
rm /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork/todos/tests.py
mkdir -p /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork/todos/tests
touch /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork/todos/tests/__init__.py
```

- [ ] **Step 4: Update settings.py — add apps and DRF config**

Replace the `INSTALLED_APPS` and add `REST_FRAMEWORK` at the end of `autowork/autowork/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'todos',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

Note: We use `IsAuthenticated` as the default permission here instead of `IsOwner` because `IsOwner` needs object-level access. We'll apply `IsOwner` at the ViewSet level per-view. The global default ensures unauthenticated requests are always rejected.

- [ ] **Step 5: Run migrate to verify setup**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py migrate
```

Expected: All migrations apply without errors, including `authtoken` migrations creating the `authtoken_token` table.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock autowork/todos/ autowork/autowork/settings.py
git commit -m "chore: add DRF, django-filter, and create todos app"
```

---

### Task 2: Models — Category and Todo

**Files:**
- Modify: `autowork/todos/models.py`
- Create: `autowork/todos/tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

Create `autowork/todos/tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py test todos.tests.test_models -v 2
```

Expected: FAIL — `ModuleNotFoundError: No module named 'todos.models'`

- [ ] **Step 3: Write the models**

Replace `autowork/todos/models.py` with:

```python
from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "name")
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Todo(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TODO
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    due_date = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="todos"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="todos"
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
```

- [ ] **Step 4: Create and run migrations**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py makemigrations todos
python manage.py migrate
```

Expected: `0001_initial.py` migration created with Category and Todo tables. No errors.

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py test todos.tests.test_models -v 2
```

Expected: All 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add autowork/todos/models.py autowork/todos/tests/ autowork/todos/migrations/
git commit -m "feat: add Category and Todo models with tests"
```

---

### Task 3: Admin Registration

**Files:**
- Modify: `autowork/todos/admin.py`

- [ ] **Step 1: Register models in admin**

Replace `autowork/todos/admin.py` with:

```python
from django.contrib import admin

from todos.models import Category, Todo


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name",)
    list_filter = ("user",)


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "user", "due_date", "is_deleted", "created_at")
    list_filter = ("status", "priority", "is_deleted", "user")
    search_fields = ("title", "description")
```

- [ ] **Step 2: Verify admin loads without errors**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/admin.py
git commit -m "feat: register Category and Todo models in admin"
```

---

### Task 4: Permissions — IsOwner

**Files:**
- Create: `autowork/todos/permissions.py`

- [ ] **Step 1: Write IsOwner permission class**

Create `autowork/todos/permissions.py`:

```python
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
```

- [ ] **Step 2: Verify no import errors**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python -c "from todos.permissions import IsOwner; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/permissions.py
git commit -m "feat: add IsOwner permission class"
```

---

### Task 5: Serializers

**Files:**
- Create: `autowork/todos/serializers.py`

- [ ] **Step 1: Write serializers**

Create `autowork/todos/serializers.py`:

```python
from django.contrib.auth.models import User
from rest_framework import serializers

from todos.models import Category, Todo


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        user = self.context["request"].user
        qs = Category.objects.filter(user=user, name=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("You already have a category with this name.")
        return value


class TodoSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Todo
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "category",
            "is_deleted",
            "deleted_at",
            "is_overdue",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "is_deleted", "deleted_at", "is_overdue", "created_at", "updated_at")

    def get_is_overdue(self, obj):
        from django.utils import timezone

        if obj.due_date and obj.status != Todo.Status.DONE:
            return obj.due_date < timezone.now()
        return False

    def validate_due_date(self, value):
        from django.utils import timezone

        if value and value < timezone.now() and not self.instance:
            raise serializers.ValidationError("Due date must be in the future.")
        return value

    def validate_category(self, value):
        if value:
            user = self.context["request"].user
            if value.user != user:
                raise serializers.ValidationError("This category does not belong to you.")
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
```

- [ ] **Step 2: Verify no import errors**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python -c "from todos.serializers import CategorySerializer, TodoSerializer, RegisterSerializer; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/serializers.py
git commit -m "feat: add Category, Todo, and Register serializers"
```

---

### Task 6: Filters — TodoFilter

**Files:**
- Create: `autowork/todos/filters.py`

- [ ] **Step 1: Write TodoFilter**

Create `autowork/todos/filters.py`:

```python
from django.utils import timezone
from django_filters import rest_framework as filters

from todos.models import Todo


class TodoFilter(filters.FilterSet):
    due_date_before = filters.DateTimeFilter(field_name="due_date", lookup_expr="lte")
    due_date_after = filters.DateTimeFilter(field_name="due_date", lookup_expr="gte")
    is_overdue = filters.BooleanFilter(method="filter_is_overdue")

    class Meta:
        model = Todo
        fields = ("status", "priority", "category")

    def filter_is_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(
                due_date__lt=timezone.now(),
                status__ne=Todo.Status.DONE,
            )
        return queryset
```

- [ ] **Step 2: Verify no import errors**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python -c "from todos.filters import TodoFilter; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/filters.py
git commit -m "feat: add TodoFilter with overdue, date range, and field filters"
```

---

### Task 7: Views — Auth, Categories, Todos

**Files:**
- Modify: `autowork/todos/views.py`

- [ ] **Step 1: Write all views**

Replace `autowork/todos/views.py` with:

```python
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from todos.filters import TodoFilter
from todos.models import Category, Todo
from todos.permissions import IsOwner
from todos.serializers import CategorySerializer, RegisterSerializer, TodoSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response(
            {"user": {"username": user.username, "email": user.email}, "token": token.key},
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filterset_class = TodoFilter
    search_fields = ("title", "description")
    ordering_fields = ("due_date", "priority", "status", "created_at")

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(is_deleted=False)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=["get"])
    def trash(self, request):
        deleted_todos = self.get_queryset().filter(is_deleted=True)
        serializer = self.get_serializer(deleted_todos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        todo = self.get_object()
        if not todo.is_deleted:
            return Response(
                {"detail": "Todo is not deleted."}, status=status.HTTP_400_BAD_REQUEST
            )
        todo.is_deleted = False
        todo.deleted_at = None
        todo.save()
        serializer = self.get_serializer(todo)
        return Response(serializer.data)

    @action(detail=True, methods=["delete"], url_path="permanent-delete")
    def permanent_delete(self, request, pk=None):
        todo = self.get_object()
        todo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 2: Verify no import errors**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python -c "from todos.views import RegisterView, LogoutView, CategoryViewSet, TodoViewSet; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/views.py
git commit -m "feat: add auth views, CategoryViewSet, and TodoViewSet with soft delete"
```

---

### Task 8: URL Routing

**Files:**
- Create: `autowork/todos/urls.py`
- Modify: `autowork/autowork/urls.py`

- [ ] **Step 1: Create todos URL configuration**

Create `autowork/todos/urls.py`:

```python
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from todos.views import CategoryViewSet, LogoutView, RegisterView, TodoViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"todos", TodoViewSet, basename="todo")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", obtain_auth_token, name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
] + router.urls
```

- [ ] **Step 2: Wire up todos URLs in project urls.py**

Replace `autowork/autowork/urls.py` with:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("todos.urls")),
]
```

- [ ] **Step 3: Verify URL resolution**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py show_urls | grep api
```

Expected: All `/api/...` URLs listed. If `show_urls` not available, use:

```bash
python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='autowork.settings'
import django; django.setup()
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'url_patterns'):
        for sub in pattern.url_patterns:
            print(f'{pattern.pattern}{sub.pattern}')
"
```

- [ ] **Step 4: Commit**

```bash
git add autowork/todos/urls.py autowork/autowork/urls.py
git commit -m "feat: add URL routing for auth, categories, and todos"
```

---

### Task 9: Auth Tests

**Files:**
- Create: `autowork/todos/tests/test_auth.py`

- [ ] **Step 1: Write auth tests**

Create `autowork/todos/tests/test_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py test todos.tests.test_auth -v 2
```

Expected: All 7 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/tests/test_auth.py
git commit -m "test: add auth endpoint tests"
```

---

### Task 10: Category Endpoint Tests

**Files:**
- Create: `autowork/todos/tests/test_categories.py`

- [ ] **Step 1: Write category tests**

Create `autowork/todos/tests/test_categories.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py test todos.tests.test_categories -v 2
```

Expected: All 8 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/tests/test_categories.py
git commit -m "test: add category endpoint tests"
```

---

### Task 11: Todo Endpoint Tests

**Files:**
- Create: `autowork/todos/tests/test_todos.py`

- [ ] **Step 1: Write todo tests**

Create `autowork/todos/tests/test_todos.py`:

```python
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
        self.assertEqual(response.data["results"][0]["title"], "High")
```

- [ ] **Step 2: Run tests to verify they pass**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py test todos.tests.test_todos -v 2
```

Expected: All 17 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add autowork/todos/tests/test_todos.py
git commit -m "test: add todo endpoint and filter tests"
```

---

### Task 12: Final Verification

- [ ] **Step 1: Run all tests**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py test -v 2
```

Expected: All tests across all test files PASS (8 model + 7 auth + 8 category + 17 todo = 40 tests).

- [ ] **Step 2: Run Django system check**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Start dev server and verify endpoints**

Run:
```bash
cd /Users/laiduy98/Documents/Projects/Personal/django-practice/autowork
python manage.py runserver
```

Then in another terminal, test:
```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Create category (use token from register/login)
curl -X POST http://127.0.0.1:8000/api/categories/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Work"}'

# Create todo
curl -X POST http://127.0.0.1:8000/api/todos/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk","priority":"high"}'

# List todos
curl http://127.0.0.1:8000/api/todos/ \
  -H "Authorization: Token <your-token>"
```

Expected: All requests return expected status codes and data.
