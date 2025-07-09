from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('fee_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='semesterfee',
            name='shift',
            field=models.CharField(choices=[('morning', 'Morning'), ('evening', 'Evening')], default='morning', help_text='Select the preferred shift for the students.', max_length=10),
        ),
    ]
