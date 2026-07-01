from django.utils import timezone
from django.conf import settings
from django.contrib.auth.views import redirect_to_login

# Known social-media / SEO crawler user-agent substrings.
# These bots must be able to read pages unauthenticated to generate previews.
_CRAWLER_AGENTS = (
    'facebookexternalhit', 'Facebot',
    'Twitterbot', 'LinkedInBot',
    'WhatsApp', 'Slackbot',
    'TelegramBot', 'Discordbot',
    'Googlebot', 'bingbot', 'DuckDuckBot',
)

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


class LoginRequiredMiddleware:
    """
    Redirects unauthenticated users to the login page for every URL except
    the explicitly whitelisted public paths.
    """
    # Exact paths that are always public
    PUBLIC_EXACT = {
        '/',
        '/robots.txt',
        '/robots.txt/',
        '/sitemap.xml',
        '/sitemap.xml/',
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/track-event/',
        '/accounts/logout/',
    }

    def __init__(self, get_response):
        self.get_response = get_response
        # Prefix-based public paths (built once at startup)
        self._public_prefixes = (
            '/admin/',
            settings.STATIC_URL or '/static/',
            settings.MEDIA_URL or '/media/',
        )

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            if (
                path not in self.PUBLIC_EXACT
                and not any(path.startswith(p) for p in self._public_prefixes)
            ):
                ua = request.META.get('HTTP_USER_AGENT', '')
                if not any(bot.lower() in ua.lower() for bot in _CRAWLER_AGENTS):
                    return redirect_to_login(request.get_full_path())
        return self.get_response(request)

class CanonicalDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]

        if host == "www.celebsafrica.com":
            return self.redirect_to_canonical(request)

        return self.get_response(request)

    def redirect_to_canonical(self, request):
        url = f"https://celebsafrica.com{request.get_full_path()}"
        from django.http import HttpResponsePermanentRedirect
        return HttpResponsePermanentRedirect(url)