from rest_framework import serializers
from users.models import User, DormInfo, Profile

class MyUserSerializer(serializers.ModelSerializer):
    application_order_display = serializers.CharField(source='get_application_order_display', read_only=False)

    class Meta:
        model = User
        fields = ['nickname', 'application_order_display']
        read_only_fields = fields

class MyDormInfoSerializer(serializers.ModelSerializer):
    sex = serializers.CharField(source='get_sex_display', read_only=True)
    building = serializers.CharField(source='get_building_display', read_only=True)
    room = serializers.CharField(source='get_room_display', read_only=True)
    residency_period = serializers.CharField(source='get_residency_period_display', read_only=True)
    is_accepted = serializers.CharField(source='get_is_accepted_display', read_only=True)

    class Meta:
        model = DormInfo
        fields = [
            'name', 'student_id', 'sex', 'building', 'room',
            'residency_period', 'selected_semester', 'is_accepted'
        ]
        read_only_fields = fields

class MyProfileSerializer(serializers.ModelSerializer):
    # --- GET 요청 시 보여줄 한글 표시 필드 (읽기 전용) ---
    age = serializers.CharField(source='get_age_display')
    grade = serializers.CharField(source='get_grade_display', read_only=True)
    smoking_type = serializers.CharField(source='get_smoking_type_display', read_only=True)
    smoking_amount = serializers.CharField(source='get_smoking_amount_display', read_only=True)
    sleeping_habit = serializers.CharField(source='get_sleeping_habit_display', read_only=True)
    sleeping_habit_freq = serializers.CharField(source='get_sleeping_habit_freq_display', read_only=True)
    sleeping_habit_extent = serializers.CharField(source='get_sleeping_habit_extent_display', read_only=True)
    life_style = serializers.CharField(source='get_life_style_display', read_only=True)
    wake_up_time = serializers.CharField(source='get_wake_up_time_display', read_only=True)
    bed_time = serializers.CharField(source='get_bed_time_display', read_only=True)
    pre_sleeping_life_style = serializers.CharField(source='get_pre_sleeping_life_style_display', read_only=True)
    sensitivity_to_sleep = serializers.CharField(source='get_sensitivity_to_sleep_display', read_only=True)
    cleaning_cycle = serializers.CharField(source='get_cleaning_cycle_display', read_only=True)
    eating_in_room = serializers.CharField(source='get_eating_in_room_display', read_only=True)

    class Meta:
        model = Profile
        # '내' 정보이므로 모든 필드를 한글로 포함
        fields = [
            'age', 'grade', 'smoking_type', 'smoking_amount',
            'sleeping_habit', 'sleeping_habit_freq', 'sleeping_habit_extent',
            'life_style', 'wake_up_time', 'bed_time', 'pre_sleeping_life_style',
            'sensitivity_to_sleep', 'cleaning_cycle', 'eating_in_room'
        ]
        read_only_fields = fields