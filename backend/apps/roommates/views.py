from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import RoommateProfile, RoommateMatch, RoommateMessage
from .serializers import (
    RoommateProfileSerializer, MatchCandidateSerializer, RoommateMessageSerializer,
)
from .matcher import find_matches, compatibility_score


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = RoommateProfileSerializer

    def get_object(self):
        profile, _ = RoommateProfile.objects.get_or_create(user=self.request.user)
        return profile


class MatchesView(APIView):
    def get(self, request):
        try:
            profile = request.user.roommate_profile
        except RoommateProfile.DoesNotExist:
            return Response({'detail': 'Create a roommate profile first.'}, status=status.HTTP_400_BAD_REQUEST)

        if not profile.is_active:
            return Response({'detail': 'Your profile is paused. Activate it to see matches.'},
                            status=status.HTTP_400_BAD_REQUEST)

        matches = find_matches(profile, limit=20)
        data = []
        for candidate, score in matches:
            serialized = MatchCandidateSerializer(candidate).data
            serialized['score'] = score
            data.append(serialized)
        return Response(data)


class LikeView(APIView):
    """Send a 'like' to another roommate. If they already liked you, it becomes a match."""

    def post(self, request, pk):
        try:
            from_profile = request.user.roommate_profile
            to_profile = RoommateProfile.objects.get(pk=pk)
        except (RoommateProfile.DoesNotExist, AttributeError):
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if from_profile.id == to_profile.id:
            return Response({'detail': "Can't like yourself."}, status=status.HTTP_400_BAD_REQUEST)

        score = compatibility_score(from_profile, to_profile)

        my_match, _ = RoommateMatch.objects.update_or_create(
            from_profile=from_profile, to_profile=to_profile,
            defaults={'status': 'liked', 'score': score},
        )

        # Did they already like me?
        their_like = RoommateMatch.objects.filter(
            from_profile=to_profile, to_profile=from_profile, status__in=['liked', 'matched']
        ).first()

        if their_like:
            my_match.status = 'matched'
            their_like.status = 'matched'
            my_match.save()
            their_like.save()
            return Response({'matched': True, 'score': score})

        return Response({'matched': False, 'score': score})


class PassView(APIView):
    def post(self, request, pk):
        try:
            from_profile = request.user.roommate_profile
            to_profile = RoommateProfile.objects.get(pk=pk)
        except (RoommateProfile.DoesNotExist, AttributeError):
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        RoommateMatch.objects.update_or_create(
            from_profile=from_profile, to_profile=to_profile,
            defaults={'status': 'passed'},
        )
        return Response({'detail': 'Passed.'})


class MyMatchesView(APIView):
    def get(self, request):
        try:
            profile = request.user.roommate_profile
        except RoommateProfile.DoesNotExist:
            return Response([])

        matches = RoommateMatch.objects.filter(
            from_profile=profile, status='matched'
        ).select_related('to_profile__user', 'to_profile__institution')

        data = []
        for m in matches:
            serialized = MatchCandidateSerializer(m.to_profile).data
            serialized['score'] = m.score
            data.append(serialized)
        return Response(data)


class MessageThreadView(APIView):
    def get(self, request, pk):
        try:
            mine = request.user.roommate_profile
            theirs = RoommateProfile.objects.get(pk=pk)
        except RoommateProfile.DoesNotExist:
            return Response([])

        messages = RoommateMessage.objects.filter(
            sender__in=[mine, theirs],
            recipient__in=[mine, theirs],
        ).order_by('created_at')

        # Mark inbound as read
        RoommateMessage.objects.filter(sender=theirs, recipient=mine, is_read=False).update(is_read=True)

        return Response(RoommateMessageSerializer(messages, many=True).data)

    def post(self, request, pk):
        try:
            mine = request.user.roommate_profile
            theirs = RoommateProfile.objects.get(pk=pk)
        except RoommateProfile.DoesNotExist:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Must be matched to message
        is_matched = RoommateMatch.objects.filter(
            from_profile=mine, to_profile=theirs, status='matched'
        ).exists()
        if not is_matched:
            return Response({'detail': 'You can only message matched roommates.'}, status=status.HTTP_403_FORBIDDEN)

        body = request.data.get('body', '').strip()
        if not body:
            return Response({'detail': 'Message body required.'}, status=status.HTTP_400_BAD_REQUEST)

        msg = RoommateMessage.objects.create(sender=mine, recipient=theirs, body=body[:2000])
        return Response(RoommateMessageSerializer(msg).data, status=status.HTTP_201_CREATED)
