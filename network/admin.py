from django.contrib import admin
from django.db.models import Count

# Register your models here.
from .models import User, Post, Follow, Like

class PostAdmin(admin.ModelAdmin):
    """Customize posts display in admin"""
    list_display = ("id", "creator", "content_short", "likes", "created_at")

    @admin.display
    def content_short(self, Post):
        if len(Post.content) > 35:
            return f"{Post.content[:35]}..."
        else:
            return Post.content

    @admin.display
    def likes(self, Post):
        likes_count = Post.post_likes.aggregate(Count("id"))
        return likes_count['id__count']

admin.site.register(User)
admin.site.register(Post, PostAdmin)
admin.site.register(Follow)
admin.site.register(Like)