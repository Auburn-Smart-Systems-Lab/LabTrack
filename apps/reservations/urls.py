"""URL patterns for the reservations app."""

from django.urls import path

from apps.reservations import views

app_name = 'reservations'

urlpatterns = [
    path('', views.reservation_list_view, name='list'),
    path('calendar/', views.reservation_calendar_view, name='calendar'),
    path('create/', views.reservation_create_view, name='create'),
    path('<int:pk>/', views.reservation_detail_view, name='detail'),
    path('<int:pk>/cancel/', views.reservation_cancel_view, name='cancel'),
    path('waitlist/', views.waitlist_list_view, name='waitlist_list'),
    path('waitlist/create/', views.waitlist_create_view, name='waitlist_create'),
    path('waitlist/<int:pk>/leave/', views.waitlist_leave_view, name='waitlist_leave'),
]
