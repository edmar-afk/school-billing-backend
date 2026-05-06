from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Students(models.Model):
    full_name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    grade = models.CharField(max_length=10)
    status = models.TextField(default='Pending')

class Treasurers(models.Model):
    username = models.CharField(
        max_length=100,
        unique=True
    )

    password = models.CharField(
        max_length=128
    )

    full_name = models.CharField(
        max_length=100
    )

    role = models.CharField(
        max_length=50,
        default="pta_treasurer"
    )

    def __str__(self):
        return self.full_name

class Billing(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    payment_status = models.TextField(default='Pending')
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    miscellaneous_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalties = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discounts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_billed = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    date_paid = models.DateTimeField(null=True, blank=True)
    status = models.TextField(default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        tuition = float(self.tuition_fee or 0)
        misc = float(self.miscellaneous_fee or 0)
        penalties = float(self.penalties or 0)
        discounts = float(self.discounts or 0)

        total = tuition + misc + penalties - discounts

        self.total_amount = str(max(total, 0))

        super().save(*args, **kwargs)


class Reports(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE) 
    total_collection = models.TextField()
    exported_file = models.FileField(upload_to='reports/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'xlsx'])])
    

class MailSent(models.Model):
    student_name = models.TextField()
    description = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    
    
