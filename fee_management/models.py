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
    # Fee category checkboxes and their amounts
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

    def __str__(self):
        return f"Semester {self.fee_type.name} - {self.fee_type}: {self.total_amount}"
    
    
class FeeToProgram(models.Model):
    SemesterFee = models.ForeignKey(SemesterFee, on_delete=models.CASCADE, related_name='semester_fees')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    programs = models.ManyToManyField(Program)
    semester_number = models.ManyToManyField(Semester)

class StudentFeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    semester_fee = models.ForeignKey(SemesterFee, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    receipt_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.semester_fee} - {self.amount_paid}"