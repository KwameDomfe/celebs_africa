from django.utils import timezone


class LastSeenMiddleware:
    """Updates UserProfile.last_seen on every authenticated request."""

    THROTTLE_SECONDS = 60  # only write to DB at most once per minute per user

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            profile = getattr(request.user, 'profile', None)
            if profile is not None:
                last = profile.last_seen
                if last is None or (now - last).total_seconds() > self.THROTTLE_SECONDS:
                    # Use update() to avoid triggering signals / extra queries
                    from apps.accounts.models import UserProfile
                    UserProfile.objects.filter(pk=profile.pk).update(last_seen=now)
                    profile.last_seen = now  # keep in-memory copy fresh
        return self.get_response(request)
