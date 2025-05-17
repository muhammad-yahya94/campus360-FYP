import os
import django
from faker import Faker
from faker.providers import lorem, internet, phone_number, job
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
import random

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import models
from users.models import CustomUser
from academics.models import Department
from faculty_staff.models import Teacher, DESIGNATION_CHOICES

fake = Faker()

def create_fake_staff_users(num_users):
    print(f'Creating {num_users} fake staff users for teachers...')
    users = []
    existing_staff_count = CustomUser.objects.filter(is_staff=True).count()
    num_to_create = max(0, num_users - existing_staff_count)

    if num_to_create == 0:
        print('Enough staff users already exist.')
        return list(CustomUser.objects.filter(is_staff=True).exclude(teacher_profile__isnull=False))

    print(f'Need to create {num_to_create} new staff users.')

    for i in range(num_to_create):
        try:
            user = CustomUser.objects.create_user(
                email=fake.unique.email(),
                password='password123', # Default password
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                info=fake.sentence(),
                is_staff=True,
                is_superuser=False
            )
            users.append(user)
            print(f'  Created staff user: {user.email}')

            # Add a dummy profile picture
            try:
                # Using fake.image() without size/format for broader compatibility
                profile_picture_content = fake.image()
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

        except IntegrityError:
            print('  Skipping staff user creation due to unique constraint violation (email). ')
            continue

    # Return all staff users who are not already teachers
    return list(CustomUser.objects.filter(is_staff=True).exclude(teacher_profile__isnull=False))


def create_fake_teachers(num_teachers=70):
    print(f'Creating {num_teachers} fake teachers...')
    departments = list(Department.objects.all())
    
    if not departments:
        print('No departments found. Please create some departments first (e.g., run seed_data.py).')
        return []

    # Ensure we have enough staff users who are not already teachers
    available_staff_users = create_fake_staff_users(num_teachers) # Create enough staff users if needed

    if len(available_staff_users) < num_teachers:
        print(f'Warning: Only {len(available_staff_users)} available staff users found. Creating fewer teachers.')
        num_teachers_to_create = len(available_staff_users)
    else:
         num_teachers_to_create = num_teachers
         random.shuffle(available_staff_users) # Shuffle to pick random users

    teachers = []

    for i in range(num_teachers_to_create):
        user = available_staff_users[i]
        department = random.choice(departments)
        designation = random.choice([choice[0] for choice in DESIGNATION_CHOICES])

        try:
            teacher, created = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'department': department,
                    'designation': designation,
                    'contact_no': fake.phone_number(),
                    'qualification': fake.sentence(nb_words=10) + ' in ' + department.name,
                    'hire_date': fake.date_this_decade(),
                    'is_active': True,
                }
            )
            if created:
                teachers.append(teacher)
                print(f'  Created teacher: {teacher.user.full_name} ({teacher.designation})')
            else:
                 print(f'  Teacher already exists for user {user.email}. Skipping.')

        except IntegrityError:
             print(f'  Skipping teacher creation for user {user.email} due to unique constraint.')
             continue

    return teachers

if __name__ == '__main__':
    print("Starting fake teacher data generation...")
    created_teachers = create_fake_teachers(num_teachers=70)
    print(f"Fake teacher data generation complete. Created {len(created_teachers)} teachers.") 