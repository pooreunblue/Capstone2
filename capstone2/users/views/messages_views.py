from django.db.models import Q, Max
from rest_framework import generics, serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from users.models import Message
from users.serializers import MessageSerializer, ConversationSerializer
from users.utils import get_user_from_header

class MessageSendView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        sender = get_user_from_header(self.request)
        if not sender:
            raise serializers.ValidationError("헤더에 유효한 X-User-ID가 없습니다.")

        recipient_id = self.request.data.get('recipient')
        if not recipient_id:
            raise serializers.ValidationError({"recipient": "받는 사람 ID가 필요합니다."})

        if str(sender.id) == str(recipient_id):
            raise serializers.ValidationError("자기 자신에게 쪽지를 보낼 수 없습니다.")

        serializer.save(sender=sender)

class ConversationListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = get_user_from_header(self.request)
        if not user:
            return Message.objects.none()

        all_messages = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient')

        opponent_ids = set()
        for msg in all_messages:
            if msg.sender_id == user.id:
                opponent_ids.add(msg.recipient_id)
            else:
                opponent_ids.add(msg.sender_id)

        latest_message_ids = []
        for opp_id in opponent_ids:
            latest_msg_id = all_messages.filter(
                Q(sender_id=user.id, recipient_id=opp_id) |
                Q(sender_id=opp_id, recipient_id=user.id)
            ).aggregate(Max('id')).get('id__max')

            if latest_msg_id:
                latest_message_ids.append(latest_msg_id)

        queryset = Message.objects.filter(
            id__in=latest_message_ids
        ).order_by('-timestamp')

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request_user'] = get_user_from_header(self.request)
        return context

class ConversationDetailView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = get_user_from_header(self.request)
        if not user:
            return Message.objects.none()

        opponent_id = self.kwargs.get('user_id')
        if not opponent_id:
            return Message.objects.none()

        Message.objects.filter(
            sender_id=opponent_id,
            recipient=user,
            is_read=False
        ).update(is_read=True)

        queryset = Message.objects.filter(
            (Q(sender=user) & Q(recipient_id=opponent_id)) |
            (Q(sender_id=opponent_id) & Q(recipient=user))
        ).select_related('sender', 'recipient').order_by('timestamp')

        return queryset