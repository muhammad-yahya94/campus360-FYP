from django.contrib import admin
from .models import FeeType, SemesterFee, StudentFeePayment, FeeToProgram
from faculty_staff.models import Office


admin.site.register(FeeType)
admin.site.register(SemesterFee)
admin.site.register(FeeToProgram)
admin.site.register(StudentFeePayment)
