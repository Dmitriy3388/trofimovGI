from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account:'

urlpatterns = [
    #path('login/', views.user_login, name='login'),
    #адреса входа и выхода
    path('login/', auth_views.LoginView.as_view(), name='account:login'),
    path('logout/', auth_views.LogoutView.as_view(), name='account:logout'),
    # change password urls
    path('', include('django.contrib.auth.urls')),
    #path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
]
