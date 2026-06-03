
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from .views import home, top_celebs, sitemap_xml

urlpatterns = [
    path("", home, name="home"),
    path('top-celebs/', top_celebs, name='top_celebs'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('celebs/', include('apps.celebs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
