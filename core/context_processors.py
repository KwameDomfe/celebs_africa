from django.utils import timezone
from datetime import timedelta


def online_users(request):
    from apps.accounts.models import UserProfile
    threshold = timezone.now() - timedelta(minutes=5)
    count = UserProfile.objects.filter(last_seen__gte=threshold).count()
    return {'online_users_count': count}
