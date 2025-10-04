from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
import os

def debug_env(request):
    return JsonResponse({
        'allowed_hosts_raw': os.environ.get('ALLOWED_HOSTS', 'NOT_SET'),
        'allowed_hosts_after_split': os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(','),
        'debug': os.environ.get('DEBUG', 'NOT_SET'),
        'secret_key_exists': bool(os.environ.get('SECRET_KEY')),
        'host_header': request.get_host(),
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('debug-env/', debug_env),
]
