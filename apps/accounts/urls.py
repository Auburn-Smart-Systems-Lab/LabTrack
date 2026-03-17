from django.urls import path
from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/', views.user_detail_view, name='user_detail'),
    path('users/<int:pk>/', views.user_detail_view, name='profile_view'),
    path('users/<int:pk>/role/', views.assign_role_view, name='assign_role'),
]