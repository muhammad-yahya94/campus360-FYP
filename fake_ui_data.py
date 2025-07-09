import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

from django.db import models
from faker import Faker
import random
from datetime import timedelta
from django.utils import timezone
from users.models import CustomUser
from announcements.models import News, Event
from site_elements.models import Slider, Alumni, Gallery
from faculty_staff.models import Office, OfficeStaff
from django_ckeditor_5.fields import CKEditor5Field
from autoslug import AutoSlugField


fake = Faker()

def create_fake_users(num_users=5):
    """Create fake CustomUser instances."""
    users = []
    for _ in range(num_users):
        user = CustomUser.objects.create(
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            is_active=True
        )
        user.set_password('password123')
        user.save()
        users.append(user)
    return users

def create_fake_news(num_items=10):
    """Create fake News instances."""
    for _ in range(num_items):
        news = News.objects.create(
            title=fake.sentence(nb_words=6),
            content=fake.paragraphs(nb=3, ext_word_list=None),
            published_date=fake.date_time_between(start_date='-1y', end_date='now'),
            is_published=fake.boolean(chance_of_getting_true=80)
        )
        news.save()

def create_fake_events(num_items=10):
    """Create fake Event instances."""
    for _ in range(num_items):
        start_date = fake.date_time_between(start_date='now', end_date='+1y')
        end_date = start_date + timedelta(hours=random.randint(2, 12))
        event = Event.objects.create(
            title=fake.sentence(nb_words=5),
            description=fake.paragraphs(nb=2, ext_word_list=None),
            event_start_date=start_date,
            event_end_date=end_date,
            location=fake.address().replace('\n', ', '),
            image=f'events/fake_event_image_{random.randint(1, 100)}.jpg',
            created_at=fake.date_between(start_date='-1y', end_date='today')
        )
        event.save()

def create_fake_sliders(num_items=5):
    """Create fake Slider instances."""
    for _ in range(num_items):
        slider = Slider.objects.create(
            title=fake.sentence(nb_words=4),
            image=f'slider/fake_slider_image_{random.randint(1, 100)}.jpg',
            is_active=fake.boolean(chance_of_getting_true=90)
        )
        slider.save()

def create_fake_alumni(num_items=10):
    """Create fake Alumni instances."""
    for _ in range(num_items):
        alumni = Alumni.objects.create(
            name=fake.name(),
            graduation_year=fake.year(),
            profession=fake.job(),
            testimonial=fake.paragraph(nb_sentences=3),
            image=f'alumni/fake_alumni_image_{random.randint(1, 100)}.jpg'
        )
        alumni.save()

def create_fake_gallery(num_items=15):
    """Create fake Gallery instances."""
    for _ in range(num_items):
        gallery = Gallery.objects.create(
            title=fake.sentence(nb_words=4),
            image=f'gallery/fake_gallery_image_{random.randint(1, 100)}.jpg',
            date_added=fake.date_time_between(start_date='-2y', end_date='now')
        )
        gallery.save()

def create_treasure_office():
    """Create Treasure Office and its staff."""
    # Create the Treasure Office
    treasure_office = Office.objects.create(
        name="Treasure Office",
        description="The Treasure Office is responsible for managing all financial transactions, fee collection, and financial records of the institution. We handle student fee payments, staff payroll, budget management, and financial reporting.",
        location="Administrative Building, Ground Floor, Room 101",
        contact_email="treasure@campus360.edu",
        contact_phone="+1-555-0123",
        slug="treasure-office"
    )
    
    # Create staff members for the Treasure Office
    staff_positions = [
        "Treasurer",
        "Assistant Treasurer", 
        "Financial Officer",
        "Accountant",
        "Cashier"
    ]
    
    staff_members = []
    for i, position in enumerate(staff_positions):
        # Create user for staff member
        user = CustomUser.objects.create(
            email=f"treasure.staff{i+1}@campus360.edu",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            is_active=True
        )
        user.set_password('password123')
        user.save()
        
        # Create office staff member
        staff = OfficeStaff.objects.create(
            user=user,
            office=treasure_office,
            position=position,
            contact_no=f"+1-555-{1000+i:04d}"
        )
        staff_members.append(staff)
    
    print(f"Created Treasure Office with {len(staff_members)} staff members")
    return treasure_office, staff_members

def populate_fake_data():
    """Populate all models with fake data."""
    print("Creating fake users...")
    create_fake_users(5)
    print("Creating fake news...")
    create_fake_news(10)
    print("Creating fake events...")
    create_fake_events(10)
    print("Creating fake sliders...")
    create_fake_sliders(5)
    print("Creating fake alumni...")
    create_fake_alumni(10)
    print("Creating fake gallery images...")
    create_fake_gallery(15)
    print("Creating Treasure Office...")
    create_treasure_office()
    print("Fake data population complete.")

if __name__ == "__main__":
    populate_fake_data()