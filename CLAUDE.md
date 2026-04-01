# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django REST Framework todo management API. Users manage todos and categories via token-authenticated endpoints. All data is user-scoped.

## Common Commands

All commands run from the `autowork/` directory (where `manage.py` lives):

```bash
# Run all tests
cd autowork && python manage.py test -v 2

# Run a single test module
python manage.py test todos.tests.test_todos -v 2

# Run a specific test class or method
python manage.py test todos.tests.test_todos.TestTodoEndpoints.test_create_todo -v 2

# Database migrations
python manage.py makemigrations todos
python manage.py migrate

# Start dev server
python manage.py runserver

# Django system check
python manage.py check
```

Dependencies are managed with `uv` (see `pyproject.toml`). Python 3.12+.

## Architecture

### URL Routing

`autowork/autowork/urls.py` includes `todos/urls.py` under `/api/`. The app URL config uses a DRF `DefaultRouter` for categories and todos, plus explicit paths for auth endpoints (`register`, `login`, `logout`).

### Models (`todos/models.py`)

- **Category**: name + user FK. Unique together constraint on `(user, name)`.
- **Todo**: title, description, status (todo/in_progress/done), priority (low/medium/high), due_date, category FK (SET_NULL), user FK. Soft delete via `is_deleted` + `deleted_at`. Both models ordered by `-created_at`.

### Views (`todos/views.py`)

- **RegisterView/LogoutView**: Standalone APIViews for auth. Registration is `AllowAny`, logout deletes the token.
- **CategoryViewSet**: Mixin-based (no `ModelViewSet`) — list/create/retrieve/update/destroy. Scopes to `request.user`.
- **TodoViewSet**: Full `ModelViewSet` with custom `list`/`retrieve` to exclude soft-deleted items. `destroy` performs soft delete. Extra actions: `trash`, `restore`, `permanent_delete`.

### Permissions (`todos/permissions.py`)

`IsOwner` checks `obj.user == request.user` on object-level actions.

### Filtering (`todos/filters.py`)

`TodoFilter` (django-filter) on status, priority, category, `due_date_before`, `due_date_after`, and computed `is_overdue`. Global filter/search/ordering backends configured in DRF settings.

### Serializers (`todos/serializers.py`)

- **CategorySerializer**: Validates name uniqueness per user (excludes self on update).
- **TodoSerializer**: Computed `is_overdue` field, validates due_date is future (create only), validates category ownership.
- **RegisterSerializer**: Creates user with hashed password.

## Key Patterns

- All ViewSets filter by `request.user` in `get_queryset()` — no cross-user data access.
- DRF default settings enforce `IsAuthenticated` + `TokenAuthentication` globally (overridden only on `RegisterView`).
- Soft-deleted todos are excluded from default list/retrieve but accessible via the `trash` action.
- Tests live in `todos/tests/` split by domain: `test_auth.py`, `test_categories.py`, `test_todos.py`, `test_models.py`.
