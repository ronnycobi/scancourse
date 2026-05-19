from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='ai-chat'),
    path('sessions/', views.ChatSessionListView.as_view(), name='chat-sessions'),
    path('sessions/<int:pk>/', views.ChatSessionDetailView.as_view(), name='chat-session-detail'),

    # Motivation letter generator
    path('motivation-letters/', views.MotivationLetterListView.as_view(), name='motivation-list'),
    path('motivation-letters/generate/', views.MotivationLetterGenerateView.as_view(), name='motivation-generate'),
    path('motivation-letters/<int:pk>/', views.MotivationLetterDetailView.as_view(), name='motivation-detail'),
    path('motivation-letters/<int:pk>/refine/', views.MotivationLetterRefineView.as_view(), name='motivation-refine'),
    path('motivation-letters/<int:pk>/finalise/', views.MotivationLetterFinaliseView.as_view(), name='motivation-finalise'),
]
