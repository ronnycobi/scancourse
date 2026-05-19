from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkReadView(APIView):
    def post(self, request):
        notification_ids = request.data.get('ids', [])
        if notification_ids:
            Notification.objects.filter(user=request.user, id__in=notification_ids).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user).update(is_read=True)
        return Response({'detail': 'Marked as read.'})


class UnreadCountView(APIView):
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
