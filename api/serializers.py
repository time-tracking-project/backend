from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Project, TimeEntry
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
import os

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:                                         
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Send verification email (disabled for production)
        # self.send_verification_email(user)
        
        return user
    
    def send_verification_email(self, user):
        subject = 'Verify Your Email Address'
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email/{user.email_verification_token}/"
        
        html_message = f"""
        <h2>Welcome to Time Tracker!</h2>
        <p>Please click the link below to verify your email address:</p>
        <a href="{verification_url}">Verify Email</a>
        <p>If you didn't create an account, please ignore this email.</p>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        try:
            user = User.objects.get(email_verification_token=value)
            if user.is_email_verified:
                raise serializers.ValidationError("Email already verified")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token")
    
    def verify_email(self):
        user = User.objects.get(email_verification_token=self.validated_data['token'])
        user.is_email_verified = True
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            # Email verification disabled for production
            # if not user.is_email_verified:
            #     raise serializers.ValidationError('Please verify your email before logging in')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'color', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TimeEntrySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    project_color = serializers.CharField(source='project.color', read_only=True, allow_null=True)
    duration_formatted = serializers.CharField(read_only=True)
    is_running = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = [
            'id', 'project', 'project_name', 'project_color', 'description', 
            'start_time', 'end_time', 'duration_seconds', 'duration_formatted',
            'status', 'is_running', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'duration_seconds', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class StartTimerSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_project_id(self, value):
        if value is None:
            return value
        try:
            project = Project.objects.get(id=value, user=self.context['request'].user)
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project not found")
    
    def validate(self, attrs):
        user = self.context['request'].user
        
        # Check if user already has a running timer
        running_entry = TimeEntry.objects.filter(
            user=user, 
            status='running',
            end_time__isnull=True
        ).first()
        
        if running_entry:
            raise serializers.ValidationError("You already have a running timer. Please stop it first.")
        
        return attrs

class StopTimerSerializer(serializers.Serializer):
    time_entry_id = serializers.IntegerField()
    
    def validate_time_entry_id(self, value):
        try:
            time_entry = TimeEntry.objects.get(
                id=value, 
                user=self.context['request'].user,
                status='running'
            )
            return value
        except TimeEntry.DoesNotExist:
            raise serializers.ValidationError("Running time entry not found")

class TimeEntrySummarySerializer(serializers.Serializer):
    """Serializer for time tracking summary data"""
    total_time_today = serializers.CharField()
    total_time_this_week = serializers.CharField()
    total_time_this_month = serializers.CharField()
    running_timer = TimeEntrySerializer(required=False)
    recent_entries = TimeEntrySerializer(many=True)
