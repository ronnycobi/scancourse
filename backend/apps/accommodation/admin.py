from django.contrib import admin
from .models import Accommodation, AccommodationImage


class AccommodationImageInline(admin.TabularInline):
    model = AccommodationImage
    extra = 1


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'province', 'room_type', 'price_per_month', 'nsfas_accredited', 'is_active')
    list_filter = ('province', 'room_type', 'nsfas_accredited', 'is_active')
    search_fields = ('name', 'address', 'city')
    inlines = [AccommodationImageInline]
