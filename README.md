# Autowork Todos

A Django REST Framework API for managing todos and categories, with token-based authentication and soft deletes.

## Setup

```bash
uv sync
cd autowork
python manage.py migrate
python manage.py runserver
```

## API Endpoints

All endpoints are under `/api/`.

| Endpoint | Methods | Description |
|---|---|---|
| `auth/register/` | POST | Create account, returns token |
| `auth/login/` | POST | Get token (username + password) |
| `auth/logout/` | POST | Delete token |
| `categories/` | GET, POST | List / create categories |
| `categories/{id}/` | GET, PUT, PATCH, DELETE | Category CRUD |
| `todos/` | GET, POST | List active todos / create todo |
| `todos/{id}/` | GET, PUT, PATCH, DELETE | Todo CRUD (DELETE soft-deletes) |
| `todos/trash/` | GET | List soft-deleted todos |
| `todos/{id}/restore/` | POST | Restore a soft-deleted todo |
| `todos/{id}/permanent-delete/` | DELETE | Permanently delete a todo |

All endpoints except `register` and `login` require a `Token` auth header.

## Todo Filtering

Todos support query parameters: `status`, `priority`, `category`, `due_date_before`, `due_date_after`, `is_overdue`, `search` (title/description), `ordering` (due_date, priority, status, created_at).

## Running Tests

```bash
cd autowork && python manage.py test -v 2
```
