from django.contrib import admin

from .models import Post, PostComment, PostLike, PostShare


class PostCommentInline(admin.TabularInline):
    model = PostComment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_deleted', 'deleted_at', 'created_at', 'updated_at')
    search_fields = ('text', 'user__username', 'user__email')
    list_filter = ('is_deleted', 'created_at')
    inlines = [PostCommentInline]


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    search_fields = ('post__text', 'user__username')


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'is_deleted', 'deleted_at', 'created_at')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('text', 'user__username', 'post__text')


@admin.register(PostShare)
class PostShareAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'platform', 'created_at')
    list_filter = ('platform', 'created_at')
    search_fields = ('post__text', 'user__username')
