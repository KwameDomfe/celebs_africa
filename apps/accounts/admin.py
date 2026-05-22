from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ('bio', 'avatar')
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    def get_inlines(self, request, obj):
        # On the add page obj is None; the post_save signal creates the profile.
        # Only show the inline when editing an existing user.
        return [UserProfileInline] if obj else []


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
