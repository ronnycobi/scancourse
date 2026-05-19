from django.contrib import admin
from .models import Bursary


@admin.register(Bursary)
class BursaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'field', 'funding_type', 'province', 'application_deadline', 'is_active')
    list_filter = ('field', 'funding_type', 'province', 'is_active')
    search_fields = ('name', 'provider', 'description')
    list_editable = ('is_active',)
