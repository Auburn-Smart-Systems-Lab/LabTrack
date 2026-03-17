"""URL patterns for the activity app."""

from django.urls import path

from apps.activity import views

app_name = 'activity'

urlpatterns = [
    path('', views.activity_feed_view, name='feed'),
    path('mine/', views.my_activity_view, name='mine'),
]
