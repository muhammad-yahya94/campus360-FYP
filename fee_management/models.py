from django.db import models
from django.utils import timezone
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
    receipt_number = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        null=True,
        blank=True
    )
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"A{uuid.uuid4().hex[:7].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.semester_fee} - {self.amount_paid}"

class FeeVoucher(models.Model):
    voucher_id = models.CharField(max_length=50, unique=True, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='vouchers')
    semester_fee = models.ForeignKey(SemesterFee, on_delete=models.CASCADE, related_name='vouchers')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='fee_vouchers')
    due_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment = models.OneToOneField(
        'StudentFeePayment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='voucher'
    )
    office = models.ForeignKey(
        Office, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vouchers'
    )

    class Meta:
        unique_together = ('student', 'semester', 'semester_fee')
        ordering = ['-generated_at']

    def save(self, *args, **kwargs):
        if not self.voucher_id:
            self.voucher_id = f"EDU{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def mark_as_paid(self, payment, commit=True):
        """
        Mark this voucher as paid and link it to a payment
        """
        # Check if this payment is already linked to another voucher
        existing_voucher = FeeVoucher.objects.filter(payment=payment).exclude(id=self.id).first()
        if existing_voucher:
            raise ValueError(f'This payment is already linked to voucher {existing_voucher.voucher_id}')
            
        self.is_paid = True
        self.paid_at = timezone.now()
        self.payment = payment
        if commit:
            self.save(update_fields=['is_paid', 'paid_at', 'payment'])

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"Voucher {self.voucher_id} - {self.student} - {self.semester} ({status})"