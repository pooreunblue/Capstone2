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
    class SexChoices(models.TextChoices):
        MALE = 'MALE', '남자'
        FEMALE = 'FEMALE', '여자'

    class ApplicationOrderChoices(models.TextChoices):
        FIRST = 'FIRST', '1차'
        SECOND = 'SECOND', '2차'

    class BuildingChoices(models.TextChoices):
        MYEONGDEOK = 'MYEONGDEOK', '명덕관'
        MYEONGHYEON = 'MYEONGHYEON', '명현관'
        DONG_3 = 'DONG_3', '3동'
        DONG_4 = 'DONG_4', '4동'
        DONG_5 = 'DONG_5', '5동'

    class RoomChoices(models.TextChoices):
        DOUBLE = 'DOUBLE', '2인실'
        QUAD = 'QUAD', '4인실'

    class ResidencyPeriodChoices(models.TextChoices):
        SEMESTER = 'SEMESTER', '학기'
        SIXMONTHS = 'SIXMONTHS', '6개월'

    class AcceptanceChoices(models.TextChoices):
        ACCEPTED = 'ACCEPTED', '선발'
        NOT_ACCEPTED = 'NOT_ACCEPTED', '미선발'

    name = models.CharField("이름", max_length=10)
    sex = models.CharField("성별", max_length=20, choices=SexChoices.choices)
    application_order = models.CharField("신청 차수", max_length=20, choices=ApplicationOrderChoices.choices)
    building = models.CharField("지원 건물", max_length=20, choices=BuildingChoices.choices)
    room = models.CharField("지원 호실", max_length=20, choices=RoomChoices.choices)
    residency_period = models.CharField("거주 기간", max_length=20, choices=ResidencyPeriodChoices.choices)
    is_accepted = models.CharField("합격 여부", max_length=20, choices=AcceptanceChoices.choices)

    def __str__(self):
        return f"{self.user.username}님의 기숙사 지원 정보"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    class SmokingTypeChoices(models.TextChoices):
        NON_SMOKER = 'NON_SMOKER', '비흡연자'
        CIGARETTE = 'CIGARETTE', '연초'
        E_CIGARETTE = 'E_CIGARETTE', '궐련형 전자담배'
        LIQUID = 'LIQUID', '액상형 전자담배'
        MIXED = 'MIXED', '두 종류 이상 혼합 흡연'

    class SmokingAmountChoices(models.TextChoices):
        LESS_THAN_FIVE = 'LESS_THAN_FIVE', '하루 5개비 미만'
        LESS_THAN_TEN = 'LESS_THAN_TEN', '하루 10개비 미만'
        MORE_THAN_TEN = 'MORE_THAN_TEN', '하루 10개비 이상'

    class SleepingHabitChoices(models.TextChoices):
        NONE = 'NONE', '잠버릇 없음'
        SNORING = 'SNORING', '코골이'
        GRINDING = 'GRINDING', '이갈이'
        TALKING = 'TALKING', '잠꼬대'

    class SleepingHabitTimeChoices(models.TextChoices):
        EVERYTIME = 'EVERYTIME', '매번',
        ONLY_WHEN_TIRED = 'ONLY_WHEN_TIRED', '피곤할 때만'

    class SleepingHabitExtentChoices(models.TextChoices):
        WEAK = 'WEAK', '약함'
        NORMAL = 'NORMAL', '보통'
        SEVERE = 'SEVERE', '심함'

    class LifeStyleChoices(models.TextChoices):
        MORNING = 'MORNING', '아침형'
        NIGHT = 'NIGHT', '저녁형'
        IRREGULAR = 'IRREGULAR', '불규칙적'

    class WakeUptimeChoices(models.TextChoices):
        BEFORE_FIVE = 'BEFORE_FIVE', '5시 이전'
        FIVE_TO_SIX = 'FIVE_TO_SIX', '5시부터 6시'
        SIX_TO_SEVEN = 'SIX_TO_SEVEN', '6시부터 7시'
        SEVEN_TO_EIGHT = 'SEVEN_TO_EIGHT', '7시부터 8시'
        AFTER_EIGHT = 'AFTER_EIGHT', '8시 이후'
        FLEXIBLE = 'FLEXIBLE', '유동적'

    class BedTimeChoices(models.TextChoices):
        BEFORE_TEN = 'BEFORE_TEN', '10시 이전'
        TEN_TO_ELEVEN = 'TEN_TO_ELEVEN', '10시부터 11시'
        ELEVEN_TO_TWELVE = 'ELEVEN_TO_TWELVE', '11시부터 12시'
        TWELVE_TO_ONE = 'TWELVE_TO_ONE', '12시부터 1시'
        ONE_TO_TWO = 'ONE_TO_TWO', '1시부터 2시'
        AFTER_TWO = 'AFTER_TWO', '2시 이후'

    class CleaningCycleChoices(models.TextChoices):
        EVERYDAY = 'EVERYDAY', '매일'
        TWICE_A_WEEK = 'TWICE_A_WEEK', '한 주에 두 번'
        ONCE_A_WEEK = 'ONCE_A_WEEK', '한 주에 한 번'
        ONCE_IN_A_WHILE = 'ONCE_IN_A_WHILE', '가끔씩'
        RARELY = 'RARELY', '거의 하지 않음'

    class EatingInRoomChoices(models.TextChoices):
        NEVER = 'NEVER', '절대 안 함'
        SOMETIMES = 'SOMETIMES', '가끔'
        OFTEN = 'OFTEN', '자주'

    smoking_type = models.CharField("흡연 종류", max_length=20, choices=SmokingTypeChoices.choices, blank=True)
    smoking_amount = models.CharField("흡연량", max_length=20, choices=SmokingAmountChoices.choices, blank=True, null=True)
    sleeping_habit = models.CharField("잠버릇 종류", max_length=20, choices=SleepingHabitChoices.choices, blank=True)
    sleeping_habit_time = models.CharField("잠버릇 빈도", max_length=20, choices=SleepingHabitTimeChoices.choices, blank=True, null=True)
    sleeping_habit_extent = models.CharField("잠버릇 강도", max_length=20, choices=SleepingHabitExtentChoices.choices, blank=True, null=True)
    life_style = models.CharField("생활 스타일", max_length=20, choices=LifeStyleChoices.choices, blank=True)
    wake_up_time = models.CharField("기상 시간", max_length=20, choices=WakeUptimeChoices.choices, blank=True)
    bed_time = models.CharField("취침 시간", max_length=20, choices=BedTimeChoices.choices, blank=True)
    cleaning_cycle = models.CharField("청소 주기", max_length=20, choices=CleaningCycleChoices.choices, blank=True)
    eating_in_room = models.CharField("실내 취식 여부", max_length=20, choices=EatingInRoomChoices.choices, blank=True)

    def __str__(self):
        return f"{self.user.username}님의 프로필"