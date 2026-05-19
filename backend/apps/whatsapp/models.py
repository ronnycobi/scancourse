from django.db import models
from django.conf import settings


class WhatsAppSession(models.Model):
    """
    Tracks conversation state per WhatsApp number.
    State machine: each user is in a 'state' which determines how the next message is interpreted.
    """

    STATE_CHOICES = [
        ('idle', 'Idle (showing menu)'),
        ('awaiting_marks', 'Waiting for marks input'),
        ('awaiting_photo', 'Waiting for report photo'),
        ('awaiting_bursary_pick', 'Waiting for bursary number'),
        ('awaiting_uni_pick', 'Waiting for university name'),
        ('chatting_ai', 'Chatting with AI'),
    ]

    phone_number = models.CharField(max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='whatsapp_sessions',
    )
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default='idle')
    context = models.JSONField(default=dict, blank=True)
    last_message_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'whatsapp_sessions'

    def __str__(self):
        return f'{self.phone_number} ({self.state})'

    def reset(self):
        self.state = 'idle'
        self.context = {}
        self.save(update_fields=['state', 'context', 'last_message_at'])


class WhatsAppMessage(models.Model):
    """Audit log of every inbound + outbound message."""

    DIRECTION_CHOICES = [('in', 'Inbound'), ('out', 'Outbound')]

    session = models.ForeignKey(WhatsAppSession, on_delete=models.CASCADE, related_name='messages')
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    body = models.TextField(blank=True)
    media_url = models.URLField(blank=True)
    twilio_sid = models.CharField(max_length=64, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'whatsapp_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.direction}] {self.session.phone_number}: {self.body[:60]}'
