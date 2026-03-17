"""URL patterns for the borrowing app."""

from django.urls import path

from apps.borrowing import views

app_name = 'borrowing'

urlpatterns = [
    path('', views.borrow_list_view, name='list'),
    path('request/', views.borrow_request_create_view, name='create'),
    path('<int:pk>/', views.borrow_detail_view, name='detail'),
    path('<int:pk>/approve/', views.borrow_approve_view, name='approve'),
    path('<int:pk>/reject/', views.borrow_reject_view, name='reject'),
    path('<int:pk>/return/', views.borrow_return_view, name='return'),
    path('overdue/', views.overdue_list_view, name='overdue'),
    path('queue/', views.approval_queue_view, name='queue'),
]
