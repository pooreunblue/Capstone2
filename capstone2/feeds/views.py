from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message':f'Hello {request.user.username}'})
