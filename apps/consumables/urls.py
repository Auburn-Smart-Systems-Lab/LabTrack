"""URL patterns for the consumables app."""

from django.urls import path

from apps.consumables import views

app_name = 'consumables'

urlpatterns = [
    path('', views.consumable_list_view, name='list'),
    path('create/', views.consumable_create_view, name='create'),
    path('<int:pk>/', views.consumable_detail_view, name='detail'),
    path('<int:pk>/edit/', views.consumable_edit_view, name='edit'),
    path('<int:pk>/delete/', views.consumable_delete_view, name='delete'),
    path('<int:pk>/log-usage/', views.log_usage_view, name='log_usage'),
    path('<int:pk>/restock/', views.restock_view, name='restock'),
    path('low-stock/', views.low_stock_list_view, name='low_stock'),
]
