from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('mark-read/', views.MarkReadView.as_view(), name='notification-mark-read'),
    path('unread-count/', views.UnreadCountView.as_view(), name='notification-unread-count'),
]
