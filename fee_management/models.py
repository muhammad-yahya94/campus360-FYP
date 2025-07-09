from django.db import models
from students.models import Student
from academics.models import Program, Semester
from admissions.models import AcademicSession
import uuid
from faculty_staff.models import Office

class FeeType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class SemesterFee(models.Model):
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE, related_name='semester_fees')
    is_active = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    computer_fee = models.BooleanField(default=False)
    computer_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    examination_fund = models.BooleanField(default=False)
    examination_fund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tuition_fee = models.BooleanField(default=False)
    tuition_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    others = models.BooleanField(default=False)
    others_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    evening_fund = models.BooleanField(default=False)
    evening_fund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shift = models.CharField(max_length=10, choices=[
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    ], help_text="Select the preferred shift for the students.")
    def __str__(self):
        return f"Semester {self.fee_type.name} - {self.fee_type}: {self.total_amount}"
    
class FeeToProgram(models.Model):
    SemesterFee = models.ForeignKey(SemesterFee, on_delete=models.CASCADE, related_name='semester_fees')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    programs = models.ManyToManyField(Program)
    semester_number = models.ManyToManyField(Semester)
    
    def __str__(self):
        return f"Semester {self.SemesterFee} - {self.semester_number}"


class StudentFeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    semester_fee = models.ForeignKey(SemesterFee, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    receipt_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.semester_fee} - {self.amount_paid}"

class FeeVoucher(models.Model):
    voucher_id = models.CharField(max_length=50, unique=True, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='vouchers')
    semester_fee = models.ForeignKey(SemesterFee, on_delete=models.CASCADE, related_name='vouchers')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    due_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.voucher_id:
            self.voucher_id = f"EDU{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('student', 'semester', 'semester_fee')

    def __str__(self):
        return f"Voucher {self.voucher_id} - {self.student} - {self.semester}"