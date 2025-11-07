from rest_framework import serializers
from users.models import User, Message

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True) # 요청 Body에서는 받지 않고 View에서 직접 주입할 수 있도록 허용
    sender_nickname = serializers.CharField(source='sender.nickname', read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    recipient_nickname = serializers.CharField(source='recipient.nickname', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_nickname', 'recipient', 'recipient_nickname', 'content', 'timestamp', 'is_read']
        read_only_fields = ['id', 'sender', 'sender_nickname','recipient_nickname','timestamp', 'is_read']

class ConversationSerializer(serializers.ModelSerializer):
    opponent_nickname = serializers.SerializerMethodField()
    last_message = serializers.CharField(source='content')

    class Meta:
        model = Message
        fields = [
            'id', 'opponent_nickname', 'last_message', 'timestamp', 'is_read'
        ]

    def get_opponent_nickname(self, message):
        request_user = self.context.get('request_user')

        if not request_user:
            return "알 수 없음"

        if message.sender == request_user:
            return message.recipient.nickname
        else:
            return message.sender.nickname
