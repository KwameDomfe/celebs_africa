from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_FAN = 'fan'
    ROLE_CELEB = 'celeb'
    ROLE_MANAGER = 'manager'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = [
        (ROLE_FAN, 'Fan'),
        (ROLE_CELEB, 'Celeb'),
        (ROLE_MANAGER, 'Celeb Manager'),
        (ROLE_STAFF, 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=300, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_FAN)

    def __str__(self):
        return f"{self.user.username}'s profile"


class FunnelEvent(models.Model):
    EVENT_HERO_REGISTER_CLICK = 'hero_register_click'
    EVENT_UNLOCK_REGISTER_CLICK = 'unlock_register_click'
    EVENT_DIRECTORY_GATE_REGISTER_CLICK = 'directory_gate_register_click'
    EVENT_REGISTER_PAGE_VIEW = 'register_page_view'
    EVENT_SIGNUP_SUCCESS = 'signup_success'

    EVENT_CHOICES = [
        (EVENT_HERO_REGISTER_CLICK, 'Hero Register Click'),
        (EVENT_UNLOCK_REGISTER_CLICK, 'Unlock Register Click'),
        (EVENT_DIRECTORY_GATE_REGISTER_CLICK, 'Directory Gate Register Click'),
        (EVENT_REGISTER_PAGE_VIEW, 'Register Page View'),
        (EVENT_SIGNUP_SUCCESS, 'Signup Success'),
    ]

    event_name = models.CharField(max_length=80, choices=EVENT_CHOICES, db_index=True)
    source_path = models.CharField(max_length=300, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='funnel_events')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_name} @ {self.created_at:%Y-%m-%d %H:%M}"


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    if not created:
        profile.save()
