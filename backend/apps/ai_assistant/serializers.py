from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'role', 'content', 'created_at')


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ('id', 'title', 'last_message', 'messages', 'created_at', 'updated_at')

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        return msg.content[:100] if msg else ''


class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    session_id = serializers.IntegerField(required=False, allow_null=True)


class MotivationLetterSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import MotivationLetter
        model = MotivationLetter
        fields = '__all__'
        read_only_fields = ('user', 'content', 'revision_count', 'created_at', 'updated_at')


class MotivationLetterGenerateSerializer(serializers.Serializer):
    course_name = serializers.CharField(max_length=200)
    institution_name = serializers.CharField(max_length=200)
    student_background = serializers.CharField(max_length=2000)
    key_achievements = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    why_this_course = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    why_this_institution = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    additional_info = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    tone = serializers.ChoiceField(
        choices=['professional', 'warm', 'confident', 'humble'],
        default='professional', required=False,
    )
    language = serializers.ChoiceField(
        choices=['en', 'zu', 'xh', 'af', 'st'],
        default='en', required=False,
    )


class MotivationLetterRefineSerializer(serializers.Serializer):
    feedback = serializers.CharField(max_length=1000)
