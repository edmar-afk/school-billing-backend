from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Students(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    grade = models.CharField(max_length=10)
    
    


class Billing(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    payment_status = models.TextField(default='Pending')
    tuition_fee = models.TextField()
    miscellaneous_fee = models.TextField()
    penalties = models.TextField()
    discounts = models.TextField()
    total_amount = models.TextField()
    date_billed = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    date_paid = models.DateTimeField(null=True, blank=True)
    

class Reports(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE) 
    total_collection = models.TextField()
    exported_file = models.FileField(upload_to='reports/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx'])])
    

class MailSent(models.Model):
    student_name = models.TextField()
    description = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)