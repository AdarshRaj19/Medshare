from django.contrib import admin
from .models import (
    Medicine, DonationRequest, UserProfile, MedicineRating, MedicineSearchLog, 
    Notification, ContactMessage, Testimonial, FAQ, PasswordResetToken
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization_name', 'verified', 'created_at')
    list_filter = ('role', 'verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'organization_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'donor', 'quantity', 'expiry_date', 'status', 'rating', 'created_at')
    list_filter = ('status', 'created_at', 'expiry_date')
    search_fields = ('name', 'donor__username', 'description')
    readonly_fields = ('created_at', 'updated_at', 'viewed_by')
    fieldsets = (
        ('Basic Information', {
            'fields': ('donor', 'name', 'description', 'image')
        }),
        ('Quantity & Storage', {
            'fields': ('quantity', 'unit', 'storage_condition')
        }),
        ('Dates', {
            'fields': ('expiry_date', 'manufacture_date')
        }),
        ('Batch & Location', {
            'fields': ('batch_number', 'location_name', 'latitude', 'longitude')
        }),
        ('Status & Rating', {
            'fields': ('status', 'rating', 'rating_count', 'recommendation_score')
        }),
        ('Tracking', {
            'fields': ('viewed_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'medicine', 'ngo', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'medicine__donor')
    search_fields = ('medicine__name', 'ngo__username', 'medicine__donor__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Request Details', {
            'fields': ('medicine', 'ngo', 'status')
        }),
        ('Request Info', {
            'fields': ('quantity_requested', 'message')
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MedicineRating)
class MedicineRatingAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('medicine__name', 'user__username', 'review')
    readonly_fields = ('created_at',)

@admin.register(MedicineSearchLog)
class MedicineSearchLogAdmin(admin.ModelAdmin):
    list_display = ('search_query', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('search_query', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'approved', 'created_at')
    list_filter = ('role', 'approved', 'created_at')
    search_fields = ('name', 'message', 'user__username')
    readonly_fields = ('created_at',)
    actions = ['approve_testimonials']

    def approve_testimonials(self, request, queryset):
        queryset.update(approved=True)
        self.message_user(request, f"{queryset.count()} testimonials approved.")
    approve_testimonials.short_description = "Approve selected testimonials"

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'active')
    list_filter = ('category', 'active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'active')
    ordering = ('order',)

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'used')
    list_filter = ('used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at')