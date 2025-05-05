from django.db import models


# ===== 1. Faculty =====
class Faculty(models.Model):
    name = models.CharField(max_length=100)  # e.g., Engineering, Languages
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculties"


# ===== 2. Department =====
class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)  # e.g., Computer Science
    code = models.CharField(max_length=10)   # e.g., CS

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"


# ===== 3. Program =====
class Program(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=100)
    degree_type = models.CharField(max_length=10, help_text='e.g., PhD, MPhil, BS')
    duration_years = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
