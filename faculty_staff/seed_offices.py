import os
import django
from faker import Faker
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

from faculty_staff.models import Office, OfficeStaff
from users.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()
fake = Faker()

def create_fake_offices(num_offices=5):
    print(f'Creating {num_offices} fake offices...')
    for _ in range(num_offices):
        name = fake.unique.job() + ' Office'
        description = fake.paragraph(nb_sentences=5)
        location = fake.address()
        contact_email = fake.unique.email()
        contact_phone = fake.phone_number()

        # Create a dummy image file
        image_content = fake.image(size=(800, 600), format='jpeg')
        image_file = SimpleUploadedFile(
            name=f'{slugify(name)}.jpg',
            content=image_content,
            content_type='image/jpeg'
        )

        office, created = Office.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'image': image_file,
                'location': location,
                'contact_email': contact_email,
                'contact_phone': contact_phone,
            }
        )
        if created:
            print(f'Created office: {office.name}')

def create_fake_office_staff(num_staff_per_office=3):
    print(f'Creating fake office staff...')
    offices = Office.objects.all()
    if not offices.exists():
        print('No offices found. Please create some offices first.')
        return

    for office in offices:
        print(f'\nAdding staff to {office.name}...')
        for i in range(num_staff_per_office):
            # Create a fake user for the staff member
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()
            password = fake.password()

            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_staff': True, # Office staff might have admin access
                    'is_active': True,
                }
            )
            if user_created:
                 user.set_password(password)
                 user.save()
                 print(f'  Created user: {user.email}')

            # Create a dummy profile picture
            profile_picture_content = fake.image(size=(200, 200), format='jpeg')
            profile_picture_file = SimpleUploadedFile(
                name=f'{slugify(user.email)}_profile.jpg',
                content=profile_picture_content,
                content_type='image/jpeg'
            )
            user.profile_picture = profile_picture_file
            user.save()

            position = fake.job()
            contact_no = fake.phone_number()

            officestaff, created = OfficeStaff.objects.get_or_create(
                user=user,
                office=office,
                defaults={
                    'position': position,
                    'contact_no': contact_no,
                }
            )
            if created:
                print(f'  Created staff: {officestaff.user.get_full_name() or officestaff.user.first_name} in {office.name}')

if __name__ == '__main__':
    print('Seeding database with fake office data...')
    create_fake_offices()
    create_fake_office_staff()
    print('Seeding complete.') 