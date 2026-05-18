from django.contrib import admin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "content", "author__username")
