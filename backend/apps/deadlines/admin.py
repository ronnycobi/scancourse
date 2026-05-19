from django.contrib import admin
from .models import Deadline


@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = ('title', 'deadline_type', 'institution', 'deadline_date', 'is_active')
    list_filter = ('deadline_type', 'is_active')
    search_fields = ('title', 'institution__name')
