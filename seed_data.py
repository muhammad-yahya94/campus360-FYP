import os
import django
from faker import Faker
from faker.providers import date_time, lorem, python, file, internet, job, phone_number, address
from faker_education import SchoolProvider
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.utils import timezone
import random   
from datetime import timedelta, datetime   

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import models from your apps
from users.models import CustomUser
from academics.models import Faculty, Department, Program, Semester
from site_elements.models import Slider, Alumni, Gallery
from announcements.models import News, Event
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from faculty_staff.models import Teacher, Office, OfficeStaff, DESIGNATION_CHOICES
from courses.models import Course, CourseOffering
from students.models import Student, StudentEnrollment


fake = Faker()
fake.add_provider(SchoolProvider)

def create_fake_users(num_users=20):
    print(f'Creating {num_users} fake users...')
    users = []
    for _ in range(num_users):
        try:
            # Increase probability of staff users to 40%
            is_staff = random.random() < 0.4
            
            user = CustomUser.objects.create_user(
                email=fake.unique.email(),
                password='password123', # Default password
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                info=fake.sentence(),
                is_staff=is_staff,
                is_superuser=False # Don't create fake superusers by default
            )
            users.append(user)
            print(f'  Created user: {user.email} (Staff: {is_staff})')
        except IntegrityError:
            print('  Skipping user creation due to unique constraint violation (email).')
            continue # Skip if email is not unique

        # Add a dummy profile picture
        try:
            profile_picture_content = fake.image(size=(200, 200), image_format='jpeg')
            profile_picture_file = SimpleUploadedFile(
                name=f'{slugify(user.email)}_profile.jpg',
                content=profile_picture_content,
                content_type='image/jpeg'
            )
            user.profile_picture = profile_picture_file
            user.save()
            print(f'    Added profile picture for {user.email}')
        except Exception as e:
            print(f'    Failed to add profile picture for {user.email}: {e}')

    return users

def create_fake_faculties(num_faculties=5):
    print(f'Creating {num_faculties} fake faculties...')
    faculties = []
    for _ in range(num_faculties):
        try:
            name = fake.unique.catch_phrase() + ' Faculty'
            faculty, created = Faculty.objects.get_or_create(
                name=name,
                defaults={
                    'description': fake.paragraph(nb_sentences=5),
                    'slug': slugify(name) # Slug is auto-populated on save if not provided
                }
            )
            if created:
                faculties.append(faculty)
                print(f'  Created faculty: {faculty.name}')
            else:
                 print(f'  Faculty already exists: {faculty.name}')
        except IntegrityError:
            print(f'  Skipping faculty creation due to unique slug violation.')
            continue
    return faculties

def create_fake_departments(num_departments_per_faculty=3):
    print(f'Creating fake departments...')
    faculties = Faculty.objects.all()
    if not faculties.exists():
        print('No faculties found. Please create some faculties first.')
        return []
    departments = []
    for faculty in faculties:
        print(f'  Adding departments to {faculty.name}...')
        for i in range(num_departments_per_faculty):
            try:
                name = fake.unique.word() + ' Department'
                code = fake.unique.lexify(text='????').upper()

                # Create a dummy image file
                image_content = fake.image(size=(800, 600), image_format='jpeg')
                image_file = SimpleUploadedFile(
                    name=f'{slugify(name)}.jpg',
                    content=image_content,
                    content_type='image/jpeg'
                )

                department, created = Department.objects.get_or_create(
                    name=name,
                    defaults={
                        'faculty': faculty,
                        'code': code,
                        'image': image_file,
                        'introduction': fake.paragraph(nb_sentences=3),
                        'details': fake.text(max_nb_chars=500),
                        'slug': slugify(name + '-' + code) # Ensure unique slug if names are similar
                    }
                )
                if created:
                    departments.append(department)
                    print(f'    Created department: {department.name} ({department.code})')
                else:
                     print(f'    Department already exists: {department.name}')
            except IntegrityError:
                print(f'    Skipping department creation due to unique constraint violation.')
                continue
            except Exception as e:
                print(f'    Error creating department: {e}')

    return departments

def create_fake_programs(num_programs_per_department=2):
    print(f'Creating fake programs...')
    departments = Department.objects.all()
    if not departments.exists():
        print('No departments found. Please create some departments first.')
        return []
    programs = []
    for department in departments:
        print(f'  Adding programs to {department.name}...')
        degree_types = ['BS', 'MS', 'PhD', 'MPhil']
        for i in range(num_programs_per_department):
            try:
                name = fake.catch_phrase() + ' Program'
                degree_type = random.choice(degree_types)
                total_semesters = random.choice([4, 6, 8, 10])
                
                program, created = Program.objects.get_or_create(
                    department=department,
                    name=name,
                    degree_type=degree_type,
                    defaults={
                        'duration_years': total_semesters // 2,  # Assuming 2 semesters per year
                        'total_semesters': total_semesters,
                    }
                )
                if created:
                    programs.append(program)
                    print(f'    Created program: {program.name} ({program.degree_type})')
                    
                    # Create semesters for this program
                    for sem_num in range(1, total_semesters + 1):
                        semester_name = f'Semester {sem_num}'
                        
                        # Get or create academic session
                        current_year = timezone.now().year
                        session_name = f'Fall {current_year}'
                        current_session, session_created = AcademicSession.objects.get_or_create(
                            name=session_name,
                            defaults={
                                'start_date': datetime(current_year, 9, 1),
                                'end_date': datetime(current_year, 12, 31),
                                'is_active': True
                            }
                        )
                        
                        if session_created:
                            print(f'    Created academic session: {current_session.name}')
                        
                        # Calculate semester dates
                        start_date = current_session.start_date
                        end_date = current_session.end_date
                        mid_term_start = start_date + timedelta(days=30)
                        mid_term_end = mid_term_start + timedelta(days=15)
                        final_term_start = end_date - timedelta(days=30)
                        final_term_end = end_date
                        registration_start = start_date - timedelta(days=30)
                        registration_end = start_date - timedelta(days=7)
                        classes_start = start_date
                        
                        try:
                            semester, sem_created = Semester.objects.get_or_create(
                                program=program,
                                semester_number=sem_num,
                                academic_session=current_session,
                                defaults={
                                    'semester_type': 'regular',
                                    'name': semester_name,
                                    'is_active': True,
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'registration_start': registration_start,
                                    'registration_end': registration_end,
                                    'classes_start': classes_start,
                                    'mid_term_start': mid_term_start,
                                    'mid_term_end': mid_term_end,
                                    'final_term_start': final_term_start,
                                    'final_term_end': final_term_end
                                }
                            )
                            if sem_created:
                                print(f'      Created semester: {semester.name} for {program.name}')
                        except Exception as e:
                            print(f'      Error creating semester: {e}')
                            continue
                else:
                    print(f'    Program already exists: {program.name} ({program.degree_type})')
            except IntegrityError:
                print(f'    Skipping program creation due to unique constraint violation.')
                continue

    return programs

def create_fake_academic_sessions(num_sessions=4):
    print(f'Creating {num_sessions} academic sessions...')
    sessions = []
    current_year = timezone.now().year
    
    for i in range(num_sessions):
        try:
            start_year = current_year - (num_sessions - i - 1)
            end_year = start_year + 4  # 4-year program
            name = f'Fall {start_year}'
            
            session, created = AcademicSession.objects.get_or_create(
                name=name,
                defaults={
                    'start_year': start_year,
                    'end_year': end_year,
                    'is_active': (i == num_sessions - 1),  # Make the last one active
                    'description': f'Academic session for {start_year}-{end_year}'
                }
            )
            if created:
                sessions.append(session)
                print(f'  Created academic session: {session.name}')
            else:
                print(f'  Academic session already exists: {session.name}')
        except Exception as e:
            print(f'  Error creating academic session: {e}')
    
    return sessions

def create_fake_semesters():
    print(f'Creating semesters...')
    programs = Program.objects.all()
    academic_sessions = AcademicSession.objects.all()

    if not programs.exists():
        print('No programs found. Please create some programs first.')
        return []
    if not academic_sessions.exists():
        print('No academic sessions found. Please create some academic sessions first.')
        return []

    semesters = []
    for program in programs:
        print(f'  Creating semesters for program: {program.name}...')
        for session in academic_sessions:
            print(f'    Creating semesters for session: {session.name}...')
            for i in range(1, program.total_semesters + 1):
                try:
                    # Calculate semester dates based on academic session
                    is_fall = i % 2 == 1
                    start_month = 9 if is_fall else 2
                    end_month = 12 if is_fall else 5
                    
                    start_date = datetime(session.start_year, start_month, 1)
                    end_date = datetime(session.start_year, end_month, 31)
                    
                    # Calculate other dates
                    registration_start = start_date - timedelta(days=30)
                    registration_end = start_date - timedelta(days=7)
                    classes_start = start_date
                    mid_term_start = start_date + timedelta(days=45)
                    mid_term_end = mid_term_start + timedelta(days=15)
                    final_term_start = end_date - timedelta(days=30)
                    final_term_end = end_date
                    
                    semester, created = Semester.objects.get_or_create(
                        academic_session=session,  # Use the session instance directly
                        semester_number=i,
                        defaults={
                            'semester_type': 'fall' if is_fall else 'spring',
                            'start_date': start_date,
                            'end_date': end_date,
                            'registration_start': registration_start,
                            'registration_end': registration_end,
                            'classes_start': classes_start,
                            'mid_term_start': mid_term_start,
                            'mid_term_end': mid_term_end,
                            'final_term_start': final_term_start,
                            'final_term_end': final_term_end,
                            'is_active': True
                        }
                    )
                    if created:
                        semesters.append(semester)
                        print(f'      Created semester: {semester.semester_number} for {session.name}')
                    else:
                        print(f'      Semester already exists: {semester.semester_number} for {session.name}')
                except IntegrityError:
                    print(f'      Skipping semester creation due to unique constraint.')
                    continue
                except Exception as e:
                    print(f'      Error creating semester: {e}')
                    print(f'      Session: {session} (type: {type(session)})')
                    continue

    return semesters

def create_fake_admission_cycles(num_cycles_per_program=1):
    print(f'Creating fake admission cycles...')
    programs = Program.objects.all()
    sessions = AcademicSession.objects.all()
    if not programs.exists():
        print('No programs found. Please create some programs first.')
        return []
    if not sessions.exists():
        print('No academic sessions found. Please create some academic sessions first.')
        return []

    cycles = []
    for program in programs:
        print(f'  Adding admission cycles for {program.name}...')
        available_sessions = list(sessions)
        random.shuffle(available_sessions)
        sessions_to_use = available_sessions[:num_cycles_per_program]

        for session in sessions_to_use:
            try:
                start_date = fake.date_between_dates(date_start=session.start_date - timedelta(days=90), date_end=session.start_date - timedelta(days=30))
                end_date = fake.date_between_dates(date_start=session.start_date - timedelta(days=20), date_end=session.start_date - timedelta(days=5))
                is_open = fake.boolean(chance_of_getting_true=50) # 50% chance of being open

                cycle, created = AdmissionCycle.objects.get_or_create(
                    program=program,
                    session=session,
                    defaults={
                        'application_start': start_date,
                        'application_end': end_date,
                        'is_open': is_open,
                    }
                )
                if created:
                    cycles.append(cycle)
                    print(f'    Created admission cycle: {cycle}')
                else:
                    print(f'    Admission cycle already exists: {cycle}')
            except IntegrityError:
                 print(f'    Skipping admission cycle creation due to unique constraint violation.')
                 continue

    return cycles

def create_fake_applicants(num_applicants_per_program=10):
    print(f'Creating fake applicants...')
    programs = Program.objects.all()
    users = list(CustomUser.objects.filter(is_superuser=False, is_staff=False)) # Use non-staff, non-superusers

    if not programs.exists():
        print('No programs found. Please create some programs first.')
        return []
    if not users:
        print('No suitable users found. Please create some users first.')
        return []

    applicants = []
    # Shuffle users to assign them randomly to applicants
    random.shuffle(users)
    user_index = 0

    for program in programs:
        print(f'  Adding applicants for {program.name}...')
        for i in range(num_applicants_per_program):
            if user_index >= len(users):
                print('    Not enough users to create more applicants.')
                break
            user = users[user_index]
            user_index += 1
            try:
                # Ensure at least 50% of applicants are accepted
                if i < num_applicants_per_program * 0.5:
                    status = 'accepted'
                else:
                    status = random.choice(['pending', 'rejected'])
                
                dob = fake.date_of_birth(minimum_age=18, maximum_age=30)

                # Create a dummy photo file
                photo_content = fake.image(size=(200, 200), image_format='jpeg')
                photo_file = SimpleUploadedFile(
                    name=f'{slugify(user.email)}_applicant.jpg',
                    content=photo_content,
                    content_type='image/jpeg'
                )

                applicant, created = Applicant.objects.get_or_create(
                    user=user,
                    program=program,
                    defaults={
                        'faculty': program.department.faculty,
                        'department': program.department,
                        'status': status,
                        'applicant_photo': photo_file,
                        'full_name': user.full_name or fake.name(),
                        'religion': fake.word(ext_word_list=['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Other']),
                        'caste': fake.word(),
                        'cnic': fake.unique.bothify(text='#####-#######-#'),
                        'dob': dob,
                        'contact_no': fake.phone_number(),
                        'identification_mark': fake.sentence(nb_words=5),
                        'father_name': fake.name(),
                        'father_occupation': fake.job(),
                        'father_cnic': fake.unique.bothify(text='#####-#######-#'),
                        'monthly_income': random.randint(30000, 200000),
                        'relationship': random.choice(['father', 'guardian']),
                        'permanent_address': fake.address(),
                        'declaration': True,
                    }
                )
                if created:
                    applicants.append(applicant)
                    print(f'    Created applicant: {applicant.full_name} for {applicant.program.name} (Status: {status})')
                else:
                    print(f'    Applicant already exists for user {user.email} and program {program.name}')

            except IntegrityError:
                print(f'    Skipping applicant creation for user {user.email} due to unique constraint.')
                continue
            except Exception as e:
                print(f'    Error creating applicant for user {user.email}: {e}')

    return applicants

def create_fake_academic_qualifications(num_qualifications_per_applicant=2):
    print(f'Creating fake academic qualifications...')
    applicants = Applicant.objects.all()
    if not applicants.exists():
        print('No applicants found. Please create some applicants first.')
        return []
    qualifications = []
    for applicant in applicants:
        print(f'  Adding qualifications for {applicant.full_name}...')
        for i in range(num_qualifications_per_applicant):
            try:
                passing_year = random.randint(applicant.dob.year + 16 + i, applicant.dob.year + 18 + i)
                total_marks = random.choice([1100, 1000, 500, 400])
                marks_obtained = random.randint(int(total_marks * 0.5), int(total_marks * 0.95))
                division = random.choice(['A+', 'A', 'B', 'C', 'Fail'])

                qualification, created = AcademicQualification.objects.get_or_create(
                    applicant=applicant,
                     # Add unique constraint fields here if necessary for get_or_create
                    defaults={
                        'passing_year': passing_year,
                        'marks_obtained': marks_obtained,
                        'total_marks': total_marks,
                        'division': division,
                        'subjects': fake.catch_phrase(),
                        'board': fake.city() + ' Board',
                  
                    }
                )
                if created:
                    qualifications.append(qualification)
                    print(f'    Created qualification: {qualification}')
                else:
                    print(f'    Qualification already exists for {applicant.full_name} ')

            except IntegrityError:
                 print(f'    Skipping qualification creation for {applicant.full_name} due to unique constraint.')
                 continue

    return qualifications

def create_fake_extra_curricular_activities(num_activities_per_applicant=1):
    print(f'Creating fake extra-curricular activities...')
    applicants = Applicant.objects.all()
    if not applicants.exists():
        print('No applicants found. Please create some applicants first.')
        return []
    activities = []
    for applicant in applicants:
        print(f'  Adding activities for {applicant.full_name}...')
        for i in range(num_activities_per_applicant):
            try:
                activity_year = random.randint(applicant.dob.year + 15, applicant.dob.year + 25)

                activity, created = ExtraCurricularActivity.objects.get_or_create(
                    applicant=applicant,
                     # Add unique constraint fields here if necessary for get_or_create
                    defaults={
                        'activity': fake.word() + ' Club',
                        'position': fake.job(),
                        'achievement': fake.sentence(nb_words=10),
                        'activity_year': activity_year
                    }
                )
                if created:
                    activities.append(activity)
                    print(f'    Created activity: {activity}')
                else:
                    print(f'    Activity already exists for {applicant.full_name}')
            except IntegrityError:
                print(f'    Skipping activity creation for {applicant.full_name} due to unique constraint.')
                continue

    return activities

def create_fake_offices(num_offices=5):
    print(f'Creating {num_offices} fake offices...')
    offices = []
    for _ in range(num_offices):
        try:
            name = fake.unique.job() + ' Office'
             # Create a dummy image file
            image_content = fake.image(size=(800, 600), image_format='jpeg')
            image_file = SimpleUploadedFile(
                name=f'{slugify(name)}.jpg',
                content=image_content,
                content_type='image/jpeg'
            )

            office, created = Office.objects.get_or_create(
                name=name,
                defaults={
                    'description': fake.paragraph(nb_sentences=5),
                    'image': image_file,
                    'location': fake.address(),
                    'contact_email': fake.unique.email(),
                    'contact_phone': fake.phone_number(),
                    'slug': slugify(name)
                }
            )
            if created:
                offices.append(office)
                print(f'  Created office: {office.name}')
            else:
                 print(f'  Office already exists: {office.name}')
        except IntegrityError:
            print(f'  Skipping office creation due to unique slug violation.')
            continue
        except Exception as e:
            print(f'  Error creating office: {e}')
    return offices

def create_fake_teachers(num_teachers_per_department=2):
    print(f'Creating fake teachers...')
    departments = Department.objects.all()
    # Use staff users for teachers
    staff_users = list(CustomUser.objects.filter(is_staff=True, is_superuser=False))

    if not departments.exists():
        print('No departments found. Please create some departments first.')
        return []
    if not staff_users:
        print('No staff users found for teachers. Please create some staff users first.')
        return []

    teachers = []
    # Shuffle staff users to assign them randomly to teachers
    random.shuffle(staff_users)
    user_index = 0

    for department in departments:
        print(f'  Adding teachers to {department.name}...')
        for i in range(num_teachers_per_department):
            if user_index >= len(staff_users):
                print('    Not enough staff users to create more teachers.')
                break
            user = staff_users[user_index]
            user_index += 1
            try:
                designation = random.choice([choice[0] for choice in DESIGNATION_CHOICES])

                teacher, created = Teacher.objects.get_or_create(
                    user=user,
                    department=department,
                     # Add unique constraint fields here if necessary for get_or_create
                    defaults={
                        'designation': designation,
                        'contact_no': fake.phone_number(),
                        'qualification': fake.sentence(nb_words=10) + ' in ' + department.name,
                        'hire_date': fake.date_this_decade(),
                        'is_active': True,
                    }
                )
                if created:
                    teachers.append(teacher)
                    print(f'    Created teacher: {teacher.user.full_name} ({teacher.designation})')
                else:
                     print(f'    Teacher already exists for user {user.email} in {department.name}')
            except IntegrityError:
                print(f'    Skipping teacher creation for user {user.email} due to unique constraint.')
                continue

    return teachers

def create_fake_office_staff(num_staff_per_office=3):
    print(f'Creating fake office staff...')
    offices = Office.objects.all()
     # Use staff users for office staff, excluding those already assigned as teachers
    staff_users = list(CustomUser.objects.filter(is_staff=True, is_superuser=False).exclude(teacher_profile__isnull=False))

    if not offices.exists():
        print('No offices found. Please create some offices first.')
        return []
    if not staff_users:
        print('No available staff users found for office staff. Please create more staff users.')
        return []

    officestaff = []
    # Shuffle available staff users to assign them randomly
    random.shuffle(staff_users)
    user_index = 0

    for office in offices:
        print(f'  Adding staff to {office.name}...')
        for i in range(num_staff_per_office):
            if user_index >= len(staff_users):
                print('    Not enough available staff users to create more office staff.')
                break
            user = staff_users[user_index]
            user_index += 1
            try:
                position = fake.job()

                staff, created = OfficeStaff.objects.get_or_create(
                    user=user,
                    office=office,
                    defaults={
                        'position': position,
                        'contact_no': fake.phone_number(),
                    }
                )
                if created:
                    officestaff.append(staff)
                    print(f'    Created staff: {staff.user.full_name} in {office.name}')
                else:
                     print(f'    Office staff already exists for user {user.email} in {office.name}')
            except IntegrityError:
                print(f'    Skipping office staff creation for user {user.email} due to unique constraint.')
                continue

    return officestaff

def delete_all_data():
    print("Deleting all existing data...")
    # Delete in reverse order of dependencies
    StudentEnrollment.objects.all().delete()
    Student.objects.all().delete()
    CourseOffering.objects.all().delete()
    Course.objects.all().delete()
    OfficeStaff.objects.all().delete()
    Teacher.objects.all().delete()
    Office.objects.all().delete()
    ExtraCurricularActivity.objects.all().delete()
    AcademicQualification.objects.all().delete()
    Applicant.objects.all().delete()
    AdmissionCycle.objects.all().delete()
    AcademicSession.objects.all().delete()
    Program.objects.all().delete()
    Department.objects.all().delete()
    Faculty.objects.all().delete()
    Gallery.objects.all().delete()
    Alumni.objects.all().delete()
    Slider.objects.all().delete()
    Event.objects.all().delete()
    News.objects.all().delete()
    CustomUser.objects.filter(is_superuser=False).delete()  # Keep superusers
    print("All existing data deleted.")

def create_fake_courses(num_courses_per_department=5):
    print(f'Creating fake courses...')
    departments = Department.objects.all()
    programs = Program.objects.all()
    if not departments.exists():
        print('No departments found. Please create some departments first.')
        return []
    if not programs.exists():
         print('No programs found. Please create some programs first.')
         return []
    courses = []

    all_programs = list(programs)
    program_index = 0

    for department in departments:
        print(f'  Adding courses for {department.name}...')
        for i in range(num_courses_per_department):
            if program_index >= len(all_programs):
                program_index = 0 # Cycle through programs if needed
            program = all_programs[program_index]
            program_index += 1

            try:
                code = f'{department.code[:2].upper()}{random.randint(100, 499)}'
                name = fake.catch_phrase() + ' ' + random.choice(['I', 'II', 'III', ''])

                course, created = Course.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'credits': random.randint(1, 4),
                        'description': fake.text(max_nb_chars=300),
                        'is_active': True,
                    }
                )
                if created:
                    courses.append(course)
                    print(f'    Created course: {course.code} - {course.name}')
                else:
                     print(f'    Course already exists: {course.code}')
            except IntegrityError:
                print(f'    Skipping course creation due to unique code violation.')
                continue

    return courses

def create_fake_course_offerings():
    print(f'Creating fake course offerings...')
    departments = Department.objects.all()
    programs = Program.objects.all()
    courses = Course.objects.all()
    teachers = Teacher.objects.all()
    semesters = Semester.objects.all()

    if not departments.exists() or not programs.exists():
        print('No departments or programs found. Cannot create course offerings.')
        return []

    if not courses.exists():
        print('No courses found. Please create some courses first.')
        return []
    if not teachers.exists():
        print('No teachers found. Please create some teachers first.')
        return []
    if not semesters.exists():
        print('No semesters found. Please create some semesters first.')
        return []

    offerings = []
    available_departments = list(departments)
    available_programs = list(programs)
    available_teachers = list(teachers)
    available_semesters = list(semesters)

    if not available_departments or not available_programs or not available_teachers or not available_semesters:
        print('Not enough departments, programs, teachers, or semesters to create course offerings.')
        return []

    random.shuffle(available_teachers)
    teacher_index = 0

    offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]

    for course in courses:
        if not available_teachers or not available_departments or not available_programs or not available_semesters:
            print(f'  Not enough resources to create offering for {course.name}. Skipping.')
            break

        teacher = available_teachers[teacher_index % len(available_teachers)]
        department = random.choice(available_departments)
        program = random.choice(available_programs)
        semester = random.choice([s for s in available_semesters if s.program == program])
        offering_type = random.choice(offering_types)

        teacher_index += 1

        try:
            offering, created = CourseOffering.objects.get_or_create(
                course=course,
                teacher=teacher,
                department=department,
                program=program,
                semester=semester,
                academic_session=semester.academic_session,
                offering_type=offering_type,
                defaults={
                    'is_active': True,
                    'max_capacity': random.randint(20, 40),
                    'current_enrollment': 0
                }
            )
            if created:
                offerings.append(offering)
                print(f'    Created offering: {offering}')
            else:
                print(f'    Offering already exists: {offering}')

        except IntegrityError:
            print(f'    Skipping course offering creation due to unique constraint.')
            continue

    return offerings

# Skipping CourseOfferingTeacherChange for simplicity, can be added if needed
# def create_fake_course_offering_teacher_changes():
#    pass

def create_fake_assignments(num_assignments_per_offering=3):
    print(f'Creating fake assignments...')
    offerings = CourseOffering.objects.all()
    if not offerings.exists():
        print('No course offerings found. Please create some course offerings first.')
        return []
    assignments = []
    for offering in offerings:
        print(f'  Adding assignments for {offering}...')
        for i in range(num_assignments_per_offering):
            try:
                # Generate a plausible due date within the current year for simplicity
                due_date = fake.date_time_this_year()
                assignment_type = random.choice([choice[0] for choice in Assignment.ASSIGNMENT_TYPES])

                assignment, created = Assignment.objects.get_or_create(
                    course_offering=offering,
                    title=f'{assignment_type.capitalize()} {i + 1}',
                    defaults={
                        'description': fake.paragraph(nb_sentences=3),
                        'due_date': due_date,
                        'max_points': random.choice([50, 100, 200]),
                        'assignment_type': assignment_type,
                    }
                )
                if created:
                    assignments.append(assignment)
                    print(f'    Created assignment: {assignment.title}')
                else:
                    print(f'    Assignment already exists: {assignment.title} for {offering}')

            except IntegrityError:
                print(f'    Skipping assignment creation for {offering} due to unique constraint.')
                continue
            except Exception as e:
                print(f'    Error creating assignment for {offering}: {e}')
    return assignments

# Skipping Submission for simplicity, can be added if needed
# def create_fake_submissions():
#    pass

def create_fake_students():
    print(f'Creating fake students...')
    accepted_applicants = Applicant.objects.filter(status='accepted')

    if not accepted_applicants.exists():
        print('No accepted applicants found. Cannot create students.')
        return []

    students = []
    for applicant in accepted_applicants:
        try:
            if hasattr(applicant, 'student_profile'):
                print(f'  Student profile already exists for applicant {applicant.full_name}. Skipping.')
                continue

            # Get the program from the applicant
            program = applicant.program
            if not program:
                print(f'  No program found for applicant {applicant.full_name}. Skipping.')
                continue

            # Get or create active academic session
            current_year = timezone.now().year
            current_session = AcademicSession.objects.filter(is_active=True).first()
            if not current_session:
                print(f'  No active academic session found. Creating one...')
                current_session = AcademicSession.objects.create(
                    name=f'Fall {current_year}',
                    start_date=datetime(current_year, 9, 1),
                    end_date=datetime(current_year + 1, 5, 31),
                    is_active=True
                )
                print(f'  Created new academic session: {current_session.name}')

            # Get or create first semester
            first_semester = Semester.objects.filter(
                semester_number=1,
                is_active=True,
                academic_session=current_session  # Use the session instance directly
            ).first()
            
            if not first_semester:
                print(f'  No first semester found. Creating one...')
                first_semester = Semester.objects.create(
                    academic_session=current_session,  # Use the session instance directly
                    semester_number=1,
                    semester_type='fall',
                    start_date=datetime(current_year, 9, 1),
                    end_date=datetime(current_year, 12, 31),
                    registration_start=datetime(current_year, 8, 1),
                    registration_end=datetime(current_year, 8, 15),
                    classes_start=datetime(current_year, 9, 1),
                    mid_term_start=datetime(current_year, 10, 15),
                    mid_term_end=datetime(current_year, 10, 30),
                    final_term_start=datetime(current_year, 12, 15),
                    final_term_end=datetime(current_year, 12, 31),
                    is_active=True
                )
                print(f'  Created new semester: {first_semester.semester_number}')

            student, created = Student.objects.get_or_create(
                applicant=applicant,
                defaults={
                    'user': applicant.user,
                    'program': program,
                    'current_semester': first_semester,
                    'university_roll_no': fake.unique.random_int(min=10000, max=99999),
                    'college_roll_no': fake.unique.random_int(min=1000, max=9999),
                    'enrollment_date': fake.date_this_year(),
                    'current_status': 'active',
                    'emergency_contact': fake.name(),
                    'emergency_phone': fake.phone_number(),
                }
            )
            if created:
                students.append(student)
                print(f'  Created student profile for: {student.applicant.full_name}')
            else:
                print(f'  Student already exists for applicant {applicant.full_name}')
        except IntegrityError:
            print(f'  Skipping student creation for applicant {applicant.full_name} due to unique constraint.')
            continue
        except Exception as e:
            print(f'  Error creating student for applicant {applicant.full_name}: {e}')

    return students

def create_fake_student_enrollments():
    print(f'Creating fake student enrollments...')
    students = Student.objects.all()
    course_offerings = CourseOffering.objects.all()

    if not students.exists():
        print('No students found. Please create some students first.')
        return []
    if not course_offerings.exists():
        print('No course offerings found. Please create some course offerings first.')
        return []

    enrollments = []
    for student in students:
        print(f'  Enrolling student {student.applicant.full_name}...')
        # Get course offerings for the student's current semester
        available_offerings = course_offerings.filter(
            semester=student.current_semester,
            program=student.program
        )
        
        if not available_offerings.exists():
            print(f'    No course offerings available for semester {student.current_semester.name}.')
            continue

        # Enroll in 3-5 courses for the current semester
        num_offerings_to_enroll = random.randint(3, min(5, available_offerings.count()))
        offerings_to_enroll = random.sample(list(available_offerings), num_offerings_to_enroll)

        for offering in offerings_to_enroll:
            try:
                enrollment, created = StudentEnrollment.objects.get_or_create(
                    student=student.applicant,
                    course_offering=offering,
                    defaults={
                        'status': 'enrolled',
                    }
                )
                if created:
                    enrollments.append(enrollment)
                    print(f'    Enrolled {student.applicant.full_name} in {offering.course}')
            except IntegrityError:
                print(f'    Skipping enrollment for {student.applicant.full_name} in {offering.course} due to unique constraint.')
                continue
            except Exception as e:
                print(f'    Error creating enrollment for {student.applicant.full_name} in {offering.course}: {e}')

    return enrollments

def create_fake_sliders(num_sliders=3):
    print(f'Creating {num_sliders} fake sliders...')
    sliders = []
    for i in range(num_sliders):
        try:
            # Create a dummy image file
            image_content = fake.image(size=(1200, 600), image_format='jpeg')
            image_file = SimpleUploadedFile(
                name=f'slider_{i+1}.jpg',
                content=image_content,
                content_type='image/jpeg'
            )

            slider, created = Slider.objects.get_or_create(
                title=f'Slider Title {i+1}',
                defaults={
                    'image': image_file,
                    'is_active': True,
                }
            )
            if created:
                sliders.append(slider)
                print(f'  Created slider: {slider.title}')
            else:
                 print(f'  Slider already exists: {slider.title}')

        except IntegrityError:
             print(f'  Skipping slider creation due to unique constraint.')
             continue
        except Exception as e:
            print(f'  Error creating slider: {e}')

    return sliders

def create_fake_alumni(num_alumni=10):
    print(f'Creating {num_alumni} fake alumni...')
    alumni_list = []
    for _ in range(num_alumni):
        try:
            name = fake.name()
            # Create a dummy image file
            image_content = fake.image(size=(200, 200), image_format='jpeg')
            image_file = SimpleUploadedFile(
                name=f'{slugify(name)}_alumni.jpg',
                content=image_content,
                content_type='image/jpeg'
            )

            alumnus, created = Alumni.objects.get_or_create(
                name=name,
                 # Add unique constraint fields here if necessary for get_or_create
                defaults={
                    'graduation_year': fake.year(),
                    'profession': fake.job(),
                    'testimonial': fake.paragraph(nb_sentences=3),
                    'image': image_file,
                }
            )
            if created:
                alumni_list.append(alumnus)
                print(f'  Created alumni: {alumnus.name}')
            # No else needed, get_or_create handles existing

        except IntegrityError:
             print(f'  Skipping alumni creation due to unique constraint.')
             continue
        except Exception as e:
            print(f'  Error creating alumni: {e}')

    return alumni_list

def create_fake_gallery_items(num_items=15):
    print(f'Creating {num_items} fake gallery items...')
    gallery_items = []
    for i in range(num_items):
        try:
            title = fake.sentence(nb_words=4)
            # Create a dummy image file
            image_content = fake.image(size=(800, 600), image_format='jpeg')
            image_file = SimpleUploadedFile(
                name=f'gallery_{i+1}.jpg',
                content=image_content,
                content_type='image/jpeg'
            )

            item, created = Gallery.objects.get_or_create(
                title=title,
                 # Add unique constraint fields here if necessary for get_or_create
                defaults={
                    'image': image_file,
                    'date_added': fake.date_time_this_year(),
                }
            )
            if created:
                gallery_items.append(item)
                print(f'  Created gallery item: {item.title}')
            # No else needed, get_or_create handles existing

        except IntegrityError:
             print(f'  Skipping gallery item creation due to unique constraint.')
             continue
        except Exception as e:
            print(f'  Error creating gallery item: {e}')

    return gallery_items

def create_fake_news(num_news=10):
    print(f'Creating {num_news} fake news articles...')
    news_list = []
    for _ in range(num_news):
        try:
            title = fake.unique.sentence(nb_words=6)
            news, created = News.objects.get_or_create(
                title=title,
                defaults={
                    'content': fake.text(max_nb_chars=1000),
                    'published_date': fake.date_time_this_year(),
                    'is_published': fake.boolean(chance_of_getting_true=90),
                     # Slug is auto-populated by AutoSlugField
                }
            )
            if created:
                news_list.append(news)
                print(f'  Created news: {news.title}')
            else:
                 print(f'  News already exists: {news.title}')
        except IntegrityError:
             print(f'  Skipping news creation due to unique slug violation.')
             continue

    return news_list

def create_fake_events(num_events=10):
    print(f'Creating {num_events} fake events...')
    events_list = []
    for _ in range(num_events):
        try:
            title = fake.unique.sentence(nb_words=6) + ' Event'
            start_date = fake.date_time_this_year()
            end_date = start_date + timedelta(hours=random.randint(1, 5))

            # Create a dummy image file
            image_content = fake.image(size=(800, 400), image_format='jpeg')
            image_file = SimpleUploadedFile(
                name=f'{slugify(title)}_event.jpg',
                content=image_content,
                content_type='image/jpeg'
            )

            event, created = Event.objects.get_or_create(
                title=title,
                defaults={
                    'description': fake.text(max_nb_chars=500),
                    'event_start_date': start_date,
                    'event_end_date': end_date,
                    'location': fake.address(),
                    'image': image_file,
                    'created_at': fake.date_this_year(), # Assuming created_at is a DateField
                     # Slug is auto-populated by AutoSlugField
                }
            )
            if created:
                events_list.append(event)
                print(f'  Created event: {event.title}')
            else:
                 print(f'  Event already exists: {event.title}')
        except IntegrityError:
             print(f'  Skipping event creation due to unique slug violation.')
             continue
        except Exception as e:
             print(f'  Error creating event: {e}')

    return events_list

def create_fake_grading_system():
    print(f'Creating grading system...')
    grades = [
        ('A+', 90, 100, 4.0, 'Excellent'),
        ('A', 85, 89.99, 3.7, 'Very Good'),
        ('B+', 80, 84.99, 3.3, 'Good'),
        ('B', 75, 79.99, 3.0, 'Above Average'),
        ('C+', 70, 74.99, 2.7, 'Average'),
        ('C', 65, 69.99, 2.3, 'Below Average'),
        ('D+', 60, 64.99, 2.0, 'Passing'),
        ('D', 55, 59.99, 1.7, 'Barely Passing'),
        ('F', 0, 54.99, 0.0, 'Failing', False),
    ]
    
    for grade_data in grades:
        try:
            grade, min_marks, max_marks, points, desc = grade_data[:5]
            is_passing = grade_data[5] if len(grade_data) > 5 else True
            
            grade_obj, created = GradingSystem.objects.get_or_create(
                grade=grade,
                defaults={
                    'min_marks': min_marks,
                    'max_marks': max_marks,
                    'grade_points': points,
                    'description': desc,
                    'is_passing': is_passing
                }
            )
            if created:
                print(f'  Created grade: {grade} ({desc})')
        except Exception as e:
            print(f'  Error creating grade {grade}: {e}')

def create_fake_student_grades():
    print(f'Creating student grades...')
    enrollments = StudentEnrollment.objects.filter(status='enrolled')
    
    for enrollment in enrollments:
        try:
            # Generate random marks
            mid_term = random.randint(0, 100)
            final_term = random.randint(0, 100)
            assignment = random.randint(0, 100)
            quiz = random.randint(0, 100)
            
            # Calculate total marks
            total_marks = sum([mid_term, final_term, assignment, quiz])
            
            # Get the appropriate grade based on total marks
            grade = GradingSystem.objects.filter(
                min_marks__lte=total_marks,
                max_marks__gte=total_marks
            ).first()
            
            if not grade:
                print(f'  No grade found for marks {total_marks}. Skipping grade creation.')
                continue
            
            grade_obj, created = StudentGrade.objects.get_or_create(
                student=enrollment.student,
                course_offering=enrollment.course_offering,
                defaults={
                    'mid_term_marks': mid_term,
                    'final_term_marks': final_term,
                    'assignment_marks': assignment,
                    'quiz_marks': quiz,
                    'total_marks': total_marks,
                    'grade': grade,
                    'remarks': fake.sentence() if random.random() < 0.3 else ''
                }
            )
            if created:
                print(f'  Created grade for {enrollment.student} in {enrollment.course_offering}: {grade.grade}')
        except Exception as e:
            print(f'  Error creating grade for {enrollment.student}: {e}')

if __name__ == '__main__':
    print("Starting fake data generation...")
    
    # First delete all existing data
    delete_all_data()
    
    # Create core data first (essential for relationships)
    print("\n1. Creating core data...")
    fake_users = create_fake_users(num_users=50)  # Increased number of users
    fake_faculties = create_fake_faculties(num_faculties=3)
    fake_departments = create_fake_departments(num_departments_per_faculty=3)
    fake_programs = create_fake_programs(num_programs_per_department=2)
    
    # Create academic sessions and semesters
    print("\n2. Creating academic sessions and semesters...")
    fake_academic_sessions = create_fake_academic_sessions(num_sessions=4)
    create_fake_semesters()
    
    # Create grading system
    print("\n3. Creating grading system...")
    create_fake_grading_system()
    
    # Create data for admissions
    print("\n4. Creating admission data...")
    fake_admission_cycles = create_fake_admission_cycles(num_cycles_per_program=1)
    fake_applicants = create_fake_applicants(num_applicants_per_program=10)
    create_fake_academic_qualifications(num_qualifications_per_applicant=2)
    create_fake_extra_curricular_activities(num_activities_per_applicant=1)
    
    # Create faculty and staff
    print("\n5. Creating faculty and staff...")
    fake_offices = create_fake_offices(num_offices=4)
    fake_teachers = create_fake_teachers(num_teachers_per_department=2)
    create_fake_office_staff(num_staff_per_office=3)
    
    # Create courses and offerings
    print("\n6. Creating courses and offerings...")
    fake_courses = create_fake_courses(num_courses_per_department=5)
    
    # Ensure we have semesters before creating offerings
    if not Semester.objects.exists():
        print("No semesters found. Creating default semester...")
        current_year = timezone.now().year
        current_session = AcademicSession.objects.filter(is_active=True).first()
        if not current_session:
            current_session = AcademicSession.objects.create(
                name=f'Fall {current_year}',
                start_year=current_year,
                end_year=current_year + 4,  # 4-year program
                is_active=True,
                description=f'Academic session for {current_year}-{current_year + 4}'
            )
            print(f"Created new academic session: {current_session.name}")
        
        # Create a default semester for each program
        for program in Program.objects.all():
            try:
                # Get or create the semester
                semester, created = Semester.objects.get_or_create(
                    academic_session=current_session,  # Use the session instance directly
                    semester_number=1,
                    defaults={
                        'semester_type': 'fall',
                        'start_date': datetime(current_year, 9, 1),
                        'end_date': datetime(current_year, 12, 31),
                        'registration_start': datetime(current_year, 8, 1),
                        'registration_end': datetime(current_year, 8, 15),
                        'classes_start': datetime(current_year, 9, 1),
                        'mid_term_start': datetime(current_year, 10, 15),
                        'mid_term_end': datetime(current_year, 10, 30),
                        'final_term_start': datetime(current_year, 12, 15),
                        'final_term_end': datetime(current_year, 12, 31),
                        'is_active': True
                    }
                )
                if created:
                    print(f"Created default semester for program: {program.name}")
                else:
                    print(f"Semester already exists for program: {program.name}")
            except Exception as e:
                print(f"Error creating default semester for program {program.name}: {e}")
                print(f"Current session: {current_session} (type: {type(current_session)})")
                continue
    
    fake_course_offerings = create_fake_course_offerings()
    
    # Create students and enrollments
    print("\n7. Creating students and enrollments...")
    fake_students = create_fake_students()
    if fake_students:
        print(f"Created {len(fake_students)} students")
        create_fake_student_enrollments()
        create_fake_student_grades()
    else:
        print("No students were created. Check if there are any accepted applicants.")
    
    # Create site elements
    print("\n8. Creating site elements...")
    create_fake_sliders(num_sliders=3)
    create_fake_alumni(num_alumni=8)
    create_fake_gallery_items(num_items=12)
    create_fake_news(num_news=7)
    create_fake_events(num_events=7)
    
    print("\nFake data generation complete.") 