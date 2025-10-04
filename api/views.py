from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

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