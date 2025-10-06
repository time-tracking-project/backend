from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, EmailVerificationSerializer, LoginSerializer

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