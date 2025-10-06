from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Q
from .serializers import (
    UserRegistrationSerializer, EmailVerificationSerializer, LoginSerializer,
    ProjectSerializer, TimeEntrySerializer, StartTimerSerializer, 
    StopTimerSerializer, TimeEntrySummarySerializer
)
from .models import Project, TimeEntry

@api_view(['GET'])
def test_api(request):
    """
    A simple API view to test if the backend is working.
    """
    data = {
        'message': 'Hello from the timetracker API!',
        'status': 'success',
        'timestamp': '2024-06-15T12:00:00Z'
    }
    return Response(data)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and send verification email.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'User created successfully. Please check your email to verify your account.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user's email address using the token.
    """
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.verify_email()
        return Response({
            'message': 'Email verified successfully!',
            'user_id': user.id
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_email_verified': user.is_email_verified
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Time Tracking Views

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def projects(request):
    """
    List all projects for the authenticated user or create a new project.
    """
    if request.method == 'GET':
        projects = Project.objects.filter(user=request.user, is_active=True)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_detail(request, pk):
    """
    Retrieve, update or delete a project.
    """
    project = get_object_or_404(Project, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = ProjectSerializer(project)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProjectSerializer(project, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        project.is_active = False
        project.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def time_entries(request):
    """
    List all time entries for the authenticated user.
    """
    entries = TimeEntry.objects.filter(user=request.user).order_by('-start_time')[:50]
    serializer = TimeEntrySerializer(entries, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_timer(request):
    """
    Start a new timer for a project (or without a project).
    """
    serializer = StartTimerSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        project_id = serializer.validated_data.get('project_id')
        project = None
        
        if project_id:
            project = Project.objects.get(id=project_id)
        
        time_entry = TimeEntry.objects.create(
            project=project,
            user=request.user,
            description=serializer.validated_data.get('description', ''),
            start_time=timezone.now(),
            status='running'
        )
        
        response_serializer = TimeEntrySerializer(time_entry)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_timer(request):
    """
    Stop a running timer.
    """
    serializer = StopTimerSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        time_entry = TimeEntry.objects.get(id=serializer.validated_data['time_entry_id'])
        time_entry.end_time = timezone.now()
        time_entry.status = 'stopped'
        time_entry.save()
        
        response_serializer = TimeEntrySerializer(time_entry)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timer_status(request):
    """
    Get the current running timer status for the user.
    """
    running_timer = TimeEntry.objects.filter(
        user=request.user, 
        status='running',
        end_time__isnull=True
    ).first()
    
    if running_timer:
        serializer = TimeEntrySerializer(running_timer)
        return Response({'running': True, 'timer': serializer.data})
    
    return Response({'running': False, 'timer': None})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """
    Get time tracking summary for dashboard.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    # Get running timer
    running_timer = TimeEntry.objects.filter(
        user=request.user, 
        status='running',
        end_time__isnull=True
    ).first()
    
    # Get recent entries
    recent_entries = TimeEntry.objects.filter(
        user=request.user
    ).order_by('-start_time')[:10]
    
    # Calculate totals
    today_total = TimeEntry.objects.filter(
        user=request.user,
        start_time__gte=today_start,
        status='stopped'
    ).aggregate(total=Sum('duration_seconds'))['total'] or 0
    
    week_total = TimeEntry.objects.filter(
        user=request.user,
        start_time__gte=week_start,
        status='stopped'
    ).aggregate(total=Sum('duration_seconds'))['total'] or 0
    
    month_total = TimeEntry.objects.filter(
        user=request.user,
        start_time__gte=month_start,
        status='stopped'
    ).aggregate(total=Sum('duration_seconds'))['total'] or 0
    
    def format_duration(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    summary_data = {
        'total_time_today': format_duration(today_total),
        'total_time_this_week': format_duration(week_total),
        'total_time_this_month': format_duration(month_total),
        'running_timer': TimeEntrySerializer(running_timer).data if running_timer else None,
        'recent_entries': TimeEntrySerializer(recent_entries, many=True).data
    }
    
    serializer = TimeEntrySummarySerializer(summary_data)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token(request):
    """
    Refresh JWT token.
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        new_access_token = str(token.access_token)
        
        return Response({
            'access': new_access_token,
            'refresh': str(token)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)