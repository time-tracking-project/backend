from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api, name='api-test'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/verify-email/', views.verify_email, name='verify-email'),
]