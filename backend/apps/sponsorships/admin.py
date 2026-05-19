from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Sponsor, SponsorshipPlan, Sponsorship, SponsorshipImpression, SponsorshipClick


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sponsor_type', 'contact_email', 'is_active', 'active_sponsorships')
    list_filter = ('sponsor_type', 'is_active')
    search_fields = ('name', 'contact_email')
    prepopulated_fields = {'slug': ('name',)}

    def active_sponsorships(self, obj):
        return obj.sponsorships.filter(status='active').count()


@admin.register(SponsorshipPlan)
class SponsorshipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'monthly_price_zar', 'priority_boost', 'has_featured_card', 'has_homepage_banner')
    list_filter = ('tier',)


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = (
        'sponsor', 'plan', 'target', 'status',
        'starts_at', 'ends_at', 'amount_paid_zar',
        'impression_total', 'click_total',
    )
    list_filter = ('status', 'plan__tier')
    search_fields = ('sponsor__name', 'bursary__name', 'institution__name', 'invoice_number')
    actions = ['activate_sponsorships', 'expire_sponsorships', 'sync_bursary_promotion']

    def target(self, obj):
        if obj.bursary:
            return f'Bursary: {obj.bursary.name}'
        if obj.institution:
            return f'Institution: {obj.institution.name}'
        return 'general'

    def impression_total(self, obj):
        return obj.impressions.count()
    impression_total.short_description = 'Impressions'

    def click_total(self, obj):
        return obj.clicks.count()
    click_total.short_description = 'Clicks'

    def activate_sponsorships(self, request, queryset):
        count = queryset.update(status='active')
        self._sync_promotion_for(queryset)
        self.message_user(request, f'Activated {count} sponsorship(s).')
    activate_sponsorships.short_description = 'Activate selected sponsorships'

    def expire_sponsorships(self, request, queryset):
        count = queryset.update(status='expired')
        self._sync_promotion_for(queryset)
        self.message_user(request, f'Expired {count} sponsorship(s).')
    expire_sponsorships.short_description = 'Expire selected sponsorships'

    def sync_bursary_promotion(self, request, queryset):
        from .promotion import sync_all_bursary_promotion
        sync_all_bursary_promotion()
        self.message_user(request, 'Re-synced sponsored bursary flags.')
    sync_bursary_promotion.short_description = 'Re-sync bursary promotion (full)'

    def _sync_promotion_for(self, queryset):
        from .promotion import sync_bursary_promotion
        for s in queryset:
            if s.bursary_id:
                sync_bursary_promotion(s.bursary)


@admin.register(SponsorshipImpression)
class SponsorshipImpressionAdmin(admin.ModelAdmin):
    list_display = ('sponsorship', 'placement', 'user', 'timestamp')
    list_filter = ('placement',)
    readonly_fields = ('sponsorship', 'user', 'placement', 'timestamp')


@admin.register(SponsorshipClick)
class SponsorshipClickAdmin(admin.ModelAdmin):
    list_display = ('sponsorship', 'action', 'user', 'timestamp')
    list_filter = ('action',)
    readonly_fields = ('sponsorship', 'user', 'action', 'referrer', 'timestamp')
