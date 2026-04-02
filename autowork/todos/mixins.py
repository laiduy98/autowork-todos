from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

class SoftDeleteMixins:
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