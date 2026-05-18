from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import BlogPost
from .serializers import BlogPostSerializer


class BlogPostViewSet(viewsets.ModelViewSet):
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = BlogPost.objects.select_related("author")
        author_id = self.request.query_params.get("author")
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.filter(status=BlogPost.Status.PUBLISHED)
        if user.is_staff or user.role in {"ADMIN", "COACH"}:
            return queryset
        return (queryset.filter(status=BlogPost.Status.PUBLISHED) | queryset.filter(author=user)).distinct()

    def perform_update(self, serializer):
        user = self.request.user
        if not (user.is_staff or user.role in {"ADMIN", "COACH"} or serializer.instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only edit your own posts.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or user.role in {"ADMIN", "COACH"} or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()
