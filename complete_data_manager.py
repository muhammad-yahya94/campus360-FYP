#!/usr/bin/env python3
"""
Complete Data Management Utility for Campus360 University System
================================================================

This comprehensive utility provides:
- Complete data generation for all models
- Safe data deletion with proper foreign key handling
- Data export/import functionality
- Interactive menu system
- Progress tracking and logging
- Data validation and integrity checks

Usage: python complete_data_manager.py
"""

import os
import sys
import django
import json
import random
import string
import uuid
import time
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import all models
from django.db import transaction, connection
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from faker import Faker

# User and Authentication
from users.models import CustomUser

# Academic Structure
from academics.models import Faculty, Department, Program, Semester

# Admissions
from admissions.models import (
    AcademicSession, AdmissionCycle, Applicant, 
    AcademicQualification, ExtraCurricularActivity
)

# Faculty and Staff
from faculty_staff.models import Teacher, TeacherDetails, Office, OfficeStaff

# Courses and Academic Content
from courses.models import (
    Course, CourseOffering, Venue, TimetableSlot, LectureReplacement,
    StudyMaterial, Assignment, AssignmentSubmission, Notice, 
    ExamResult, Attendance, Quiz, Question, Option, QuizSubmission
)

# Students
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment

# Fee Management (if exists)
try:
    from fee_management.models import SemesterFee, FeeVoucher
    FEE_MANAGEMENT_AVAILABLE = True
except ImportError:
    FEE_MANAGEMENT_AVAILABLE = False

# Initialize Faker
fake = Faker()

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================

class Config:
    """Configuration settings for data generation"""
    
    # Quantities for data generation
    NUM_FACULTIES = 3
    NUM_DEPARTMENTS_PER_FACULTY = 3
    NUM_PROGRAMS_PER_DEPARTMENT = 2
    NUM_SESSIONS = 3
    NUM_SEMESTERS_PER_PROGRAM = 8  # For BS programs
    
    # Staff and Faculty
    NUM_TEACHERS_PER_DEPARTMENT = 5
    NUM_OFFICES = 5
    NUM_OFFICE_STAFF_PER_OFFICE = 2
    
    # Courses and Academic Content
    NUM_COURSES_PER_DEPARTMENT = 8
    NUM_VENUES_PER_DEPARTMENT = 3
    NUM_ASSIGNMENTS_PER_COURSE = 3
    NUM_STUDY_MATERIALS_PER_COURSE = 5
    NUM_NOTICES = 10
    
    # Students and Enrollments
    NUM_STUDENTS_PER_PROGRAM = 20
    NUM_ATTENDANCE_RECORDS_PER_STUDENT = 15
    
    # Quizzes
    NUM_QUIZZES_PER_COURSE = 2
    NUM_QUESTIONS_PER_QUIZ = 5
    NUM_OPTIONS_PER_QUESTION = 4
    
    # File paths
    BACKUP_DIR = Path("data_backups")
    LOG_FILE = "data_manager.log"
    
    # University-specific data
    UNIVERSITY_NAME = "Campus360 University"
    UNIVERSITY_DOMAINS = ["campus360.edu.pk", "student.campus360.edu.pk", "faculty.campus360.edu.pk"]
    
    # Pakistani names and data
    PAKISTANI_MALE_NAMES = [
        "Muhammad", "Ali", "Ahmad", "Hassan", "Hussain", "Omar", "Usman", "Bilal",
        "Hamza", "Zain", "Faisal", "Tariq", "Imran", "Shahid", "Rashid", "Kamran",
        "Asif", "Naveed", "Saeed", "Majid", "Khalid", "Fahad", "Waqar", "Umer"
    ]
    
    PAKISTANI_FEMALE_NAMES = [
        "Fatima", "Aisha", "Zainab", "Khadija", "Maryam", "Hafsa", "Ruqayyah", "Safia",
        "Amina", "Zara", "Sana", "Hina", "Nida", "Farah", "Sadia", "Rabia",
        "Noor", "Ayesha", "Samina", "Nasreen", "Shazia", "Farzana", "Rubina", "Shaista"
    ]
    
    PAKISTANI_SURNAMES = [
        "Khan", "Ahmed", "Ali", "Shah", "Malik", "Sheikh", "Qureshi", "Siddiqui",
        "Butt", "Chaudhry", "Awan", "Rajput", "Mughal", "Bhatti", "Dar", "Mir",
        "Hashmi", "Abbasi", "Ansari", "Baig", "Gilani", "Naqvi", "Rizvi", "Kazmi"
    ]
    
    PAKISTANI_CITIES = [
        "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan",
        "Peshawar", "Quetta", "Sialkot", "Gujranwala", "Hyderabad", "Bahawalpur",
        "Sargodha", "Sukkur", "Larkana", "Mardan", "Mingora", "Rahim Yar Khan"
    ]
    
    DEGREE_TYPES = ["BS", "MS", "PhD", "BBA", "MBA", "BE", "ME"]
    
    SUBJECTS_BY_FIELD = {
        "Computer Science": [
            "Programming Fundamentals", "Data Structures", "Algorithms", "Database Systems",
            "Software Engineering", "Computer Networks", "Operating Systems", "Web Development",
            "Machine Learning", "Artificial Intelligence", "Cybersecurity", "Mobile App Development"
        ],
        "Business Administration": [
            "Principles of Management", "Marketing Management", "Financial Management", "Human Resource Management",
            "Operations Management", "Strategic Management", "Business Ethics", "Entrepreneurship",
            "International Business", "Supply Chain Management", "Business Analytics", "Leadership"
        ],
        "Engineering": [
            "Engineering Mathematics", "Physics", "Chemistry", "Engineering Drawing",
            "Mechanics", "Thermodynamics", "Fluid Mechanics", "Materials Science",
            "Control Systems", "Power Systems", "Electronics", "Digital Logic Design"
        ],
        "English": [
            "English Literature", "Linguistics", "Creative Writing", "Grammar and Composition",
            "Poetry Analysis", "Drama Studies", "Novel Studies", "Research Methodology",
            "Comparative Literature", "Translation Studies", "Academic Writing", "Public Speaking"
        ]
    }

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

class ProgressTracker:
    """Track and display progress for long-running operations"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        self.current += increment
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                print(f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%) - ETA: {eta:.1f}s", end="")
            else:
                print(f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%)", end="")
    
    def finish(self):
        elapsed = time.time() - self.start_time
        print(f"\r{self.description}: {self.total}/{self.total} (100.0%) - Completed in {elapsed:.1f}s")

def generate_pakistani_name(gender: str = None) -> tuple:
    """Generate a realistic Pakistani name"""
    if gender is None:
        gender = random.choice(['male', 'female'])
    
    if gender == 'male':
        first_name = random.choice(Config.PAKISTANI_MALE_NAMES)
    else:
        first_name = random.choice(Config.PAKISTANI_FEMALE_NAMES)
    
    last_name = random.choice(Config.PAKISTANI_SURNAMES)
    return first_name, last_name

def generate_cnic() -> str:
    """Generate a realistic Pakistani CNIC number"""
    # Format: XXXXX-XXXXXXX-X
    part1 = ''.join([str(random.randint(0, 9)) for _ in range(5)])
    part2 = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    part3 = str(random.randint(0, 9))
    return f"{part1}-{part2}-{part3}"

def generate_phone_number() -> str:
    """Generate a Pakistani phone number"""
    prefixes = ['0300', '0301', '0302', '0303', '0304', '0305', '0321', '0322', '0323', '0324', '0325']
    prefix = random.choice(prefixes)
    number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix}{number}"

def generate_email(first_name: str, last_name: str, domain: str = None) -> str:
    """Generate an email address"""
    if domain is None:
        domain = random.choice(Config.UNIVERSITY_DOMAINS)
    
    username = f"{first_name.lower()}.{last_name.lower()}"
    # Add random number if needed to avoid duplicates
    if random.random() < 0.3:
        username += str(random.randint(1, 999))
    
    return f"{username}@{domain}"

def create_fake_image(filename: str = None) -> SimpleUploadedFile:
    """Create a dummy image file"""
    if filename is None:
        filename = f"fake_image_{uuid.uuid4().hex[:8]}.jpg"
    
    return SimpleUploadedFile(
        name=filename,
        content=b'fake_image_content_for_testing',
        content_type='image/jpeg'
    )

def create_fake_file(filename: str = None, extension: str = 'pdf') -> SimpleUploadedFile:
    """Create a dummy file"""
    if filename is None:
        filename = f"fake_file_{uuid.uuid4().hex[:8]}.{extension}"
    
    content_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain'
    }
    
    return SimpleUploadedFile(
        name=filename,
        content=b'fake_file_content_for_testing',
        content_type=content_types.get(extension, 'application/octet-stream')
    )

@contextmanager
def db_transaction():
    """Context manager for database transactions with proper error handling"""
    try:
        with transaction.atomic():
            yield
    except Exception as e:
        logger.error(f"Database transaction failed: {str(e)}")
        raise

# ============================================================================
# DATA GENERATION CLASSES
# ============================================================================

class DataGenerator:
    """Main data generation class"""
    
    def __init__(self):
        self.created_objects = {
            'users': [],
            'faculties': [],
            'departments': [],
            'programs': [],
            'sessions': [],
            'semesters': [],
            'teachers': [],
            'offices': [],
            'office_staff': [],
            'courses': [],
            'venues': [],
            'course_offerings': [],
            'students': [],
            'applicants': [],
        }
    
    def generate_all_data(self):
        """Generate all data in proper order"""
        logger.info("Starting comprehensive data generation for university system...")
        start_time = time.time()
        
        try:
            with db_transaction():
                # Core academic structure
                self.generate_academic_sessions()
                self.generate_faculties_and_departments()
                self.generate_programs()
                self.generate_semesters()
                
                # Users and staff
                self.generate_admin_users()
                self.generate_offices()
                self.generate_teachers()
                self.generate_office_staff()
                
                # Courses and academic content
                self.generate_courses()
                self.generate_venues()
                self.generate_course_offerings()
                self.generate_timetable_slots()
                
                # Students and admissions
                self.generate_applicants_and_students()
                self.generate_enrollments()
                
                # Academic records and content
                self.generate_assignments()
                self.generate_study_materials()
                self.generate_attendance()
                self.generate_exam_results()
                self.generate_notices()
                self.generate_quizzes()
                
                # Fee management (if available)
                if FEE_MANAGEMENT_AVAILABLE:
                    self.generate_fee_data()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Data generation completed successfully in {elapsed_time:.2f} seconds")
            self.print_generation_summary()
            
        except Exception as e:
            logger.error(f"Data generation failed: {str(e)}")
            raise
    
    def generate_academic_sessions(self):
        """Generate academic sessions"""
        logger.info("Generating academic sessions...")
        current_year = datetime.now().year
        
        sessions_data = [
            (f"{current_year-2}-{current_year+2}", current_year-2, current_year+2, False),
            (f"{current_year-1}-{current_year+3}", current_year-1, current_year+3, False),
            (f"{current_year}-{current_year+4}", current_year, current_year+4, True),  # Active session
        ]
        
        for name, start_year, end_year, is_active in sessions_data:
            session, created = AcademicSession.objects.get_or_create(
                name=name,
                defaults={
                    'start_year': start_year,
                    'end_year': end_year,
                    'is_active': is_active,
                    'description': f"Academic session spanning {start_year} to {end_year}"
                }
            )
            if created:
                self.created_objects['sessions'].append(session)
                logger.info(f"Created session: {session.name}")
    
    def generate_faculties_and_departments(self):
        """Generate faculties and departments"""
        logger.info("Generating faculties and departments...")
        
        faculties_data = [
            {
                'name': 'Faculty of Computer Science & Information Technology',
                'slug': 'faculty-cs-it',
                'description': 'Leading faculty in computer science and information technology education',
                'departments': [
                    {'name': 'Department of Computer Science', 'code': 'CS', 'field': 'Computer Science'},
                    {'name': 'Department of Software Engineering', 'code': 'SE', 'field': 'Computer Science'},
                    {'name': 'Department of Information Technology', 'code': 'IT', 'field': 'Computer Science'},
                ]
            },
            {
                'name': 'Faculty of Business Administration',
                'slug': 'faculty-business',
                'description': 'Excellence in business education and management studies',
                'departments': [
                    {'name': 'Department of Business Administration', 'code': 'BBA', 'field': 'Business Administration'},
                    {'name': 'Department of Commerce', 'code': 'COM', 'field': 'Business Administration'},
                    {'name': 'Department of Economics', 'code': 'ECO', 'field': 'Business Administration'},
                ]
            },
            {
                'name': 'Faculty of Engineering',
                'slug': 'faculty-engineering',
                'description': 'Premier engineering education and research',
                'departments': [
                    {'name': 'Department of Electrical Engineering', 'code': 'EE', 'field': 'Engineering'},
                    {'name': 'Department of Mechanical Engineering', 'code': 'ME', 'field': 'Engineering'},
                    {'name': 'Department of Civil Engineering', 'code': 'CE', 'field': 'Engineering'},
                ]
            }
        ]
        
        for faculty_data in faculties_data:
            faculty, created = Faculty.objects.get_or_create(
                slug=faculty_data['slug'],
                defaults={
                    'name': faculty_data['name'],
                    'description': faculty_data['description']
                }
            )
            if created:
                self.created_objects['faculties'].append(faculty)
                logger.info(f"Created faculty: {faculty.name}")
            
            # Create departments
            for dept_data in faculty_data['departments']:
                dept_slug = f"dept-{dept_data['code'].lower()}"
                department, created = Department.objects.get_or_create(
                    slug=dept_slug,
                    code=dept_data['code'],
                    defaults={
                        'faculty': faculty,
                        'name': dept_data['name'],
                        'image': create_fake_image(),
                        'introduction': f"Welcome to the {dept_data['name']}",
                        'details': f"The {dept_data['name']} offers comprehensive education in {dept_data['field']}"
                    }
                )
                if created:
                    department.field = dept_data['field']  # Store for later use
                    self.created_objects['departments'].append(department)
                    logger.info(f"Created department: {department.name}")
    
    def generate_programs(self):
        """Generate academic programs"""
        logger.info("Generating academic programs...")
        
        for department in self.created_objects['departments']:
            field = getattr(department, 'field', 'General')
            
            # Generate different degree programs
            programs_data = [
                {'name': f"Bachelor of Science in {field}", 'degree_type': 'BS', 'duration': 4, 'semesters': 8},
                {'name': f"Master of Science in {field}", 'degree_type': 'MS', 'duration': 2, 'semesters': 4},
            ]
            
            for prog_data in programs_data:
                program, created = Program.objects.get_or_create(
                    name=prog_data['name'],
                    department=department,
                    defaults={
                        'degree_type': prog_data['degree_type'],
                        'duration_years': prog_data['duration'],
                        'total_semesters': prog_data['semesters'],
                        'start_year': 2020,
                        'is_active': True
                    }
                )
                if created:
                    self.created_objects['programs'].append(program)
                    logger.info(f"Created program: {program.name}")
    
    def generate_semesters(self):
        """Generate semesters for all programs and sessions"""
        logger.info("Generating semesters...")
        
        for program in self.created_objects['programs']:
            for session in self.created_objects['sessions']:
                for sem_num in range(1, program.total_semesters + 1):
                    semester, created = Semester.objects.get_or_create(
                        program=program,
                        session=session,
                        number=sem_num,
                        defaults={
                            'name': f"Semester {sem_num}",
                            'description': f"Semester {sem_num} of {program.name}",
                            'start_time': date(session.start_year, 1 if sem_num % 2 == 1 else 7, 1),
                            'end_time': date(session.start_year, 6 if sem_num % 2 == 1 else 12, 30),
                            'is_active': session.is_active and sem_num <= 2  # Only first 2 semesters active
                        }
                    )
                    if created:
                        self.created_objects['semesters'].append(semester)
    
    def generate_admin_users(self):
        """Generate admin and system users"""
        logger.info("Generating admin users...")
        
        # Create superuser
        admin_user, created = CustomUser.objects.get_or_create(
            email='admin@campus360.edu.pk',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'password': make_password('admin123')
            }
        )
        if created:
            self.created_objects['users'].append(admin_user)
            logger.info("Created admin user: admin@campus360.edu.pk")
    
    def generate_offices(self):
        """Generate administrative offices"""
        logger.info("Generating offices...")
        
        offices_data = [
            {'name': 'Registrar Office', 'location': 'Main Building, Ground Floor'},
            {'name': 'Admission Office', 'location': 'Admin Block, First Floor'},
            {'name': 'Finance Office', 'location': 'Admin Block, Ground Floor'},
            {'name': 'Student Affairs Office', 'location': 'Student Center, Second Floor'},
            {'name': 'Examination Office', 'location': 'Academic Block, First Floor'},
        ]
        
        for office_data in offices_data:
            office, created = Office.objects.get_or_create(
                name=office_data['name'],
                defaults={
                    'description': f"Administrative office handling {office_data['name'].lower()} related matters",
                    'location': office_data['location'],
                    'contact_email': f"{office_data['name'].lower().replace(' ', '.')}@campus360.edu.pk",
                    'contact_phone': generate_phone_number(),
                    'image': create_fake_image()
                }
            )
            if created:
                self.created_objects['offices'].append(office)
                logger.info(f"Created office: {office.name}")
    
    def generate_teachers(self):
        """Generate teacher profiles"""
        logger.info("Generating teachers...")
        
        progress = ProgressTracker(
            len(self.created_objects['departments']) * Config.NUM_TEACHERS_PER_DEPARTMENT,
            "Creating teachers"
        )
        
        for department in self.created_objects['departments']:
            for i in range(Config.NUM_TEACHERS_PER_DEPARTMENT):
                first_name, last_name = generate_pakistani_name()
                email = generate_email(first_name, last_name, "faculty.campus360.edu.pk")
                
                # Create user
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_staff': True,
                        'password': make_password('teacher123')
                    }
                )
                
                if created:
                    self.created_objects['users'].append(user)
                    
                    # Create teacher profile
                    designation = 'head_of_department' if i == 0 else 'professor'
                    teacher = Teacher.objects.create(
                        user=user,
                        department=department,
                        designation=designation,
                        contact_no=generate_phone_number(),
                        qualification=random.choice(['PhD', 'MS', 'M.Phil']) + f" in {getattr(department, 'field', 'General Studies')}",
                        hire_date=fake.date_between(start_date='-10y', end_date='today'),
                        is_active=True,
                        experience=fake.text(max_nb_chars=500)
                    )
                    
                    # Create teacher details
                    TeacherDetails.objects.create(
                        teacher=teacher,
                        employment_type=random.choice(['permanent', 'contract', 'visitor']),
                        salary_per_lecture=Decimal(random.randint(2000, 5000)),
                        fixed_salary=Decimal(random.randint(50000, 150000)),
                        status='available'
                    )
                    
                    self.created_objects['teachers'].append(teacher)
                
                progress.update()
        
        progress.finish()
    
    def generate_office_staff(self):
        """Generate office staff"""
        logger.info("Generating office staff...")
        
        for office in self.created_objects['offices']:
            for i in range(Config.NUM_OFFICE_STAFF_PER_OFFICE):
                first_name, last_name = generate_pakistani_name()
                email = generate_email(first_name, last_name, "staff.campus360.edu.pk")
                
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_staff': True,
                        'password': make_password('staff123')
                    }
                )
                
                if created:
                    self.created_objects['users'].append(user)
                    
                    positions = ['Assistant', 'Officer', 'Clerk', 'Manager', 'Coordinator']
                    OfficeStaff.objects.create(
                        user=user,
                        office=office,
                        position=random.choice(positions),
                        contact_no=generate_phone_number()
                    )
    
    def generate_courses(self):
        """Generate courses for each department"""
        logger.info("Generating courses...")
        
        progress = ProgressTracker(
            len(self.created_objects['departments']) * Config.NUM_COURSES_PER_DEPARTMENT,
            "Creating courses"
        )
        
        for department in self.created_objects['departments']:
            field = getattr(department, 'field', 'General')
            subjects = Config.SUBJECTS_BY_FIELD.get(field, ['General Subject'])
            
            for i in range(Config.NUM_COURSES_PER_DEPARTMENT):
                course_code = f"{department.code}{100 + i + 1}"
                subject = random.choice(subjects)
                
                course, created = Course.objects.get_or_create(
                    code=course_code,
                    defaults={
                        'name': subject,
                        'credits': random.choice([2, 3, 4]),
                        'lab_work': random.choice([0, 1, 2]),
                        'is_active': True,
                        'description': f"Comprehensive course covering {subject.lower()}",
                        'opt': random.choice([True, False])
                    }
                )
                
                if created:
                    self.created_objects['courses'].append(course)
                
                progress.update()
        
        progress.finish()
    
    def generate_venues(self):
        """Generate venues for each department"""
        logger.info("Generating venues...")
        
        for department in self.created_objects['departments']:
            for i in range(Config.NUM_VENUES_PER_DEPARTMENT):
                venue_types = ['Room', 'Lab', 'Hall', 'Auditorium']
                venue_type = random.choice(venue_types)
                
                Venue.objects.get_or_create(
                    name=f"{department.code}-{venue_type}-{i+1}",
                    department=department,
                    defaults={
                        'capacity': random.randint(30, 100),
                        'is_active': True
                    }
                )
    
    def generate_course_offerings(self):
        """Generate course offerings"""
        logger.info("Generating course offerings...")
        
        active_session = AcademicSession.objects.filter(is_active=True).first()
        if not active_session:
            logger.warning("No active session found for course offerings")
            return
        
        progress = ProgressTracker(
            len(self.created_objects['semesters']),
            "Creating course offerings"
        )
        
        for semester in self.created_objects['semesters']:
            if not semester.is_active:
                progress.update()
                continue
            
            # Get courses from the same department
            dept_courses = [c for c in self.created_objects['courses'] 
                          if c.code.startswith(semester.program.department.code)]
            
            # Get teachers from the same department
            dept_teachers = [t for t in self.created_objects['teachers'] 
                           if t.department == semester.program.department]
            
            if not dept_teachers:
                progress.update()
                continue
            
            # Create 4-6 course offerings per semester
            selected_courses = random.sample(dept_courses, min(6, len(dept_courses)))
            
            for course in selected_courses:
                teacher = random.choice(dept_teachers)
                
                offering, created = CourseOffering.objects.get_or_create(
                    course=course,
                    teacher=teacher,
                    semester=semester,
                    academic_session=active_session,
                    defaults={
                        'department': semester.program.department,
                        'program': semester.program,
                        'is_active': True,
                        'current_enrollment': 0,
                        'shift': random.choice(['morning', 'evening']),
                        'offering_type': random.choice(['core', 'elective', 'major'])
                    }
                )
                
                if created:
                    self.created_objects['course_offerings'].append(offering)
            
            progress.update()
        
        progress.finish()
    
    def generate_timetable_slots(self):
        """Generate timetable slots for course offerings"""
        logger.info("Generating timetable slots...")
        
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        time_slots = [
            ('08:00:00', '09:00:00'),
            ('09:00:00', '10:00:00'),
            ('10:00:00', '11:00:00'),
            ('11:00:00', '12:00:00'),
            ('14:00:00', '15:00:00'),
            ('15:00:00', '16:00:00'),
            ('16:00:00', '17:00:00'),
        ]
        
        for offering in self.created_objects['course_offerings']:
            # Get venues from the same department
            dept_venues = Venue.objects.filter(department=offering.department)
            if not dept_venues.exists():
                continue
            
            # Create 1-2 time slots per offering
            for _ in range(random.randint(1, 2)):
                day = random.choice(days)
                start_time, end_time = random.choice(time_slots)
                venue = random.choice(dept_venues)
                
                try:
                    TimetableSlot.objects.get_or_create(
                        course_offering=offering,
                        day=day,
                        start_time=start_time,
                        venue=venue,
                        defaults={
                            'end_time': end_time
                        }
                    )
                except Exception as e:
                    # Skip if there's a conflict
                    continue
    
    def generate_applicants_and_students(self):
        """Generate applicants and students"""
        logger.info("Generating applicants and students...")
        
        active_session = AcademicSession.objects.filter(is_active=True).first()
        if not active_session:
            logger.warning("No active session found")
            return
        
        progress = ProgressTracker(
            len(self.created_objects['programs']) * Config.NUM_STUDENTS_PER_PROGRAM,
            "Creating students"
        )
        
        for program in self.created_objects['programs']:
            for i in range(Config.NUM_STUDENTS_PER_PROGRAM):
                # Generate student data
                gender = random.choice(['male', 'female'])
                first_name, last_name = generate_pakistani_name(gender)
                email = generate_email(first_name, last_name, "student.campus360.edu.pk")
                
                # Create user
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'password': make_password('student123')
                    }
                )
                
                if created:
                    self.created_objects['users'].append(user)
                    
                    # Create applicant
                    applicant = Applicant.objects.create(
                        user=user,
                        session=active_session,
                        faculty=program.department.faculty,
                        department=program.department,
                        program=program,
                        status='accepted',
                        full_name=f"{first_name} {last_name}",
                        religion='Islam',
                        cnic=generate_cnic(),
                        dob=fake.date_of_birth(minimum_age=18, maximum_age=25),
                        contact_no=generate_phone_number(),
                        father_name=fake.name_male(),
                        father_occupation=fake.job(),
                        monthly_income=random.randint(20000, 100000),
                        relationship='father',
                        permanent_address=f"{fake.address()}, {random.choice(Config.PAKISTANI_CITIES)}",
                        shift=random.choice(['morning', 'evening']),
                        declaration=True,
                        applicant_photo=create_fake_image()
                    )
                    
                    # Create student
                    student = Student.objects.create(
                        applicant=applicant,
                        user=user,
                        program=program,
                        university_roll_no=fake.unique.random_number(digits=8, fix_len=True),
                        college_roll_no=fake.unique.random_number(digits=6, fix_len=True),
                        enrollment_date=date(active_session.start_year, 1, 15),
                        current_status='active',
                        emergency_contact=fake.name(),
                        emergency_phone=generate_phone_number()
                    )
                    
                    self.created_objects['applicants'].append(applicant)
                    self.created_objects['students'].append(student)
                    
                    # Create academic qualifications
                    self.create_academic_qualifications(applicant)
                
                progress.update()
        
        progress.finish()
    
    def create_academic_qualifications(self, applicant):
        """Create academic qualifications for an applicant"""
        qualifications = [
            {
                'exam_passed': 'Matriculation',
                'passing_year': random.randint(2015, 2019),
                'marks_obtained': random.randint(800, 1050),
                'total_marks': 1100,
                'division': random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                'board': random.choice(['BISE Lahore', 'BISE Karachi', 'BISE Rawalpindi', 'FBISE'])
            },
            {
                'exam_passed': 'Intermediate',
                'passing_year': random.randint(2017, 2021),
                'marks_obtained': random.randint(700, 1000),
                'total_marks': 1100,
                'division': random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                'board': random.choice(['BISE Lahore', 'BISE Karachi', 'BISE Rawalpindi', 'FBISE'])
            }
        ]
        
        for qual_data in qualifications:
            AcademicQualification.objects.create(
                applicant=applicant,
                **qual_data,
                certificate_file=create_fake_file(extension='pdf')
            )
    
    def generate_enrollments(self):
        """Generate semester and course enrollments"""
        logger.info("Generating enrollments...")
        
        progress = ProgressTracker(len(self.created_objects['students']), "Creating enrollments")
        
        for student in self.created_objects['students']:
            # Get active semesters for student's program
            active_semesters = Semester.objects.filter(
                program=student.program,
                session__is_active=True,
                is_active=True
            ).order_by('number')
            
            for semester in active_semesters[:2]:  # Enroll in first 2 semesters
                # Create semester enrollment
                sem_enrollment, created = StudentSemesterEnrollment.objects.get_or_create(
                    student=student,
                    semester=semester,
                    defaults={'status': 'enrolled'}
                )
                
                if created:
                    # Get course offerings for this semester
                    course_offerings = CourseOffering.objects.filter(
                        semester=semester,
                        is_active=True
                    )[:5]  # Enroll in up to 5 courses
                    
                    for offering in course_offerings:
                        CourseEnrollment.objects.get_or_create(
                            student_semester_enrollment=sem_enrollment,
                            course_offering=offering,
                            defaults={'status': 'enrolled'}
                        )
                        
                        # Update enrollment count
                        offering.current_enrollment += 1
                        offering.save()
            
            progress.update()
        
        progress.finish()
    
    def generate_assignments(self):
        """Generate assignments for course offerings"""
        logger.info("Generating assignments...")
        
        progress = ProgressTracker(
            len(self.created_objects['course_offerings']) * Config.NUM_ASSIGNMENTS_PER_COURSE,
            "Creating assignments"
        )
        
        for offering in self.created_objects['course_offerings']:
            for i in range(Config.NUM_ASSIGNMENTS_PER_COURSE):
                assignment = Assignment.objects.create(
                    course_offering=offering,
                    teacher=offering.teacher,
                    title=f"Assignment {i+1}: {fake.catch_phrase()}",
                    description=fake.text(max_nb_chars=500),
                    due_date=timezone.now() + timedelta(days=random.randint(7, 30)),
                    max_points=random.choice([50, 75, 100]),
                    resource_file=create_fake_file(extension='pdf')
                )
                
                # Create submissions for some students
                enrolled_students = Student.objects.filter(
                    semester_enrollments__course_enrollments__course_offering=offering
                )
                
                for student in enrolled_students:
                    if random.random() < 0.8:  # 80% submission rate
                        AssignmentSubmission.objects.create(
                            assignment=assignment,
                            student=student,
                            content=fake.text(max_nb_chars=1000),
                            file=create_fake_file(extension='pdf'),
                            marks_obtained=random.randint(30, assignment.max_points),
                            feedback=fake.sentence(),
                            graded_by=offering.teacher
                        )
                
                progress.update()
        
        progress.finish()
    
    def generate_study_materials(self):
        """Generate study materials"""
        logger.info("Generating study materials...")
        
        progress = ProgressTracker(
            len(self.created_objects['course_offerings']) * Config.NUM_STUDY_MATERIALS_PER_COURSE,
            "Creating study materials"
        )
        
        for offering in self.created_objects['course_offerings']:
            for i in range(Config.NUM_STUDY_MATERIALS_PER_COURSE):
                StudyMaterial.objects.create(
                    course_offering=offering,
                    teacher=offering.teacher,
                    topic=f"Topic {i+1}: {fake.word().title()}",
                    title=fake.sentence(nb_words=4),
                    description=fake.text(max_nb_chars=500),
                    useful_links="\n".join([fake.url() for _ in range(3)]),
                    video_link=fake.url(),
                    image=create_fake_image()
                )
                progress.update()
        
        progress.finish()
    
    def generate_attendance(self):
        """Generate attendance records"""
        logger.info("Generating attendance records...")
        
        # Get all course enrollments
        enrollments = CourseEnrollment.objects.filter(status='enrolled')
        total_records = len(enrollments) * Config.NUM_ATTENDANCE_RECORDS_PER_STUDENT
        
        progress = ProgressTracker(total_records, "Creating attendance records")
        
        for enrollment in enrollments:
            student = enrollment.student_semester_enrollment.student
            offering = enrollment.course_offering
            
            # Generate attendance for the last 30 days
            for i in range(Config.NUM_ATTENDANCE_RECORDS_PER_STUDENT):
                attendance_date = timezone.now().date() - timedelta(days=i)
                
                # Skip weekends
                if attendance_date.weekday() >= 5:
                    progress.update()
                    continue
                
                Attendance.objects.get_or_create(
                    student=student,
                    course_offering=offering,
                    date=attendance_date,
                    defaults={
                        'status': random.choices(
                            ['present', 'absent', 'leave'],
                            weights=[80, 15, 5]
                        )[0],
                        'shift': offering.shift if offering.shift != 'both' else random.choice(['morning', 'evening']),
                        'recorded_by': offering.teacher
                    }
                )
                progress.update()
        
        progress.finish()
    
    def generate_exam_results(self):
        """Generate exam results"""
        logger.info("Generating exam results...")
        
        enrollments = CourseEnrollment.objects.filter(status='enrolled')
        progress = ProgressTracker(len(enrollments), "Creating exam results")
        
        for enrollment in enrollments:
            student = enrollment.student_semester_enrollment.student
            offering = enrollment.course_offering
            
            ExamResult.objects.get_or_create(
                course_offering=offering,
                student=student,
                defaults={
                    'midterm_obtained': random.randint(15, 25),
                    'final_obtained': random.randint(30, 50),
                    'sessional_obtained': random.randint(10, 25),
                    'practical_obtained': random.randint(0, 15) if offering.course.lab_work > 0 else 0,
                    'graded_by': offering.teacher,
                    'remarks': fake.sentence()
                }
            )
            progress.update()
        
        progress.finish()
    
    def generate_notices(self):
        """Generate notices"""
        logger.info("Generating notices...")
        
        teachers = Teacher.objects.all()[:5]  # Use first 5 teachers
        programs = Program.objects.all()[:3]  # Use first 3 programs
        
        for i in range(Config.NUM_NOTICES):
            notice = Notice.objects.create(
                title=fake.sentence(nb_words=6),
                content=fake.text(max_nb_chars=1000),
                notice_type=random.choice(['general', 'academic', 'event', 'exam', 'holiday']),
                priority=random.choice(['high', 'medium', 'low']),
                is_pinned=random.choice([True, False]),
                is_active=True,
                valid_from=timezone.now() - timedelta(days=random.randint(0, 30)),
                valid_until=timezone.now() + timedelta(days=random.randint(30, 90)),
                created_by=random.choice(teachers) if teachers else None,
                attachment=create_fake_file(extension='pdf') if random.random() < 0.3 else None
            )
            
            # Add to some programs
            if random.random() < 0.5:
                notice.programs.add(*random.sample(list(programs), random.randint(1, len(programs))))
    
    def generate_quizzes(self):
        """Generate quizzes with questions and options"""
        logger.info("Generating quizzes...")
        
        progress = ProgressTracker(
            len(self.created_objects['course_offerings']) * Config.NUM_QUIZZES_PER_COURSE,
            "Creating quizzes"
        )
        
        for offering in self.created_objects['course_offerings']:
            for i in range(Config.NUM_QUIZZES_PER_COURSE):
                quiz = Quiz.objects.create(
                    course_offering=offering,
                    title=f"Quiz {i+1}: {fake.word().title()}",
                    publish_flag=random.choice([True, False]),
                    timer_seconds=random.choice([15, 30, 45, 60])
                )
                
                # Create questions for the quiz
                for j in range(Config.NUM_QUESTIONS_PER_QUIZ):
                    question = Question.objects.create(
                        quiz=quiz,
                        text=fake.sentence(nb_words=10) + "?",
                        marks=random.choice([1, 2, 3])
                    )
                    
                    # Create options for the question
                    correct_option_index = random.randint(0, Config.NUM_OPTIONS_PER_QUESTION - 1)
                    for k in range(Config.NUM_OPTIONS_PER_QUESTION):
                        Option.objects.create(
                            question=question,
                            text=fake.sentence(nb_words=4),
                            is_correct=(k == correct_option_index)
                        )
                
                # Create some quiz submissions
                enrolled_students = Student.objects.filter(
                    semester_enrollments__course_enrollments__course_offering=offering
                )
                
                for student in enrolled_students:
                    if random.random() < 0.6:  # 60% participation rate
                        QuizSubmission.objects.create(
                            student=student,
                            quiz=quiz,
                            score=random.randint(0, Config.NUM_QUESTIONS_PER_QUIZ * 3),
                            answers={}  # Simplified for now
                        )
                
                progress.update()
        
        progress.finish()
    
    def generate_fee_data(self):
        """Generate fee management data if available"""
        if not FEE_MANAGEMENT_AVAILABLE:
            return
        
        logger.info("Generating fee management data...")
        
        # This would be implemented based on your fee_management models
        # Placeholder for now
        pass
    
    def print_generation_summary(self):
        """Print summary of generated data"""
        logger.info("\n" + "="*60)
        logger.info("DATA GENERATION SUMMARY")
        logger.info("="*60)
        
        models_count = {
            'Users': CustomUser.objects.count(),
            'Faculties': Faculty.objects.count(),
            'Departments': Department.objects.count(),
            'Programs': Program.objects.count(),
            'Academic Sessions': AcademicSession.objects.count(),
            'Semesters': Semester.objects.count(),
            'Teachers': Teacher.objects.count(),
            'Offices': Office.objects.count(),
            'Office Staff': OfficeStaff.objects.count(),
            'Courses': Course.objects.count(),
            'Course Offerings': CourseOffering.objects.count(),
            'Venues': Venue.objects.count(),
            'Timetable Slots': TimetableSlot.objects.count(),
            'Students': Student.objects.count(),
            'Applicants': Applicant.objects.count(),
            'Semester Enrollments': StudentSemesterEnrollment.objects.count(),
            'Course Enrollments': CourseEnrollment.objects.count(),
            'Assignments': Assignment.objects.count(),
            'Assignment Submissions': AssignmentSubmission.objects.count(),
            'Study Materials': StudyMaterial.objects.count(),
            'Attendance Records': Attendance.objects.count(),
            'Exam Results': ExamResult.objects.count(),
            'Notices': Notice.objects.count(),
            'Quizzes': Quiz.objects.count(),
            'Questions': Question.objects.count(),
            'Quiz Submissions': QuizSubmission.objects.count(),
        }
        
        for model_name, count in models_count.items():
            logger.info(f"- {model_name}: {count}")
        
        logger.info("="*60)

# ============================================================================
# DATA DELETION CLASSES
# ============================================================================

class DataDeleter:
    """Handle safe data deletion with proper foreign key handling"""
    
    def __init__(self):
        # Order matters - delete in reverse dependency order
        self.deletion_order = [
            # Academic records (most dependent)
            QuizSubmission, Option, Question, Quiz,
            AssignmentSubmission, Assignment,
            ExamResult, Attendance,
            StudyMaterial, Notice,
            
            # Enrollments and relationships
            CourseEnrollment, StudentSemesterEnrollment,
            TimetableSlot, LectureReplacement,
            
            # Students and applications
            Student, AcademicQualification, ExtraCurricularActivity, Applicant,
            
            # Course structure
            CourseOffering, Course, Venue,
            
            # Staff and administration
            TeacherDetails, Teacher, OfficeStaff, Office,
            
            # Academic structure
            Semester, AdmissionCycle, Program, Department, Faculty,
            AcademicSession,
            
            # Users (least dependent)
            CustomUser,
        ]
    
    def delete_all_data(self):
        """Delete all data in proper order"""
        logger.info("Starting complete data deletion...")
        start_time = time.time()
        
        total_deleted = 0
        
        try:
            with db_transaction():
                for model in self.deletion_order:
                    count = model.objects.count()
                    if count > 0:
                        model.objects.all().delete()
                        total_deleted += count
                        logger.info(f"Deleted {count} {model.__name__} records")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Data deletion completed successfully in {elapsed_time:.2f} seconds")
            logger.info(f"Total records deleted: {total_deleted}")
            
        except Exception as e:
            logger.error(f"Data deletion failed: {str(e)}")
            raise
    
    def delete_specific_models(self, model_names: List[str]):
        """Delete data from specific models"""
        logger.info(f"Deleting data from specific models: {model_names}")
        
        # Map model names to model classes
        model_map = {model.__name__: model for model in self.deletion_order}
        
        models_to_delete = []
        for name in model_names:
            if name in model_map:
                models_to_delete.append(model_map[name])
            else:
                logger.warning(f"Model '{name}' not found")
        
        # Sort by deletion order
        models_to_delete.sort(key=lambda x: self.deletion_order.index(x))
        
        try:
            with db_transaction():
                for model in models_to_delete:
                    count = model.objects.count()
                    if count > 0:
                        model.objects.all().delete()
                        logger.info(f"Deleted {count} {model.__name__} records")
        
        except Exception as e:
            logger.error(f"Specific model deletion failed: {str(e)}")
            raise

# ============================================================================
# DATA EXPORT/IMPORT CLASSES
# ============================================================================

class DataExporter:
    """Export data to JSON files for backup"""
    
    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or Config.BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
    
    def export_all_data(self):
        """Export all data to JSON files"""
        logger.info("Starting data export...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = self.backup_dir / f"backup_{timestamp}"
        export_dir.mkdir(exist_ok=True)
        
        models_to_export = [
            CustomUser, Faculty, Department, Program, AcademicSession,
            Semester, Teacher, Office, Course, Student, Applicant
        ]
        
        for model in models_to_export:
            self.export_model_data(model, export_dir)
        
        logger.info(f"Data export completed. Files saved in: {export_dir}")
    
    def export_model_data(self, model, export_dir: Path):
        """Export data for a specific model"""
        try:
            from django.core import serializers
            
            data = serializers.serialize('json', model.objects.all())
            filename = export_dir / f"{model.__name__.lower()}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(data)
            
            logger.info(f"Exported {model.objects.count()} {model.__name__} records")
            
        except Exception as e:
            logger.error(f"Failed to export {model.__name__}: {str(e)}")

class DataImporter:
    """Import data from JSON files"""
    
    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or Config.BACKUP_DIR
    
    def import_data_from_backup(self, backup_name: str):
        """Import data from a specific backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup directory not found: {backup_path}")
            return
        
        logger.info(f"Importing data from: {backup_path}")
        
        # Import in dependency order
        import_order = [
            'customuser', 'faculty', 'department', 'program', 'academicsession',
            'semester', 'teacher', 'office', 'course', 'applicant', 'student'
        ]
        
        for model_name in import_order:
            json_file = backup_path / f"{model_name}.json"
            if json_file.exists():
                self.import_model_data(json_file)
    
    def import_model_data(self, json_file: Path):
        """Import data for a specific model from JSON file"""
        try:
            from django.core import serializers
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = f.read()
            
            objects = serializers.deserialize('json', data)
            
            with db_transaction():
                for obj in objects:
                    obj.save()
            
            logger.info(f"Imported data from: {json_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to import from {json_file}: {str(e)}")

# ============================================================================
# INTERACTIVE MENU SYSTEM
# ============================================================================

class InteractiveMenu:
    """Interactive command-line menu system"""
    
    def __init__(self):
        self.generator = DataGenerator()
        self.deleter = DataDeleter()
        self.exporter = DataExporter()
        self.importer = DataImporter()
    
    def show_main_menu(self):
        """Display main menu"""
        while True:
            print("\n" + "="*60)
            print("CAMPUS360 UNIVERSITY DATA MANAGEMENT SYSTEM")
            print("="*60)
            print("1. Generate Complete Data")
            print("2. Delete All Data")
            print("3. Delete Specific Data")
            print("4. Export Data (Backup)")
            print("5. Import Data (Restore)")
            print("6. View Data Statistics")
            print("7. Configuration Settings")
            print("0. Exit")
            print("="*60)
            
            choice = input("Enter your choice (0-7): ").strip()
            
            if choice == '1':
                self.handle_generate_data()
            elif choice == '2':
                self.handle_delete_all_data()
            elif choice == '3':
                self.handle_delete_specific_data()
            elif choice == '4':
                self.handle_export_data()
            elif choice == '5':
                self.handle_import_data()
            elif choice == '6':
                self.handle_view_statistics()
            elif choice == '7':
                self.handle_configuration()
            elif choice == '0':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def handle_generate_data(self):
        """Handle data generation"""
        print("\nDATA GENERATION")
        print("-" * 30)
        print("This will generate complete dummy data for the university system.")
        print("This includes users, academic structure, courses, students, and all related data.")
        
        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm == 'yes':
            try:
                self.generator.generate_all_data()
                print("\nData generation completed successfully!")
            except Exception as e:
                print(f"\nError during data generation: {str(e)}")
        else:
            print("Data generation cancelled.")
    
    def handle_delete_all_data(self):
        """Handle complete data deletion"""
        print("\nDATA DELETION - WARNING!")
        print("-" * 30)
        print("This will DELETE ALL DATA from the database.")
        print("This action CANNOT be undone!")
        
        confirm1 = input("Are you absolutely sure? (yes/no): ").strip().lower()
        if confirm1 == 'yes':
            confirm2 = input("Type 'DELETE ALL DATA' to confirm: ").strip()
            if confirm2 == 'DELETE ALL DATA':
                try:
                    self.deleter.delete_all_data()
                    print("\nAll data deleted successfully!")
                except Exception as e:
                    print(f"\nError during data deletion: {str(e)}")
            else:
                print("Confirmation text incorrect. Deletion cancelled.")
        else:
            print("Data deletion cancelled.")
    
    def handle_delete_specific_data(self):
        """Handle specific model data deletion"""
        print("\nSPECIFIC DATA DELETION")
        print("-" * 30)
        
        available_models = [model.__name__ for model in self.deleter.deletion_order]
        
        print("Available models:")
        for i, model_name in enumerate(available_models, 1):
            print(f"{i:2d}. {model_name}")
        
        print("\nEnter model numbers to delete (comma-separated):")
        selection = input("Models: ").strip()
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_models = [available_models[i] for i in indices if 0 <= i < len(available_models)]
            
            if selected_models:
                print(f"\nSelected models: {', '.join(selected_models)}")
                confirm = input("Proceed with deletion? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    self.deleter.delete_specific_models(selected_models)
                    print("Specific data deletion completed!")
                else:
                    print("Deletion cancelled.")
            else:
                print("No valid models selected.")
                
        except ValueError:
            print("Invalid input. Please enter valid numbers.")
    
    def handle_export_data(self):
        """Handle data export"""
        print("\nDATA EXPORT (BACKUP)")
        print("-" * 30)
        
        confirm = input("Export all data to backup files? (yes/no): ").strip().lower()
        if confirm == 'yes':
            try:
                self.exporter.export_all_data()
                print("Data export completed successfully!")
            except Exception as e:
                print(f"Error during data export: {str(e)}")
        else:
            print("Data export cancelled.")
    
    def handle_import_data(self):
        """Handle data import"""
        print("\nDATA IMPORT (RESTORE)")
        print("-" * 30)
        
        # List available backups
        if Config.BACKUP_DIR.exists():
            backups = [d.name for d in Config.BACKUP_DIR.iterdir() if d.is_dir()]
            
            if backups:
                print("Available backups:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup}")
                
                try:
                    choice = int(input("Select backup number: ").strip()) - 1
                    if 0 <= choice < len(backups):
                        selected_backup = backups[choice]
                        confirm = input(f"Import data from '{selected_backup}'? (yes/no): ").strip().lower()
                        
                        if confirm == 'yes':
                            self.importer.import_data_from_backup(selected_backup)
                            print("Data import completed!")
                        else:
                            print("Data import cancelled.")
                    else:
                        print("Invalid backup selection.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            else:
                print("No backups found.")
        else:
            print("Backup directory not found.")
    
    def handle_view_statistics(self):
        """Handle viewing data statistics"""
        print("\nDATABASE STATISTICS")
        print("-" * 30)
        
        models_stats = {
            'Users': CustomUser.objects.count(),
            'Faculties': Faculty.objects.count(),
            'Departments': Department.objects.count(),
            'Programs': Program.objects.count(),
            'Academic Sessions': AcademicSession.objects.count(),
            'Semesters': Semester.objects.count(),
            'Teachers': Teacher.objects.count(),
            'Offices': Office.objects.count(),
            'Office Staff': OfficeStaff.objects.count(),
            'Courses': Course.objects.count(),
            'Course Offerings': CourseOffering.objects.count(),
            'Venues': Venue.objects.count(),
            'Timetable Slots': TimetableSlot.objects.count(),
            'Students': Student.objects.count(),
            'Applicants': Applicant.objects.count(),
            'Semester Enrollments': StudentSemesterEnrollment.objects.count(),
            'Course Enrollments': CourseEnrollment.objects.count(),
            'Assignments': Assignment.objects.count(),
            'Assignment Submissions': AssignmentSubmission.objects.count(),
            'Study Materials': StudyMaterial.objects.count(),
            'Attendance Records': Attendance.objects.count(),
            'Exam Results': ExamResult.objects.count(),
            'Notices': Notice.objects.count(),
            'Quizzes': Quiz.objects.count(),
            'Questions': Question.objects.count(),
            'Quiz Submissions': QuizSubmission.objects.count(),
        }
        
        # Add fee management stats if available
        if FEE_MANAGEMENT_AVAILABLE:
            try:
                models_stats['Semester Fees'] = SemesterFee.objects.count()
                models_stats['Fee Vouchers'] = FeeVoucher.objects.count()
            except:
                pass
        
        # Display statistics
        total_records = 0
        for model_name, count in models_stats.items():
            print(f"- {model_name:<25}: {count:>8}")
            total_records += count
        
        print("-" * 40)
        print(f"{'Total Records':<25}: {total_records:>8}")
        
        # Additional statistics
        print("\nADDITIONAL STATISTICS")
        print("-" * 30)
        
        try:
            active_sessions = AcademicSession.objects.filter(is_active=True).count()
            active_students = Student.objects.filter(current_status='active').count()
            active_teachers = Teacher.objects.filter(is_active=True).count()
            active_courses = CourseOffering.objects.filter(is_active=True).count()
            
            print(f"- Active Sessions: {active_sessions}")
            print(f"- Active Students: {active_students}")
            print(f"- Active Teachers: {active_teachers}")
            print(f"- Active Course Offerings: {active_courses}")
            
            # Database size estimation
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                db_size = cursor.fetchone()[0] if cursor.fetchone() else "Unknown"
                print(f"- Database Size: {db_size}")
                
        except Exception as e:
            print(f"- Error getting additional stats: {str(e)}")
        
        input("\nPress Enter to continue...")
    
    def handle_configuration(self):
        """Handle configuration settings"""
        print("\nCONFIGURATION SETTINGS")
        print("-" * 30)
        
        while True:
            print("\n1. View Current Configuration")
            print("2. Modify Data Generation Quantities")
            print("3. Update University Information")
            print("4. Reset to Default Configuration")
            print("0. Back to Main Menu")
            
            choice = input("\nEnter your choice (0-4): ").strip()
            
            if choice == '1':
                self.show_current_config()
            elif choice == '2':
                self.modify_quantities()
            elif choice == '3':
                self.update_university_info()
            elif choice == '4':
                self.reset_config()
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")
    
    def show_current_config(self):
        """Display current configuration"""
        print("\nCURRENT CONFIGURATION")
        print("-" * 40)
        
        print("Data Generation Quantities:")
        print(f"- Faculties: {Config.NUM_FACULTIES}")
        print(f"- Departments per Faculty: {Config.NUM_DEPARTMENTS_PER_FACULTY}")
        print(f"- Programs per Department: {Config.NUM_PROGRAMS_PER_DEPARTMENT}")
        print(f"- Sessions: {Config.NUM_SESSIONS}")
        print(f"- Teachers per Department: {Config.NUM_TEACHERS_PER_DEPARTMENT}")
        print(f"- Students per Program: {Config.NUM_STUDENTS_PER_PROGRAM}")
        print(f"- Courses per Department: {Config.NUM_COURSES_PER_DEPARTMENT}")
        print(f"- Assignments per Course: {Config.NUM_ASSIGNMENTS_PER_COURSE}")
        print(f"- Study Materials per Course: {Config.NUM_STUDY_MATERIALS_PER_COURSE}")
        print(f"- Quizzes per Course: {Config.NUM_QUIZZES_PER_COURSE}")
        print(f"- Questions per Quiz: {Config.NUM_QUESTIONS_PER_QUIZ}")
        
        print(f"\nUniversity Information:")
        print(f"- Name: {Config.UNIVERSITY_NAME}")
        print(f"- Domains: {', '.join(Config.UNIVERSITY_DOMAINS)}")
        
        print(f"\nFile Paths:")
        print(f"- Backup Directory: {Config.BACKUP_DIR}")
        print(f"- Log File: {Config.LOG_FILE}")
        
        input("\nPress Enter to continue...")
    
    def modify_quantities(self):
        """Modify data generation quantities"""
        print("\nMODIFY DATA GENERATION QUANTITIES")
        print("-" * 40)
        
        try:
            print("Enter new values (press Enter to keep current value):")
            
            # Get new values
            new_faculties = input(f"Faculties ({Config.NUM_FACULTIES}): ").strip()
            if new_faculties:
                Config.NUM_FACULTIES = int(new_faculties)
            
            new_depts = input(f"Departments per Faculty ({Config.NUM_DEPARTMENTS_PER_FACULTY}): ").strip()
            if new_depts:
                Config.NUM_DEPARTMENTS_PER_FACULTY = int(new_depts)
            
            new_programs = input(f"Programs per Department ({Config.NUM_PROGRAMS_PER_DEPARTMENT}): ").strip()
            if new_programs:
                Config.NUM_PROGRAMS_PER_DEPARTMENT = int(new_programs)
            
            new_teachers = input(f"Teachers per Department ({Config.NUM_TEACHERS_PER_DEPARTMENT}): ").strip()
            if new_teachers:
                Config.NUM_TEACHERS_PER_DEPARTMENT = int(new_teachers)
            
            new_students = input(f"Students per Program ({Config.NUM_STUDENTS_PER_PROGRAM}): ").strip()
            if new_students:
                Config.NUM_STUDENTS_PER_PROGRAM = int(new_students)
            
            new_courses = input(f"Courses per Department ({Config.NUM_COURSES_PER_DEPARTMENT}): ").strip()
            if new_courses:
                Config.NUM_COURSES_PER_DEPARTMENT = int(new_courses)
            
            print("\nConfiguration updated successfully!")
            
        except ValueError:
            print("Invalid input. Please enter valid numbers.")
        except Exception as e:
            print(f"Error updating configuration: {str(e)}")
    
    def update_university_info(self):
        """Update university information"""
        print("\nUPDATE UNIVERSITY INFORMATION")
        print("-" * 40)
        
        try:
            new_name = input(f"University Name ({Config.UNIVERSITY_NAME}): ").strip()
            if new_name:
                Config.UNIVERSITY_NAME = new_name
            
            print("Current domains:", ", ".join(Config.UNIVERSITY_DOMAINS))
            new_domains = input("New domains (comma-separated, press Enter to keep current): ").strip()
            if new_domains:
                Config.UNIVERSITY_DOMAINS = [d.strip() for d in new_domains.split(',')]
            
            print("\nUniversity information updated successfully!")
            
        except Exception as e:
            print(f"Error updating university information: {str(e)}")
    
    def reset_config(self):
        """Reset configuration to defaults"""
        print("\nRESET CONFIGURATION")
        print("-" * 30)
        
        confirm = input("Reset all configuration to default values? (yes/no): ").strip().lower()
        if confirm == 'yes':
            # Reset to original values
            Config.NUM_FACULTIES = 3
            Config.NUM_DEPARTMENTS_PER_FACULTY = 3
            Config.NUM_PROGRAMS_PER_DEPARTMENT = 2
            Config.NUM_SESSIONS = 3
            Config.NUM_TEACHERS_PER_DEPARTMENT = 5
            Config.NUM_STUDENTS_PER_PROGRAM = 20
            Config.NUM_COURSES_PER_DEPARTMENT = 8
            Config.NUM_ASSIGNMENTS_PER_COURSE = 3
            Config.NUM_STUDY_MATERIALS_PER_COURSE = 5
            Config.NUM_QUIZZES_PER_COURSE = 2
            Config.NUM_QUESTIONS_PER_QUIZ = 5
            Config.UNIVERSITY_NAME = "Campus360 University"
            Config.UNIVERSITY_DOMAINS = ["campus360.edu.pk", "student.campus360.edu.pk", "faculty.campus360.edu.pk"]
            
            print("Configuration reset to default values!")
        else:
            print("Configuration reset cancelled.")

# ============================================================================
# DATA VALIDATION AND INTEGRITY CHECKS
# ============================================================================

class DataValidator:
    """Validate data integrity and relationships"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_all_data(self):
        """Run comprehensive data validation"""
        logger.info("Starting data validation...")
        
        self.validation_errors = []
        self.validation_warnings = []
        
        # Run all validation checks
        self.validate_user_relationships()
        self.validate_academic_structure()
        self.validate_enrollments()
        self.validate_course_offerings()
        self.validate_attendance_records()
        self.validate_file_references()
        
        # Report results
        self.report_validation_results()
        
        return len(self.validation_errors) == 0
    
    def validate_user_relationships(self):
        """Validate user-related relationships"""
        # Check for users without profiles
        users_without_profiles = CustomUser.objects.exclude(
            teacher__isnull=False
        ).exclude(
            student__isnull=False
        ).exclude(
            officestaff__isnull=False
        ).exclude(
            is_superuser=True
        )
        
        if users_without_profiles.exists():
            self.validation_warnings.append(
                f"Found {users_without_profiles.count()} users without associated profiles"
            )
        
        # Check for duplicate emails
        duplicate_emails = CustomUser.objects.values('email').annotate(
            count=models.Count('email')
        ).filter(count__gt=1)
        
        if duplicate_emails.exists():
            self.validation_errors.append(
                f"Found {duplicate_emails.count()} duplicate email addresses"
            )
    
    def validate_academic_structure(self):
        """Validate academic structure integrity"""
        # Check for programs without departments
        programs_without_dept = Program.objects.filter(department__isnull=True)
        if programs_without_dept.exists():
            self.validation_errors.append(
                f"Found {programs_without_dept.count()} programs without departments"
            )
        
        # Check for departments without faculty
        depts_without_faculty = Department.objects.filter(faculty__isnull=True)
        if depts_without_faculty.exists():
            self.validation_errors.append(
                f"Found {depts_without_faculty.count()} departments without faculty"
            )
        
        # Check for inactive sessions with active semesters
        inactive_sessions_with_active_semesters = AcademicSession.objects.filter(
            is_active=False,
            semester__is_active=True
        ).distinct()
        
        if inactive_sessions_with_active_semesters.exists():
            self.validation_warnings.append(
                f"Found {inactive_sessions_with_active_semesters.count()} inactive sessions with active semesters"
            )
    
    def validate_enrollments(self):
        """Validate enrollment data"""
        # Check for students enrolled in courses from different programs
        invalid_enrollments = CourseEnrollment.objects.exclude(
            course_offering__program=models.F('student_semester_enrollment__semester__program')
        )
        
        if invalid_enrollments.exists():
            self.validation_errors.append(
                f"Found {invalid_enrollments.count()} invalid course enrollments (wrong program)"
            )
        
        # Check for enrollment count mismatches
        offerings_with_wrong_count = CourseOffering.objects.annotate(
            actual_count=models.Count('course_enrollments')
        ).exclude(
            current_enrollment=models.F('actual_count')
        )
        
        if offerings_with_wrong_count.exists():
            self.validation_warnings.append(
                f"Found {offerings_with_wrong_count.count()} course offerings with incorrect enrollment counts"
            )
    
    def validate_course_offerings(self):
        """Validate course offering data"""
        # Check for course offerings without timetable slots
        offerings_without_slots = CourseOffering.objects.filter(
            timetable_slots__isnull=True,
            is_active=True
        )
        
        if offerings_without_slots.exists():
            self.validation_warnings.append(
                f"Found {offerings_without_slots.count()} active course offerings without timetable slots"
            )
        
        # Check for overlapping timetable slots for same teacher
        overlapping_slots = TimetableSlot.objects.values(
            'course_offering__teacher', 'day', 'start_time'
        ).annotate(
            count=models.Count('id')
        ).filter(count__gt=1)
        
        if overlapping_slots.exists():
            self.validation_errors.append(
                f"Found {overlapping_slots.count()} overlapping timetable slots"
            )
    
    def validate_attendance_records(self):
        """Validate attendance records"""
        # Check for attendance records for non-enrolled students
        invalid_attendance = Attendance.objects.exclude(
            student__semester_enrollments__course_enrollments__course_offering=models.F('course_offering')
        )
        
        if invalid_attendance.exists():
            self.validation_errors.append(
                f"Found {invalid_attendance.count()} attendance records for non-enrolled students"
            )
        
        # Check for future attendance records
        future_attendance = Attendance.objects.filter(
            date__gt=timezone.now().date()
        )
        
        if future_attendance.exists():
            self.validation_warnings.append(
                f"Found {future_attendance.count()} attendance records for future dates"
            )
    
    def validate_file_references(self):
        """Validate file references"""
        # This is a simplified check - in production, you'd check actual file existence
        models_with_files = [
            (Department, 'image'),
            (StudyMaterial, 'image'),
            (Assignment, 'resource_file'),
            (AssignmentSubmission, 'file'),
            (Applicant, 'applicant_photo'),
            (AcademicQualification, 'certificate_file'),
        ]
        
        for model, field in models_with_files:
            empty_files = model.objects.filter(**{f"{field}__isnull": True})
            if empty_files.exists():
                self.validation_warnings.append(
                    f"Found {empty_files.count()} {model.__name__} records without {field}"
                )
    
    def report_validation_results(self):
        """Report validation results"""
        print("\nDATA VALIDATION RESULTS")
        print("=" * 50)
        
        if not self.validation_errors and not self.validation_warnings:
            print("✅ All validation checks passed!")
            return
        
        if self.validation_errors:
            print(f"\n❌ ERRORS ({len(self.validation_errors)}):")
            for i, error in enumerate(self.validation_errors, 1):
                print(f"  {i}. {error}")
        
        if self.validation_warnings:
            print(f"\n⚠️  WARNINGS ({len(self.validation_warnings)}):")
            for i, warning in enumerate(self.validation_warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\n" + "=" * 50)

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """Monitor database performance and provide optimization suggestions"""
    
    def __init__(self):
        self.metrics = {}
    
    def analyze_performance(self):
        """Analyze database performance"""
        logger.info("Analyzing database performance...")
        
        self.check_table_sizes()
        self.check_query_performance()
        self.check_index_usage()
        self.provide_optimization_suggestions()
    
    def check_table_sizes(self):
        """Check table sizes"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats
                    WHERE schemaname = 'public'
                    ORDER BY n_distinct DESC;
                """)
                
                results = cursor.fetchall()
                self.metrics['table_stats'] = results
                
        except Exception as e:
            logger.warning(f"Could not analyze table sizes: {str(e)}")
    
    def check_query_performance(self):
        """Check query performance"""
        # This would typically involve analyzing slow query logs
        # For now, we'll do basic checks
        
        slow_queries = []
        
        # Check for N+1 query problems by looking at related object access patterns
        # This is a simplified check
        try:
            # Check course offerings with many related queries
            offerings_count = CourseOffering.objects.count()
            if offerings_count > 100:
                slow_queries.append("Consider using select_related() for CourseOffering queries")
            
            # Check student enrollments
            enrollments_count = CourseEnrollment.objects.count()
            if enrollments_count > 500:
                slow_queries.append("Consider using prefetch_related() for enrollment queries")
            
            self.metrics['slow_queries'] = slow_queries
            
        except Exception as e:
            logger.warning(f"Could not analyze query performance: {str(e)}")
    
    def check_index_usage(self):
        """Check database index usage"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    ORDER BY schemaname, tablename;
                """)
                
                unused_indexes = cursor.fetchall()
                self.metrics['unused_indexes'] = unused_indexes
                
        except Exception as e:
            logger.warning(f"Could not analyze index usage: {str(e)}")
    
    def provide_optimization_suggestions(self):
        """Provide optimization suggestions"""
        suggestions = []
        
        # Based on collected metrics, provide suggestions
        if 'slow_queries' in self.metrics:
            suggestions.extend(self.metrics['slow_queries'])
        
        if 'unused_indexes' in self.metrics and self.metrics['unused_indexes']:
            suggestions.append(f"Consider removing {len(self.metrics['unused_indexes'])} unused indexes")
        
        # General suggestions based on data volume
        total_students = Student.objects.count()
        total_courses = CourseOffering.objects.count()
        
        if total_students > 1000:
            suggestions.append("Consider partitioning student-related tables by academic year")
        
        if total_courses > 500:
            suggestions.append("Consider archiving old course offerings")
        
        self.metrics['suggestions'] = suggestions
        
        # Display suggestions
        if suggestions:
            print("\nPERFORMANCE OPTIMIZATION SUGGESTIONS")
            print("=" * 50)
            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion}")
        else:
            print("\n✅ No performance issues detected!")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    try:
        # Check Django setup
        from django.core.management import execute_from_command_line
        
        print("Campus360 University Data Management System")
        print("=" * 60)
        print("Initializing Django environment...")
        
        # Initialize the interactive menu
        menu = InteractiveMenu()
        menu.show_main_menu()
        
    except ImportError as e:
        print(f"Django import error: {str(e)}")
        print("Make sure Django is installed and DJANGO_SETTINGS_MODULE is set correctly.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
