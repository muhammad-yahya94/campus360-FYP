from django.contrib import admin
from .models import FeeType, SemesterFee, FeeToProgram, StudentFeePayment, FeeVoucher

class SemesterFeeAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'shift', 'total_amount', 'is_active')
    list_filter = ('fee_type', 'shift', 'is_active')
    search_fields = ('fee_type__name', 'dynamic_fees')
    readonly_fields = ('total_amount',)

    def save_model(self, request, obj, form, change):
        # Calculate total amount from dynamic_fees
        if obj.dynamic_fees:
            obj.total_amount = sum(
                float(amount) 
                for fee_head, amount in obj.dynamic_fees.items() 
                if amount and str(amount).replace('.', '').isdigit()
            )
        super().save_model(request, obj, form, change)

admin.site.register(FeeType)
admin.site.register(SemesterFee, SemesterFeeAdmin)
admin.site.register(FeeToProgram)
admin.site.register(StudentFeePayment)
admin.site.register(FeeVoucher)

