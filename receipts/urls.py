from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path('register/', views.register, name='register'),
    path('api/receipts/', views.create_receipt, name='create_receipt'),
    path('rules/', views.rules, name='rules'),
    path('profile/', views.profile, name='profile'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='receipts/login.html'),
        name='login',
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout',
    ),
]
