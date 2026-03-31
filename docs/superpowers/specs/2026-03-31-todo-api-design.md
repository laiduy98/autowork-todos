# Todo API Design

A DRF-only backend for a Todo application with full auth, soft delete, filtering, and search.

## Architecture

Single `todos` Django app inside the existing `autowork` project. DRF ViewSets with Routers. Token-based auth via `rest_framework.authtoken`. SQLite database.

## Data Models

### Category

| Field | Type | Notes |
|-------|------|-------|
| id | auto | PK |
| name | CharField(max_length=100) | unique per user |
| user | FK(auth.User) | each user has their own categories |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

- Unique constraint on `(user, name)`

### Todo

| Field | Type | Notes |
|-------|------|-------|
| id | auto | PK |
| title | CharField(max_length=255) | required |
| description | TextField | optional, blank=True |
| status | CharField(choices) | `todo`, `in_progress`, `done` — default `todo` |
| priority | CharField(choices) | `low`, `medium`, `high` — default `medium` |
| due_date | DateTimeField | optional, null=True |
| category | FK(Category) | optional, null=True, on_delete=SET_NULL |
| user | FK(auth.User) | each user sees only their own todos |
| is_deleted | BooleanField | default False — soft delete flag |
| deleted_at | DateTimeField | optional, null=True — when soft-deleted |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

- Default queryset excludes `is_deleted=True`
- `status` choices: `todo`, `in_progress`, `done`
- `priority` choices: `low`, `medium`, `high`

## Authentication

Using DRF Token Auth (`rest_framework.authtoken`).

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create account + return token |
| POST | `/api/auth/login/` | Username + password → return token |
| POST | `/api/auth/logout/` | Delete token (requires auth) |

- Register: custom view (creates user + token)
- Login: DRF's built-in `obtain_auth_token`
- Logout: custom view (deletes token)
- All other endpoints require `Authorization: Token <token>` header

## API Endpoints

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories/` | List user's categories |
| POST | `/api/categories/` | Create category |
| GET | `/api/categories/{id}/` | Get category detail |
| PUT/PATCH | `/api/categories/{id}/` | Update category |
| DELETE | `/api/categories/{id}/` | Hard delete category |

### Todos

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/todos/` | List user's active todos |
| POST | `/api/todos/` | Create todo |
| GET | `/api/todos/{id}/` | Get todo detail |
| PUT/PATCH | `/api/todos/{id}/` | Update todo |
| DELETE | `/api/todos/{id}/` | Soft delete (sets is_deleted=True, deleted_at=now) |
| GET | `/api/todos/trash/` | List soft-deleted todos |
| POST | `/api/todos/{id}/restore/` | Restore soft-deleted todo |
| DELETE | `/api/todos/{id}/permanent-delete/` | Permanently remove from DB |

- `trash`, `restore`, `permanent-delete` are custom actions on the TodoViewSet
- `restore` sets `is_deleted=False`, `deleted_at=None`

## Filtering & Search

Applied to `GET /api/todos/` using three DRF filter backends.

### Filters (DjangoFilterBackend)

- `status` — exact match
- `priority` — exact match
- `category` — exact match by category ID
- `due_date_before` — due_date <= value
- `due_date_after` — due_date >= value
- `is_overdue` — computed: due_date < now AND status != done

### Search (SearchFilter)

- `?search=keyword` — searches `title` and `description` fields (icontains)

### Ordering (OrderingFilter)

- `?ordering=field` or `?ordering=-field` for descending
- Allowed fields: `due_date`, `priority`, `status`, `created_at`

## Permissions & Validation

### Permissions

- Custom `IsOwner` permission: `obj.user == request.user`
- Applied as default DRF permission class
- Auth endpoints (register, login) use `AllowAny`

### Serializer Validation

- `title`: required, max 255 chars
- `name` (category): required, max 100 chars, unique per user
- `due_date`: must be in the future when creating
- `category`: must belong to the authenticated user
- `status`/`priority`: must be valid choice values

### Error Response Format

DRF default:
```json
{
  "field_name": ["Error message."]
}
```

## Project Structure

```
autowork/
  manage.py
  autowork/
    __init__.py
    settings.py
    urls.py                # include api urls
    wsgi.py
  todos/
    __init__.py
    models.py              # Category, Todo
    serializers.py         # CategorySerializer, TodoSerializer
    views.py               # CategoryViewSet, TodoViewSet, RegisterView
    permissions.py         # IsOwner
    filters.py             # TodoFilter (django-filter)
    urls.py                # router + auth urls
    admin.py               # register models
    tests/
      __init__.py
      test_models.py
      test_views.py
```

## Dependencies

- `djangorestframework` — DRF core
- `django-filter` — filtering support

## Settings Changes

Add to INSTALLED_APPS:
- `rest_framework`
- `rest_framework.authtoken`
- `django_filters`
- `todos`

DRF default settings:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'todos.permissions.IsOwner',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```
