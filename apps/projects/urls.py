"""URL patterns for the projects app."""

from django.urls import path

from apps.projects import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='list'),
    path('create/', views.project_create_view, name='create'),
    path('<int:pk>/', views.project_detail_view, name='detail'),
    path('<int:pk>/edit/', views.project_edit_view, name='edit'),
    path('<int:pk>/delete/', views.project_delete_view, name='delete'),
    path('<int:pk>/members/add/', views.project_member_add_view, name='member_add'),
    path('<int:pk>/members/<int:mem_pk>/remove/', views.project_member_remove_view, name='member_remove'),
]
