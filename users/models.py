from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, first_name='', **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,  first_name=first_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, first_name='', **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
  
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, first_name, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = PhoneNumberField(blank=True, null=True, region='PK')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    info = models.TextField(max_length=400, blank=True, null=True, help_text="Bio or related information")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is the primary identifier

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'



class Role(models.Model):
    ROLE_CHOICES_Admin = [
        ("HOD", "Head of department"),
        ("LA", "Lab Assistant"),
        ("Lib", "Librarian"),
        ("CL", "Clerk"),
        ("GD", "Gaurds"),
        ("Gdr", "Gardener"),
        ("OTH", "Other"),
    ]
    
    ROLE_CHOICES_HOD = [
        ("Prof", "Professors"),
        ("Std", "Students"),
        ("LA", "Lab Assistant"),
        ("Lib", "Librarian"),
        ('GD','Gaurds'),
        ("Gdr", "Gardener"),
        ("OTH", "Other"),
    ]
    
            
    desc = models.TextField()
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='role')  
    admin_role_choices = models.CharField(max_length=50, choices=ROLE_CHOICES_Admin, blank=True , null=True)
    hod_role_choices = models.CharField(max_length=50, choices=ROLE_CHOICES_HOD, blank=True , null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.admin_role_choices} - {self.hod_role_choices} - {self.created_at}"


