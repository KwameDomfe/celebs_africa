from django.urls import path
from . import views

urlpatterns = [
    path('', views.celebs_home, name='celebs_home'),
    path('create/', views.celeb_create, name='celeb_create'),
    path('<int:pk>/delete/', views.celeb_delete, name='celeb_delete'),
    path('<int:pk>/photos/upload/', views.celeb_photo_upload, name='celeb_photo_upload'),
    path('photos/<int:pk>/delete/', views.celeb_photo_delete, name='celeb_photo_delete'),
    path('<int:pk>/like/', views.celeb_like, name='celeb_like'),
    path('<int:pk>/follow/', views.celeb_follow, name='celeb_follow'),
    path('<int:pk>/review/', views.celeb_review, name='celeb_review'),
    path('<int:pk>/review/delete/', views.celeb_review_delete, name='celeb_review_delete'),
    path('<int:pk>/comment/', views.celeb_comment, name='celeb_comment'),
    path('comment/<int:pk>/edit/', views.comment_edit, name='comment_edit'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('<int:pk>/', views.celeb_detail_by_pk, name='celeb_detail_pk'),
    path('<slug:cat_slug>/<slug:family_slug>/<slug:type_slug>/<slug:slug>/', views.celeb_detail, name='celeb_detail'),
    path('<slug:slug>/edit/', views.celeb_update, name='celeb_update'),
    path('my-celebs/', views.my_celebs, name='my_celebs'),
]
