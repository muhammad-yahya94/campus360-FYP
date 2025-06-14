# Detailed Model Relationships with Fields

## Core Models
- **User**
  - username (CharField)
  - email (EmailField)
  - password (CharField)
  - is_active (BooleanField)
  - is_staff (BooleanField)
  - is_superuser (BooleanField)
  - date_joined (DateTimeField)

- **Profile**
  - user (OneToOneField)
  - bio (TextField)
  - profile_picture (ImageField)
  - contact_number (CharField)
  - address (TextField)

- **Role**
  - name (CharField)
  - description (TextField)
  - permissions (ManyToManyField)

## Academics Models
- **Department**
  - name (CharField)
  - code (CharField)
  - description (TextField)
  - head (ForeignKey -> Teacher)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)

- **Program**
  - name (CharField)
  - department (ForeignKey -> Department)
  - duration (IntegerField)
  - description (TextField)
  - eligibility_criteria (TextField)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)

- **Course**
  - code (CharField)
  - title (CharField)
  - credits (IntegerField)
  - description (TextField)
  - prerequisites (ManyToManyField -> Course)
  - department (ForeignKey -> Department)
  - semester (IntegerField)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)

- **Semester**
  - name (CharField)
  - start_date (DateField)
  - end_date (DateField)
  - academic_year (CharField)
  - status (CharField)

## Faculty & Staff Models
- **Teacher**
  - user (OneToOneField -> CustomUser)
  - department (ForeignKey -> Department)
  - designation (CharField)
  - contact_no (CharField)
  - qualification (TextField)
  - hire_date (DateField)
  - is_active (BooleanField)
  - linkedin_url (URLField)
  - twitter_url (URLField)
  - personal_website (URLField)
  - experience (TextField)

- **Office**
  - name (CharField)
  - description (TextField)
  - image (ImageField)
  - location (CharField)
  - contact_email (EmailField)
  - contact_phone (CharField)
  - slug (SlugField)

- **OfficeStaff**
  - user (OneToOneField -> CustomUser)
  - office (ForeignKey -> Office)
  - position (CharField)
  - contact_no (CharField)

## Students Models
- **Student**
  - user (OneToOneField -> CustomUser)
  - student_id (CharField)
  - admission_date (DateField)
  - program (ForeignKey -> Program)
  - current_semester (IntegerField)
  - cgpa (DecimalField)
  - status (CharField)

- **StudentProfile**
  - student (OneToOneField -> Student)
  - date_of_birth (DateField)
  - gender (CharField)
  - nationality (CharField)
  - emergency_contact (CharField)
  - address (TextField)

- **Enrollment**
  - student (ForeignKey -> Student)
  - course (ForeignKey -> Course)
  - semester (ForeignKey -> Semester)
  - grade (CharField)
  - status (CharField)

## Courses Models
- **CourseMaterial**
  - course (ForeignKey -> Course)
  - title (CharField)
  - description (TextField)
  - file (FileField)
  - upload_date (DateTimeField)
  - created_by (ForeignKey -> Teacher)

- **Assignment**
  - course (ForeignKey -> Course)
  - title (CharField)
  - description (TextField)
  - due_date (DateTimeField)
  - total_marks (IntegerField)
  - created_by (ForeignKey -> Teacher)

- **Quiz**
  - course (ForeignKey -> Course)
  - title (CharField)
  - description (TextField)
  - start_time (DateTimeField)
  - end_time (DateTimeField)
  - total_marks (IntegerField)
  - created_by (ForeignKey -> Teacher)

- **Grade**
  - student (ForeignKey -> Student)
  - course (ForeignKey -> Course)
  - assignment (ForeignKey -> Assignment)
  - quiz (ForeignKey -> Quiz)
  - marks_obtained (IntegerField)
  - grade (CharField)
  - semester (ForeignKey -> Semester)

## Learning Cycle Models
- **LearningActivity**
  - course (ForeignKey -> Course)
  - title (CharField)
  - description (TextField)
  - date (DateTimeField)
  - duration (IntegerField)
  - teacher (ForeignKey -> Teacher)

- **Assessment**
  - student (ForeignKey -> Student)
  - activity (ForeignKey -> LearningActivity)
  - grade (CharField)
  - feedback (TextField)
  - date (DateTimeField)

- **Feedback**
  - student (ForeignKey -> Student)
  - course (ForeignKey -> Course)
  - teacher (ForeignKey -> Teacher)
  - feedback_text (TextField)
  - date (DateTimeField)

- **Progress**
  - student (ForeignKey -> Student)
  - course (ForeignKey -> Course)
  - percentage_complete (DecimalField)
  - last_updated (DateTimeField)

## Payment Models
- **FeeStructure**
  - program (ForeignKey -> Program)
  - semester (ForeignKey -> Semester)
  - amount (DecimalField)
  - due_date (DateField)
  - description (TextField)

- **Payment**
  - student (ForeignKey -> Student)
  - fee_structure (ForeignKey -> FeeStructure)
  - amount_paid (DecimalField)
  - payment_date (DateField)
  - payment_method (CharField)
  - status (CharField)

- **Invoice**
  - student (ForeignKey -> Student)
  - fee_structure (ForeignKey -> FeeStructure)
  - amount (DecimalField)
  - due_date (DateField)
  - status (CharField)
  - created_at (DateTimeField)

- **Transaction**
  - payment (ForeignKey -> Payment)
  - invoice (ForeignKey -> Invoice)
  - amount (DecimalField)
  - transaction_date (DateTimeField)
  - status (CharField)
  - reference_number (CharField)

## Site Elements Models
- **Page**
  - title (CharField)
  - content (TextField)
  - slug (SlugField)
  - status (CharField)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)

- **Banner**
  - title (CharField)
  - image (ImageField)
  - link (URLField)
  - status (CharField)
  - created_at (DateTimeField)

- **Menu**
  - title (CharField)
  - url (CharField)
  - parent (ForeignKey -> self)
  - order (IntegerField)
  - status (CharField)

- **Footer**
  - content (TextField)
  - copyright_text (CharField)
  - social_links (TextField)
  - contact_info (TextField)

## Admissions Models
- **Application**
  - applicant (ForeignKey -> Applicant)
  - program (ForeignKey -> Program)
  - academic_session (ForeignKey -> AcademicSession)
  - status (CharField)
  - application_date (DateTimeField)
  - documents (ManyToManyField -> Document)

- **AdmissionTest**
  - application (ForeignKey -> Application)
  - test_date (DateTimeField)
  - test_type (CharField)
  - score (IntegerField)
  - status (CharField)

- **AdmissionStatus**
  - application (OneToOneField -> Application)
  - current_status (CharField)
  - remarks (TextField)
  - updated_at (DateTimeField)

## Announcements Models
- **Announcement**
  - title (CharField)
  - content (TextField)
  - created_by (ForeignKey -> Teacher)
  - created_at (DateTimeField)
  - expiry_date (DateTimeField)
  - is_active (BooleanField)

- **Notification**
  - announcement (ForeignKey -> Announcement)
  - recipient (ForeignKey -> CustomUser)
  - read_status (BooleanField)
  - created_at (DateTimeField)

- **Event**
  - title (CharField)
  - description (TextField)
  - start_date (DateTimeField)
  - end_date (DateTimeField)
  - location (CharField)
  - is_active (BooleanField)

## Users Models
- **CustomUser**
  - username (CharField)
  - email (EmailField)
  - password (CharField)
  - first_name (CharField)
  - last_name (CharField)
  - is_active (BooleanField)
  - is_staff (BooleanField)
  - date_joined (DateTimeField)

- **UserPermission**
  - user (ForeignKey -> CustomUser)
  - permission (CharField)
  - description (TextField)

- **UserGroup**
  - name (CharField)
  - description (TextField)
  - permissions (ManyToManyField -> Permission)

Note: This is a comprehensive overview of all models and their fields. Each model's fields are listed with their field type and relationships to other models are shown using ForeignKey and ManyToManyField relationships.
