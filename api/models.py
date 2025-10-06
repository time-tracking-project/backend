from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'user']
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"

class TimeEntry(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('paused', 'Paused'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='time_entries', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)  # Duration in seconds
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='stopped')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        project_name = self.project.name if self.project else "No Project"
        return f"{project_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Calculate duration if both start and end times are set
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
        super().save(*args, **kwargs)
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def is_running(self):
        """Check if this time entry is currently running"""
        return self.status == 'running' and self.end_time is None
