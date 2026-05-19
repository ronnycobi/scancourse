import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatInputSerializer, ChatMessageSerializer
from .ai_service import get_ai_response

logger = logging.getLogger(__name__)


class ChatView(APIView):
    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')

        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(user=request.user)
        else:
            session = ChatSession.objects.create(user=request.user)

        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in session.messages.order_by('created_at')
        ]

        ChatMessage.objects.create(session=session, role='user', content=message)

        try:
            ai_reply = get_ai_response(request.user, message, history)
        except Exception as e:
            logger.exception(f'AI error: {e}')
            ai_reply = "I'm sorry, I'm having trouble right now. Please try again in a moment."

        ChatMessage.objects.create(session=session, role='assistant', content=ai_reply)

        if not session.title and len(message) > 5:
            session.title = message[:50]
            session.save(update_fields=['title'])

        return Response({
            'session_id': session.id,
            'reply': ai_reply,
        })


class ChatSessionListView(generics.ListAPIView):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


# ════════════════════════════════════════════════════════════════
# Motivation Letter Generator
# ════════════════════════════════════════════════════════════════

class MotivationLetterListView(generics.ListAPIView):
    from .serializers import MotivationLetterSerializer
    serializer_class = MotivationLetterSerializer

    def get_queryset(self):
        from .models import MotivationLetter
        return MotivationLetter.objects.filter(user=self.request.user)


class MotivationLetterDetailView(generics.RetrieveUpdateDestroyAPIView):
    from .serializers import MotivationLetterSerializer
    serializer_class = MotivationLetterSerializer

    def get_queryset(self):
        from .models import MotivationLetter
        return MotivationLetter.objects.filter(user=self.request.user)


class MotivationLetterGenerateView(APIView):
    def post(self, request):
        from .serializers import MotivationLetterGenerateSerializer, MotivationLetterSerializer
        from .models import MotivationLetter
        from .motivation_letter import generate_motivation_letter

        serializer = MotivationLetterGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            student_name = (
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            )
            content = generate_motivation_letter(
                student_name=student_name,
                course_name=data['course_name'],
                institution_name=data['institution_name'],
                student_background=data['student_background'],
                key_achievements=data.get('key_achievements', ''),
                why_this_course=data.get('why_this_course', ''),
                why_this_institution=data.get('why_this_institution', ''),
                additional_info=data.get('additional_info', ''),
                tone=data.get('tone', 'professional'),
                language=data.get('language', 'en'),
            )
        except Exception as e:
            logger.exception(f'Motivation letter generation failed: {e}')
            return Response(
                {'detail': "Sorry, we couldn't generate that right now. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        letter = MotivationLetter.objects.create(
            user=request.user,
            title=f"{data['course_name']} @ {data['institution_name']}",
            course_name=data['course_name'],
            institution_name=data['institution_name'],
            student_background=data['student_background'],
            key_achievements=data.get('key_achievements', ''),
            why_this_course=data.get('why_this_course', ''),
            why_this_institution=data.get('why_this_institution', ''),
            additional_info=data.get('additional_info', ''),
            tone=data.get('tone', 'professional'),
            language=data.get('language', 'en'),
            content=content,
            revision_count=0,
        )

        return Response(MotivationLetterSerializer(letter).data, status=status.HTTP_201_CREATED)


class MotivationLetterRefineView(APIView):
    def post(self, request, pk):
        from .serializers import MotivationLetterRefineSerializer, MotivationLetterSerializer
        from .models import MotivationLetter
        from .motivation_letter import refine_motivation_letter

        try:
            letter = MotivationLetter.objects.get(pk=pk, user=request.user)
        except MotivationLetter.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if letter.is_finalised:
            return Response({'detail': 'This letter has been finalised.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MotivationLetterRefineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_content = refine_motivation_letter(
                letter.content,
                serializer.validated_data['feedback'],
            )
        except Exception as e:
            logger.exception(f'Motivation letter refine failed: {e}')
            return Response(
                {'detail': "Couldn't refine. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        letter.content = new_content
        letter.revision_count += 1
        letter.save(update_fields=['content', 'revision_count', 'updated_at'])
        return Response(MotivationLetterSerializer(letter).data)


class MotivationLetterFinaliseView(APIView):
    def post(self, request, pk):
        from .serializers import MotivationLetterSerializer
        from .models import MotivationLetter

        try:
            letter = MotivationLetter.objects.get(pk=pk, user=request.user)
        except MotivationLetter.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        letter.is_finalised = True
        letter.save(update_fields=['is_finalised', 'updated_at'])
        return Response(MotivationLetterSerializer(letter).data)
