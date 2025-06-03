from django.contrib import admin
from .models import Payment



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_session_id', 'amount', 'status', 'created_at')
    search_fields = ('applicant__user__firstname', 'status')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
# Register your models here.
