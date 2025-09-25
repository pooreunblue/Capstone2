from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.models import User
from users.serializers import UserSignUpSerializer

class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSignUpSerializer

class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message':f'Hello {request.user.username}'})
