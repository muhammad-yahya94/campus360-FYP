import os
import django
import random
from faker import Faker
from django.utils import timezone
from django.core.exceptions import ValidationError
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
try:
    django.setup()
    from academics.models import Department
    from faculty_staff.models import Teacher, TeacherDetails
    from users.models import CustomUser
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

fake = Faker()

def update_existing_teachers():
    teachers = Teacher.objects.all()
    if not teachers.exists():
        print("No existing teachers found. Please create teachers first.")
        return []

    updated_teachers = []
    for teacher in teachers:
        try:
            # Update new fields if they are blank or null
            if not teacher.linkedin_url:
                teacher.linkedin_url = fake.url() if random.choice([True, False]) else None
            if not teacher.twitter_url:
                teacher.twitter_url = fake.url() if random.choice([True, False]) else None
            if not teacher.personal_website:
                teacher.personal_website = fake.url() if random.choice([True, False]) else None
            if not teacher.experience:
                teacher.experience = fake.text(max_nb_chars=300)
            teacher.save()
            updated_teachers.append(teacher)
        except Exception as e:
            print(f"Error updating teacher {teacher.user.get_full_name()}: {e}")
    print(f"Updated {len(updated_teachers)} teachers with new fields")
    return updated_teachers

def create_teacher_details(teachers):
    existing_details = TeacherDetails.objects.count()
    expected_details = len(teachers)
    if existing_details >= expected_details:
        print(f"Skipping TeacherDetails creation: {existing_details} details already exist")
        return list(TeacherDetails.objects.all())
    
    details_list = []
    employment_types = ['visitor', 'contract', 'permanent']
    status_choices = ['on_break', 'on_lecture', 'on_leave', 'available']
    
    for teacher in teachers:
        if not hasattr(teacher, 'details'):
            try:
                employment_type = random.choice(employment_types)
                salary_per_lecture = random.uniform(500.00, 800.00) if employment_type in ['visitor', 'contract'] else None
                fixed_salary = random.uniform(50000.00, 150000.00) if employment_type == 'permanent' else None
                detail = TeacherDetails.objects.create(
                    teacher=teacher,
                    employment_type=employment_type,
                    salary_per_lecture=salary_per_lecture,
                    fixed_salary=fixed_salary,
                    status=random.choice(status_choices),
                    last_updated=timezone.now()
                )
                details_list.append(detail)
            except Exception as e:
                print(f"Error creating TeacherDetails for {teacher.user.get_full_name()}: {e}")
    
    print(f"Created {len(details_list)} new TeacherDetails records")
    return list(TeacherDetails.objects.all())

def main():
    print("Updating teacher data and creating TeacherDetails...")
    
    # Update existing teachers with new fields
    teachers = update_existing_teachers()
    print(f"Total teachers processed: {len(teachers)}")
    
    # Create TeacherDetails for each teacher
    teacher_details = create_teacher_details(teachers)
    print(f"Total TeacherDetails records: {len(teacher_details)}")
    
    print("Teacher data update and TeacherDetails creation completed!")

if __name__ == "__main__":
    main()