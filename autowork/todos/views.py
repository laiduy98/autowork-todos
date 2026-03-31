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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
