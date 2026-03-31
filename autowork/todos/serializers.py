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
