from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

urlpatterns = [
    path('', views.account_home, name='account_home'),
    path('register/', views.register, name='register'),
    path('track-event/', views.track_event, name='track_event'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password/', views.password_change, name='password_change'),
]
