from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.models import User, DormInfo, Profile
from users.serializers import UserSignUpSerializer, DormInfoSerializer, ProfileSerializer

class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]

class DormInfoView(generics.CreateAPIView):
    queryset = DormInfo.objects.all()
    serializer_class = DormInfoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
