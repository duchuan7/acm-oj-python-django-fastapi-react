from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "created_at", "updated_at", "delete_link")
    list_filter = ("status",)
    search_fields = ("title", "content", "author__username")
    actions = ["delete_selected"]

    @admin.display(description="Delete")
    def delete_link(self, obj):
        url = reverse("admin:blogs_blogpost_delete", args=[obj.pk])
        return format_html('<a class="deletelink" href="{}">Delete</a>', url)
