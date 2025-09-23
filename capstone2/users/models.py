from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField("전화번호", max_length=11, unique=True, blank=True)
    email = models.EmailField("이메일", unique=True, blank=True)
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username