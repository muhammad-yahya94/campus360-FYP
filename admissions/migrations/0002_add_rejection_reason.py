from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicant',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True, help_text='Reason for rejection if application is rejected.'),
        ),
    ]
