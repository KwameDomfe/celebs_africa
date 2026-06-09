from django.conf import settings
from django.db import models
from django.urls import reverse


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    text = models.TextField(max_length=1200)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post {self.pk} by {self.user}"

    def get_absolute_url(self):
        return reverse('posts_home') + f"#post-{self.pk}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user} likes post {self.post_id}"


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_comments')
    text = models.TextField(max_length=600)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment {self.pk} on post {self.post_id}"


class PostShare(models.Model):
    PLATFORM_FACEBOOK = 'facebook'
    PLATFORM_TWITTER = 'twitter'
    PLATFORM_WHATSAPP = 'whatsapp'
    PLATFORM_TELEGRAM = 'telegram'

    PLATFORM_CHOICES = [
        (PLATFORM_FACEBOOK, 'Facebook'),
        (PLATFORM_TWITTER, 'Twitter / X'),
        (PLATFORM_WHATSAPP, 'WhatsApp'),
        (PLATFORM_TELEGRAM, 'Telegram'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_shares')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} shared post {self.post_id} to {self.platform}"
