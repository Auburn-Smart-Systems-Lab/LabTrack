"""URL patterns for the kits app."""

from django.urls import path

from apps.kits import views

app_name = 'kits'

urlpatterns = [
    path('', views.kit_list_view, name='list'),
    path('create/', views.kit_create_view, name='create'),
    path('<int:pk>/', views.kit_detail_view, name='detail'),
    path('<int:pk>/edit/', views.kit_edit_view, name='edit'),
    path('<int:pk>/delete/', views.kit_delete_view, name='delete'),
    path('<int:pk>/items/add/', views.kit_item_add_view, name='item_add'),
    path('<int:pk>/items/<int:item_pk>/remove/', views.kit_item_remove_view, name='item_remove'),
]
