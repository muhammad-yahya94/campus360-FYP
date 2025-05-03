from django.db import models

# ===== 1. Degree Types (Separate Table) =====
class DegreeType(models.Model):
    code = models.CharField(max_length=10, unique=True)  # BS, MS, PhD
    name = models.CharField(max_length=100)              # Bachelor of Science
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# ===== 2. Faculty =====
class Faculty(models.Model):
    name = models.CharField(max_length=100)  # Engineering, Languages
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


# ===== 3. Department =====
class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')  # Added related_name
    name = models.CharField(max_length=100)  # Computer Science
    code = models.CharField(max_length=10)   # CS
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Program(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')  
    name = models.CharField(max_length=100)
    degree_type = models.ForeignKey(DegreeType, on_delete=models.PROTECT)
    duration_years = models.IntegerField()

    def __str__(self):
        return self.name

