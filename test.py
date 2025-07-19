import os
import django
from faker import Faker
from django.utils import timezone
from django.db import transaction, IntegrityError
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('faker.factory').setLevel(logging.ERROR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

from users.models import CustomUser

fake = Faker()

def create_test_user():
    email = f"test.user@{fake.domain_name()}"
    if CustomUser.objects.filter(email=email).exists():
        logger.debug(f"Skipping existing user: {email}")
        return CustomUser.objects.get(email=email)
    try:
        user = CustomUser(
            email=email,
            first_name="Test",
            last_name="User",
            is_active=True,
            date_joined=timezone.now()
        )
        user.set_password('password123')
        user.save()
        logger.debug(f"Created user: {email}")
        return user
    except IntegrityError:
        logger.warning(f"Skipping user {email} due to conflict")
        return None

def test_data_insertion():
    try:
        with transaction.atomic():
            user = create_test_user()
            if user:
                print(f"User created or found: {user.email}")
                logger.debug(f"User created or found: {user.email}")
            else:
                print("Failed to create or find user")
                logger.error("Failed to create or find user")
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Error: {str(e)}")

if __name__ == '__main__':
    test_data_insertion()
    print("Test data insertion completed!")
    logger.info("Test data insertion completed")