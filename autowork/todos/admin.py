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
