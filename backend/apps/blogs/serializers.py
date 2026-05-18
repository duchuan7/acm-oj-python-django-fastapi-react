from rest_framework import serializers

from .models import BlogPost


class BlogPostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = BlogPost
        fields = ["id", "author", "author_username", "title", "content", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "author_username", "created_at", "updated_at"]

    def create(self, validated_data):
        return BlogPost.objects.create(author=self.context["request"].user, **validated_data)
