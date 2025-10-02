from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField("전화번호", max_length=11, unique=True, null=True, blank=True)
    email = models.EmailField("이메일", unique=True, blank=True)
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

"""
기숙사 지원 인증 정보 저장 모델
"""
class DormInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField("이름", max_length=10)
    gender = models.CharField("성별", max_length=10)
    application_order = models.CharField("신청 차수", max_length=10)
    building = models.CharField("지원 건물", max_length=10)
    room = models.CharField("지원 호실", max_length=10)
    residency_period = models.CharField("거주 기간", max_length=10)
    is_accepted = models.BooleanField("합격 여부", default=False)
    is_registered = models.BooleanField("등록 여부", default=False)

    def __str__(self):
        return f"{self.user.username}님의 기숙사 지원 정보"
