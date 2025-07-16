from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from admissions.models import Applicant, AcademicSession, Program, Faculty, Department
from fee_management.models import MeritList, MeritListEntry, FeeVoucher, FeeType, SemesterFee, FeeToProgram
from students.models import Student
from academics.models import Semester
from faculty_staff.models import Office, OfficeStaff

class AdmissionProcessTest(TestCase):
    def setUp(self):
        # Create user and office staff
        self.user = get_user_model().objects.create_user(email='office@example.com', password='password', user_type='Office Staff')
        self.office = Office.objects.create(name='Admissions Office', slug='admissions-office')
        self.office_staff = OfficeStaff.objects.create(user=self.user, office=self.office, full_name='Office Staff')

        # Create academic session, program, etc.
        self.session = AcademicSession.objects.create(name='2025-2029', start_year=2025, end_year=2029, is_active=True)
        self.faculty = Faculty.objects.create(name='Faculty of Science')
        self.department = Department.objects.create(name='Computer Science', faculty=self.faculty)
        self.program = Program.objects.create(name='BSCS', department=self.department)
        self.semester = Semester.objects.create(name='Fall 2025', number=1, program=self.program, session=self.session)

        # Create FeeType and SemesterFee for Admission Fee
        self.admission_fee_type = FeeType.objects.create(name='Admission Fee')
        self.semester_fee = SemesterFee.objects.create(
            fee_type=self.admission_fee_type,
            amount=5000,
            total_amount=5000,
            shift='morning'
        )
        self.fee_to_program = FeeToProgram.objects.create(
            SemesterFee=self.semester_fee,
            academic_session=self.session
        )
        self.fee_to_program.programs.add(self.program)
        self.fee_to_program.semester_number.add(self.semester)

        # Create applicant
        self.applicant = Applicant.objects.create(
            user=self.user,
            session=self.session,
            faculty=self.faculty,
            department=self.department,
            program=self.program,
            status='accepted',
            full_name='Test Applicant',
            cnic='12345-6789012-3',
            dob=date(2005, 1, 1),
            shift='morning'
        )

        # Create MeritList and MeritListEntry
        self.merit_list = MeritList.objects.create(
            program=self.program,
            list_number=1,
            shift='morning',
            AcademicSession=self.session,
            valid_until=date.today() + timedelta(days=30),
            total_seats=1
        )
        self.merit_list_entry = MeritListEntry.objects.create(
            merit_list=self.merit_list,
            applicant=self.applicant,
            merit_position=1,
            relevant_percentage=90.00
        )

        # Log in the office staff user
        self.client.login(email='office@example.com', password='password')

    def test_grant_admission_single(self):
        # Grant admission to a single applicant
        response = self.client.get(reverse('fee_management:grant_admission_single', args=[self.merit_list_entry.id]))

        # Check if the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Refresh data from the database
        self.applicant.refresh_from_db()
        self.merit_list.refresh_from_db()

        # Check if applicant status is updated
        self.assertEqual(self.applicant.status, 'admitted')

        # Check if a student record is created
        self.assertTrue(Student.objects.filter(applicant=self.applicant).exists())
        student = Student.objects.get(applicant=self.applicant)

        # Check if secured seats are incremented
        self.assertEqual(self.merit_list.seccured_seats, 1)

        # Check if a fee voucher is created
        self.assertTrue(FeeVoucher.objects.filter(student=student, semester_fee=self.semester_fee).exists())

    def test_grant_admission_bulk(self):
        # Grant admission to all applicants in the merit list
        response = self.client.get(reverse('fee_management:grant_admission', args=[self.merit_list.id]))

        # Check if the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Refresh data from the database
        self.applicant.refresh_from_db()
        self.merit_list.refresh_from_db()

        # Check if applicant status is updated
        self.assertEqual(self.applicant.status, 'admitted')

        # Check if a student record is created
        self.assertTrue(Student.objects.filter(applicant=self.applicant).exists())
        student = Student.objects.get(applicant=self.applicant)

        # Check if secured seats are incremented
        self.assertEqual(self.merit_list.seccured_seats, 1)

        # Check if a fee voucher is created
        self.assertTrue(FeeVoucher.objects.filter(student=student, semester_fee=self.semester_fee).exists())
