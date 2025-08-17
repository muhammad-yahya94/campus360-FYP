import random
import string
from datetime import datetime, timedelta
from faker import Faker
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus360FYP.settings")
django.setup()

from academics.models import Faculty, Department, Program, Semester
from admissions.models import Applicant, AcademicQualification, AdmissionCycle ,AcademicSession
from payment.models import Payment
from users.models import CustomUser
import multiprocessing
from multiprocessing import Pool
import uuid
import re
import os
import django

# Initialize Faker with a seed for reproducibility
fake = Faker('en_US')
Faker.seed(4321)

# Pakistani-specific data
PAKISTANI_MALE_NAMES = [
    'Ahmed Khan', 'Muhammad Ali', 'Hassan Raza', 'Usman Malik', 'Bilal Ahmed',
    'Farhan Qureshi', 'Zain Iqbal', 'Asad Mehmood', 'Hamza Siddiqui', 'Omar Khan'
]
PAKISTANI_FEMALE_NAMES = [
    'Ayesha Khan', 'Fatima Ali', 'Sana Malik', 'Zara Ahmed', 'Maryam Raza',
    'Hina Qureshi', 'Amna Iqbal', 'Sadia Mehmood', 'Rabia Siddiqui', 'Khadija Khan'
]
PAKISTANI_SURNAMES = ['Khan', 'Malik', 'Ahmed', 'Ali', 'Raza', 'Qureshi', 'Iqbal', 'Mehmood', 'Siddiqui']
PAKISTANI_RELIGIONS = ['Islam', 'Christianity', 'Hinduism']
PAKISTANI_CASTES = ['Rajput', 'Jutt', 'Arain', 'Malik', 'Sheikh', '']

def generate_unique_cnic(existing_cnics, lock):
    """Generate a unique 13-digit CNIC number with locking."""
    while True:
        cnic = ''.join(random.choices(string.digits, k=13))
        with lock:
            if cnic not in existing_cnics:
                existing_cnics.append(cnic)
                return cnic

def generate_unique_email(full_name, existing_emails, lock):
    """Generate a unique email based on the full name with locking."""
    while True:
        base_email = (
            re.sub(r'[^a-zA-Z0-9]', '', full_name.lower().replace(' ', '.')) +
            str(random.randint(100, 999)) + '@example.com'
        )
        with lock:
            if base_email not in existing_emails:
                existing_emails.append(base_email)
                return base_email

def generate_unique_username(full_name, existing_usernames, lock):
    """Generate a unique username based on the full name with locking."""
    while True:
        base_username = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower().replace(' ', '')) + str(random.randint(100, 999))
        with lock:
            if base_username not in existing_usernames:
                existing_usernames.append(base_username)
                return base_username

def create_applicant_data(program_id, session_id, num_applicants, existing_cnics, existing_emails, existing_usernames, cnic_lock, email_lock, username_lock):
    """Generate fake applicant data for a specific program."""
    applicants_data = []
    program = Program.objects.get(id=program_id)
    session = AcademicSession.objects.get(id=session_id)
    department = program.department
    faculty = department.faculty
    degree_type = program.degree_type.lower()

    # Determine required qualifications based on degree type
    if degree_type == 'bs':
        qualifications = [
            {'exam': 'Matriculation', 'max_marks': 1100, 'marks_range': (600, 1000)},
            {'exam': 'Intermediate', 'max_marks': 1100, 'marks_range': (600, 1000)}
        ]
    elif degree_type in ['mphil', 'ms']:
        qualifications = [
            {'exam': 'Matriculation', 'max_marks': 1100, 'marks_range': (600, 1000)},
            {'exam': 'Intermediate', 'max_marks': 1100, 'marks_range': (600, 1000)},
            {'exam': 'Bachelor', 'max_marks': 100, 'marks_range': (60, 95)}
        ]
    elif degree_type == 'phd':
        qualifications = [
            {'exam': 'Matriculation', 'max_marks': 1100, 'marks_range': (600, 1000)},
            {'exam': 'Intermediate', 'max_marks': 1100, 'marks_range': (600, 1000)},
            {'exam': 'Bachelor', 'max_marks': 100, 'marks_range': (60, 95)},
            {'exam': random.choice(['MS', 'MPhil']), 'max_marks': 100, 'marks_range': (70, 90)}
        ]
    else:
        qualifications = []

    for _ in range(num_applicants):
        # Randomly select gender and name
        gender = random.choice(['male', 'female'])
        full_name = random.choice(PAKISTANI_MALE_NAMES if gender == 'male' else PAKISTANI_FEMALE_NAMES)
        
        # Generate unique identifiers
        cnic = generate_unique_cnic(existing_cnics, cnic_lock)
        email = generate_unique_email(full_name, existing_emails, email_lock)
        
        # Split full name into first and last names
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create user
        user_data = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': 'Test@1234'
        }
        
        # Applicant details
        applicant_data = {
            'full_name': full_name,
            'cnic': cnic,
            'dob': fake.date_of_birth(minimum_age=18, maximum_age=30),
            'contact_no': '03' + ''.join(random.choices(string.digits, k=9)),
            'religion': random.choice(PAKISTANI_RELIGIONS),
            'caste': random.choice(PAKISTANI_CASTES),
            'identification_mark': random.choice(['Scar on left arm', 'Mole on cheek', '']),
            'father_name': random.choice(PAKISTANI_MALE_NAMES),
            'father_occupation': random.choice(['Teacher', 'Doctor', 'Businessman', 'Engineer']),
            'father_cnic': generate_unique_cnic(existing_cnics, cnic_lock),
            'monthly_income': random.randint(30000, 150000),
            'relationship': random.choice(['father', 'guardian']),
            'permanent_address': fake.address().replace('\n', ', '),
            'shift': random.choice(['morning', 'evening']),
            'declaration': True,
            'status': 'pending',
            'faculty_id': faculty.id,
            'department_id': department.id,
            'program_id': program.id,
            'session_id': session.id
        }
        
        # Academic qualifications
        qual_data = []
        current_year = 2025
        for idx, qual in enumerate(qualifications):
            passing_year = current_year - (len(qualifications) - idx - 1) * 2
            if passing_year < 2022 and qual['exam'] in ['Bachelor', 'MS', 'MPhil']:
                passing_year = random.randint(2022, 2025)
            marks = random.randint(qual['marks_range'][0], qual['marks_range'][1])
            qual_data.append({
                'exam_passed': qual['exam'],
                'passing_year': passing_year,
                'marks_obtained': marks,
                'total_marks': qual['max_marks'],
                'division': random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                'subjects': random.choice(['Science, Math, English', 'Physics, Chemistry, Biology']),
                'board': random.choice(['BISE Lahore', 'BISE Karachi', 'Aga Khan Board'])
            })
        
        applicants_data.append({
            'user_data': user_data,
            'applicant_data': applicant_data,
            'qualifications': qual_data
        })
    
    return applicants_data

def save_applicant(applicant_data):
    """Save a single applicant's data with transaction to ensure data integrity."""
    with transaction.atomic():
        try:
            # Create CustomUser
            user = CustomUser.objects.create_user(
                email=applicant_data['user_data']['email'],
                first_name=applicant_data['user_data']['first_name'],
                last_name=applicant_data['user_data']['last_name'],
                password=applicant_data['user_data']['password']
            )
            
            # Create Applicant
            applicant_data_dict = applicant_data['applicant_data']
            qualifications = applicant_data['qualifications']

            applicant = Applicant.objects.create(
                user=user,
                session_id=applicant_data_dict['session_id'],
                faculty_id=applicant_data_dict['faculty_id'],
                department_id=applicant_data_dict['department_id'],
                program_id=applicant_data_dict['program_id'],
                status=applicant_data_dict['status'],
                applicant_photo='photos/dummy.jpg',
                full_name=applicant_data_dict['full_name'],
                religion=applicant_data_dict['religion'],
                caste=applicant_data_dict['caste'],
                cnic=applicant_data_dict['cnic'],
                dob=applicant_data_dict['dob'],
                contact_no=applicant_data_dict['contact_no'],
                identification_mark=applicant_data_dict['identification_mark'],
                father_name=applicant_data_dict['father_name'],
                father_occupation=applicant_data_dict['father_occupation'],
                father_cnic=applicant_data_dict['father_cnic'],
                monthly_income=applicant_data_dict['monthly_income'],
                relationship=applicant_data_dict['relationship'],
                permanent_address=applicant_data_dict['permanent_address'],
                shift=applicant_data_dict['shift'],
                declaration=applicant_data_dict['declaration'],
                rejection_reason=''
            )
            
            # Create Academic Qualifications
            for qual in qualifications:
                AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=qual['exam_passed'],
                    passing_year=qual['passing_year'],
                    marks_obtained=qual['marks_obtained'],
                    total_marks=qual['total_marks'],
                    division=qual['division'],
                    subjects=qual['subjects'],
                    board=qual['board']
                )
            
            # Create Payment (marked as paid)
            Payment.objects.create(
                user=applicant,
                stripe_session_id=str(uuid.uuid4()),
                stripe_payment_intent=str(uuid.uuid4()),
                amount=5000.00,
                status='paid'
            )
            
        except Exception as e:
            print(f"Error saving applicant {applicant_data['applicant_data']['full_name']}: {e}")
            raise

def setup_initial_data():
    """Create a sample Faculty, Department, and Program if none exist."""
    with transaction.atomic():
        if not Faculty.objects.exists():
            faculty = Faculty.objects.create(
                name="Faculty of Engineering",
                slug="faculty-of-engineering",
                description="Engineering Faculty"
            )
        else:
            faculty = Faculty.objects.first()
        
        if not Department.objects.exists():
            department = Department.objects.create(
                faculty=faculty,
                name="Department of Computer Science",
                slug="computer-science",
                code="CS",
                introduction="Intro to CS",
                details="Details about CS department"
            )
        else:
            department = Department.objects.first()
        
        if not Program.objects.exists():
            Program.objects.create(
                department=department,
                name="Bachelor of Science in Computer Science",
                degree_type="BS",
                duration_years=4,
                total_semesters=8,
                start_year=2020,
                is_active=True
            )
            Program.objects.create(
                department=department,
                name="Master of Science in Computer Science",
                degree_type="MS",
                duration_years=2,
                total_semesters=4,
                start_year=2020,
                is_active=True
            )
            Program.objects.create(
                department=department,
                name="PhD in Computer Science",
                degree_type="PhD",
                duration_years=3,
                total_semesters=6,
                start_year=2020,
                is_active=True
            )

def generate_fake_data():
    """Main function to generate fake data using multiprocessing."""
    # Get all programs
    programs = list(Program.objects.all())
    if not programs:
        print("No programs found. Please create programs first.")
        return
    
    # Initialize sets for unique fields
    manager = multiprocessing.Manager()
    existing_cnics = manager.list()
    existing_emails = manager.list()
    existing_usernames = manager.list()
    cnic_lock = manager.Lock()
    email_lock = manager.Lock()
    username_lock = manager.Lock()
    
    # Prepare tasks for multiprocessing
    tasks = []
    total_applicants = 50
    num_programs = len(programs)
    applicants_per_program = max(1, total_applicants // num_programs)
    remaining = total_applicants % num_programs
    start_year = 2024
    
    for i, program in enumerate(programs):
        # Distribute remaining applicants among first few programs
        current_program_applicants = applicants_per_program + (1 if i < remaining else 0)
        if current_program_applicants <= 0:
            continue
            
        # Create AcademicSession based on program duration
        end_year = start_year + program.duration_years
        session_name = f"{start_year}-{end_year}"
        session, _ = AcademicSession.objects.get_or_create(
            name=session_name,
            start_year=start_year,
            end_year=end_year,
            is_active=True
        )
        
        # Ensure AdmissionCycle exists for the program
        AdmissionCycle.objects.get_or_create(
            program=program,
            session=session,
            application_start=timezone.now() - timedelta(days=30),
            application_end=timezone.now() + timedelta(days=30),
            is_open=True
        )
        tasks.append((program.id, session.id, current_program_applicants, existing_cnics, existing_emails, existing_usernames, cnic_lock, email_lock, username_lock))
    
    # Use multiprocessing to generate data
    with Pool(processes=min(multiprocessing.cpu_count(), len(tasks))) as pool:
        results = pool.starmap(create_applicant_data, tasks)
    
    # Flatten results and save applicants
    total_created = 0
    for applicants_data in results:
        for applicant_data in applicants_data:
            save_applicant(applicant_data)
            total_created += 1
    
    print(f"Generated {total_created} applicants across {len(programs)} programs.")

if __name__ == '__main__':

    setup_initial_data()
    generate_fake_data()
