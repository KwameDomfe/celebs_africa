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


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    if not created:
        profile.save()
