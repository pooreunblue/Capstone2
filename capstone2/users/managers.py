from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    'nickname'을 주 식별자로 사용하는 커스텀 유저 모델을 위한 관리자 클래스.
    """

    def create_user(self, nickname, password, **extra_fields):
        """
        일반 사용자를 생성합니다. (nickname과 password는 필수)
        """
        if not nickname:
            raise ValueError('The Nickname must be set')

        user = self.model(nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, nickname, password, **extra_fields):
        """
        관리자(superuser)를 생성합니다.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # 위에서 만든 create_user 메서드를 호출하여 관리자를 생성합니다.
        return self.create_user(nickname, password, **extra_fields)