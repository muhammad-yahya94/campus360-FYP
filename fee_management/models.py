from django.db import models
from django.utils import timezone
from students.models import Student
from users.models import CustomUser
from academics.models import Program, Semester
from admissions.models import AcademicSession , Applicant ,AcademicQualification
import uuid
from faculty_staff.models import Office

class FeeType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# JSONField import compatible with different Django versions
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

class SemesterFee(models.Model):
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE, related_name='semester_fees')
    is_active = models.BooleanField(default=True)
    shift = models.CharField(max_length=10, choices=[
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    ], help_text="Select the preferred shift for the students.")
    dynamic_fees = JSONField(default=dict)  # Store dynamic fee heads and amounts
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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
            from datetime import datetime
            now = datetime.now()    
            # Format: YYYYMMDDHHMMSS
            timestamp = now.strftime("%Y%m%d%H%M%S")
            self.receipt_number = f"{timestamp}"
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
            from datetime import datetime
            now = datetime.now()
            # Format: YYYYMMDDHHMMSS
            timestamp = now.strftime("%Y%m%d%H%M%S")
            self.voucher_id = f"{timestamp}"
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

class MeritList(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    ]
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='merit_lists')
    list_number = models.PositiveIntegerField(help_text="Sequence number of this merit list")
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, help_text="Shift for the merit list", default='Morning')
    academic_session = models.ForeignKey(AcademicSession,on_delete=models.CASCADE, related_name='merit_lists',default=None, null=True,blank=True    )
    generation_date = models.DateField(auto_now_add=True)
    total_seats = models.PositiveIntegerField(default=0, help_text="Total number of applicants in this merit list")
    seccured_seats = models.PositiveIntegerField(default=0, help_text="Number of seats secured from this merit list")
    valid_until = models.DateTimeField(help_text="Date until which this merit list is valid")
    is_active = models.BooleanField(default=True, help_text="Is this the currently active merit list?")
    notes = models.TextField(blank=True, help_text="Any additional notes about this merit list")

    class Meta:
        unique_together = ('program', 'list_number', 'shift')
        ordering = ['-generation_date']

    def _str_(self):
        return f"Merit List #{self.list_number} - {self.program} ({self.shift})"
    def save(self, *args, **kwargs):
        # Ensure only one active merit list per program and shift
        if self.is_active:
            MeritList.objects.filter(
                program=self.program,
                shift=self.shift,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class MeritListEntry(models.Model):
    """
    Model to store selected candidates in each merit list
    """
    STATUS_CHOICES = [
        ('selected', 'Selected'),
        ('admitted', 'Admitted'),
    ]
    
    merit_list = models.ForeignKey(MeritList, on_delete=models.CASCADE, related_name='entries')
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='merit_list_entries')
    merit_position = models.PositiveIntegerField(help_text="Ranking position in the merit list")
    relevant_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Relevant percentage based on program level (Intermediate for BS, Bachelor's for MS)"
    )
    qualification_used = models.ForeignKey(
        AcademicQualification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Reference to the academic qualification used for merit calculation"
    )
    passing_year = models.PositiveIntegerField(null=True, blank=True, help_text="Passing year of the qualification used")
    marks_obtained = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text="Marks obtained in the qualification used")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='selected',
        help_text="Current status of the candidate in this merit list"
    )
    selection_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, help_text="Any additional remarks about this candidate")

    class Meta:
        unique_together = ('merit_list', 'applicant')
        ordering = ['merit_position']

    def _str_(self):
        return f"#{self.merit_position} - {self.applicant.full_name} ({self.relevant_percentage}%) - {self.status}"
    
class OfficeToHODNotification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='office_notifications_sent')
    departments = models.ManyToManyField('academics.Department', related_name='notifications', blank=True)
    attached_file = models.FileField(upload_to='notifications/', blank=True, null=True)

    def __str__(self):
        return self.title
