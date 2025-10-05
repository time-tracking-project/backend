from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
