from django.contrib import admin
from .models import Institution


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution_type', 'province', 'application_open', 'application_deadline', 'is_active')
    list_filter = ('institution_type', 'province', 'application_open', 'nsfas_accredited', 'is_active')
    search_fields = ('name', 'short_name', 'city')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('application_open', 'is_active')


# Required for autocomplete_fields in CourseOfferingAdmin
@admin.action(description='Activate selected')
def activate(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description='Deactivate selected')
def deactivate(modeladmin, request, queryset):
    queryset.update(is_active=False)


InstitutionAdmin.actions = [activate, deactivate]
