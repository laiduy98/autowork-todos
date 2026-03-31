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
