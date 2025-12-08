from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account'

urlpatterns = [
    #адреса входа и выхода
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/',
         auth_views.LogoutView.as_view(
             template_name='account/logged_out.html',
             next_page='account:login'
         ),
         name='logout'),
    # change password urls
    path('', include('django.contrib.auth.urls')),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
]
