from django.urls import path

from . import views


urlpatterns = [
    path('', views.posts_home, name='posts_home'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('<int:pk>/restore/', views.post_restore, name='post_restore'),
    path('<int:pk>/like/', views.post_like, name='post_like'),
    path('<int:pk>/comment/', views.post_comment, name='post_comment'),
    path('comment/<int:pk>/edit/', views.post_comment_edit, name='post_comment_edit'),
    path('comment/<int:pk>/delete/', views.post_comment_delete, name='post_comment_delete'),
    path('comment/<int:pk>/restore/', views.post_comment_restore, name='post_comment_restore'),
    path('<int:pk>/share/<str:platform>/', views.post_share, name='post_share'),
]
