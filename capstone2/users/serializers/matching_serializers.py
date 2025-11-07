from rest_framework import serializers
from users.models import Profile

class MatchingSummarySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    smoking_type = serializers.CharField(source='get_smoking_type_display', read_only=True)
    sleeping_habit = serializers.CharField(source='get_sleeping_habit_display', read_only=True)
    class Meta:
        model = Profile
        fields = [
            'user_id', 'nickname',
            'smoking_type', 'sleeping_habit'
        ]
        read_only_fields = fields

class PublicProfileSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    age = serializers.CharField(source='get_age_display', read_only=True)
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
    sensitivity_to_sleep= serializers.CharField(source='get_sensitivity_to_sleep_display', read_only=True)
    cleaning_cycle = serializers.CharField(source='get_cleaning_cycle_display', read_only=True)
    eating_in_room = serializers.CharField(source='get_eating_in_room_display', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'nickname', 'age',
            'grade', 'smoking_type', 'smoking_amount', 'sleeping_habit',
            'sleeping_habit_freq', 'sleeping_habit_extent',
            'life_style', 'wake_up_time', 'bed_time',
            'pre_sleeping_life_style', 'sensitivity_to_sleep',
            'cleaning_cycle', 'eating_in_room'
        ]
        read_only_fields = fields
