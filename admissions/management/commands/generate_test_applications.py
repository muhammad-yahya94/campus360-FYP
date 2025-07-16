from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from admissions.models import Applicant, AcademicQualification, ExtraCurricularActivity
from academics.models import Program, Department, Faculty
from admissions.models import AcademicSession
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker()

islamic_male_names = [
    "Ahmed", "Ali", "Hassan", "Hussain", "Omar", "Yusuf", "Ibrahim", "Abdullah", "Zain", "Bilal",
    "Faisal", "Khalid", "Sami", "Tariq", "Naveed", "Imran", "Junaid", "Saad", "Usman", "Zubair"
]

islamic_female_names = [
    "Aisha", "Fatima", "Zainab", "Khadija", "Maryam", "Sumayyah", "Sara", "Hina", "Nadia", "Sana",
    "Amna", "Rabia", "Noor", "Lubna", "Sadia", "Rania", "Amina", "Hafsa", "Mariam", "Sahar"
]

class Command(BaseCommand):
    help = 'Generates 100+ complete test admission applications with Pakistani Islamic names'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of applications to generate (default: 100)'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f"Generating {count} test applications per program with Islamic names...")

        # Get or create active academic session
        session, _ = AcademicSession.objects.get_or_create(
            name="2023-2027",
            defaults={
                'start_year': 2023,
                'end_year': 2027,
                'is_active': True
            }
        )

        # Get all available programs
        programs = list(Program.objects.all())
        if not programs:
            self.stdout.write(self.style.ERROR("No programs found. Please create programs first."))
            return

        religions = ['Islam', 'Christianity', 'Hinduism', 'Sikhism', 'Buddhism']
        castes = ['Arain', 'Jutt', 'Rajput', 'Mughal', 'Sheikh', 'Syed', 'Qureshi']
        shifts = ['morning', 'evening']
        exam_types = ['Matric', 'Intermediate', 'Bachelor']
        boards = ['FBISE', 'BISE Lahore', 'BISE Multan', 'BISE Gujranwala', 'Aga Khan Board']
        activities = ['Sports', 'Debate', 'Music', 'Art', 'Science Club', 'Programming']

        total_created = 0
        for program in programs:
            for i in range(count):
                try:
                    # Choose gender randomly
                    gender = random.choice(['male', 'female'])
                    if gender == 'male':
                        first_name = random.choice(islamic_male_names)
                    else:
                        first_name = random.choice(islamic_female_names)
                    last_name = fake.last_name()

                    # Create user account with email as username
                    email = fake.email()
                    user = get_user_model().objects.create_user(
                        email=email,
                        password='0000pppp',
                        first_name=first_name,
                        last_name=last_name
                    )

                    shift = random.choice(shifts)

                    # Create applicant
                    dob = fake.date_of_birth(minimum_age=16, maximum_age=25)
                    full_name = f"{first_name} {last_name}"
                    applicant = Applicant.objects.create(
                        user=user,
                        session=session,
                        faculty=program.department.faculty,
                        department=program.department,
                        program=program,
                        status='pending',
                        full_name=full_name,

                        religion='Islam',
                        caste=random.choice(castes),
                        cnic=fake.unique.bothify('#####-#######-#'),
                        dob=dob,

                        father_name=random.choice(islamic_male_names) + " " + last_name,
                        father_occupation=fake.job(),
                        monthly_income=random.randint(20000, 200000),
                        relationship='father',
                        permanent_address=fake.address(),
                        shift=shift,
                        declaration=True
                    )

                    # Add academic qualifications
                    for exam in exam_types:
                        passing_year = 2023 - random.randint(2, 5)
                        marks = random.randint(600, 1050)
                        total = 1100
                        
                        AcademicQualification.objects.create(
                            applicant=applicant,
                            exam_passed=exam,
                            passing_year=passing_year,
                            marks_obtained=marks,
                            total_marks=total,
                            division=self.get_division(marks/total),
                            subjects=self.get_subjects(exam),
                            board=random.choice(boards)
                        )

                    # Add extracurricular activities
                    for _ in range(random.randint(1, 3)):
                        activity = random.choice(activities)
                        ExtraCurricularActivity.objects.create(
                            applicant=applicant,
                            activity=activity,
                            position=random.choice(['Member', 'Captain', 'President']),
                            achievement=f"Won {random.choice(['1st', '2nd', '3rd'])} prize",
                            activity_year=2023 - random.randint(1, 3)
                        )

                    total_created += 1
                    self.stdout.write(f"Created application #{total_created}: {applicant.full_name} for program {program.name}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating application: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {total_created} test applications"))


    def get_division(self, percentage):
        if percentage >= 0.8:
            return '1st Division'
        elif percentage >= 0.6:
            return '2nd Division'
        else:
            return '3rd Division'

    def generate_valid_phone_number(self):
        """Generate a properly formatted Pakistani mobile number (03XX-XXXXXXX)"""
        return f"03{fake.random_int(min=10, max=99)}-{fake.random_int(min=1000000, max=9999999)}"

    def get_subjects(self, exam_type):

        if exam_type == 'Matric':
            return "English, Urdu, Math, Physics, Chemistry"
        elif exam_type == 'Intermediate':
            return "English, Urdu, Math, Physics, Chemistry, Computer Science"
        else:
            return "Major subjects according to degree program"
