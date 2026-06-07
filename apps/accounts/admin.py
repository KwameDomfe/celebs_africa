from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import UserProfile, FunnelEvent


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ('role', 'bio', 'avatar')
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    def get_inlines(self, request, obj):
        # On the add page obj is None; the post_save signal creates the profile.
        # Only show the inline when editing an existing user.
        return [UserProfileInline] if obj else []


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(FunnelEvent)
class FunnelEventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'source_path', 'session_key', 'user', 'created_at')
    list_filter = ('event_name', 'created_at')
    search_fields = ('source_path', 'session_key', 'user__username')
    readonly_fields = ('event_name', 'source_path', 'metadata', 'session_key', 'user', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    change_list_template = 'admin/accounts/funnelevent/change_list.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data['cl'].queryset
        except (AttributeError, KeyError, TypeError):
            return response

        def _summary_for(qs):
            hero_clicks = qs.filter(event_name=FunnelEvent.EVENT_HERO_REGISTER_CLICK).count()
            unlock_clicks = qs.filter(event_name=FunnelEvent.EVENT_UNLOCK_REGISTER_CLICK).count()
            gate_clicks = qs.filter(event_name=FunnelEvent.EVENT_DIRECTORY_GATE_REGISTER_CLICK).count()
            register_page_views = qs.filter(event_name=FunnelEvent.EVENT_REGISTER_PAGE_VIEW).count()
            signup_success = qs.filter(event_name=FunnelEvent.EVENT_SIGNUP_SUCCESS).count()
            register_intent = hero_clicks + unlock_clicks + gate_clicks
            return {
                'hero_clicks': hero_clicks,
                'unlock_clicks': unlock_clicks,
                'gate_clicks': gate_clicks,
                'register_intent': register_intent,
                'register_page_views': register_page_views,
                'signup_success': signup_success,
                'intent_to_view_rate': (register_page_views / register_intent * 100.0) if register_intent else 0.0,
                'view_to_signup_rate': (signup_success / register_page_views * 100.0) if register_page_views else 0.0,
                'intent_to_signup_rate': (signup_success / register_intent * 100.0) if register_intent else 0.0,
            }

        now = timezone.now()
        windows = {
            '24h': queryset.filter(created_at__gte=now - timedelta(hours=24)),
            '7d': queryset.filter(created_at__gte=now - timedelta(days=7)),
            '30d': queryset.filter(created_at__gte=now - timedelta(days=30)),
        }
        response.context_data['funnel_summaries'] = {
            label: _summary_for(qs) for label, qs in windows.items()
        }
        return response
