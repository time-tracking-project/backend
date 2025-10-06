from django.urls import path
from . import views, auth_views

urlpatterns = [
    # Test endpoint
    path('test/', views.test_api, name='api-test'),
    
    # Authentication endpoints
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login, name='login'),
    path('auth/verify-email/', auth_views.verify_email, name='verify-email'),
    path('auth/refresh/', auth_views.refresh_token, name='refresh-token'),
    
    # Project endpoints
    path('projects/', views.projects, name='projects'),
    path('projects/<int:pk>/', views.project_detail, name='project-detail'),
    
    # Time tracking endpoints
    path('time-entries/', views.time_entries, name='time-entries'),
    path('timer/start/', views.start_timer, name='start-timer'),
    path('timer/stop/', views.stop_timer, name='stop-timer'),
    path('timer/status/', views.timer_status, name='timer-status'),
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
]