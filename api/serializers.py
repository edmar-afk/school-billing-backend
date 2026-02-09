# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import models
from .models import Students, Billing, MailSent
from django.core.mail import send_mail
from django.conf import settings


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ["id", "full_name", "email", "grade"]
        


class BillingSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Students.objects.all(),
        source="student",
        write_only=True
    )

    class Meta:
        model = Billing
        fields = [
            "id",
            "student",
            "student_id",
            "payment_status",
            "tuition_fee",
            "miscellaneous_fee",
            "penalties",
            "discounts",
            "total_amount",
            "date_billed",
            "payment_method",
            "date_paid",
        ]


class BillingCreateSerializer(serializers.ModelSerializer):
     class Meta:
        model = Billing
        fields = [
            "id",
            "student",
            "payment_status",
            "tuition_fee",
            "miscellaneous_fee",
            "penalties",
            "discounts",
            "total_amount"
        ]


class MailSentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailSent
        fields = ['id', 'student_name', 'description', 'date_sent']
        
        
        



class BillingExcelSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name')
    grade = serializers.CharField(source='student.grade')
    date_billed = serializers.SerializerMethodField()
    date_paid = serializers.SerializerMethodField()

    class Meta:
        model = Billing
        fields = [
            'student_name',
            'grade',
            'payment_status',
            'tuition_fee',
            'miscellaneous_fee',
            'penalties',
            'discounts',
            'total_amount',
            'payment_method',
            'date_billed',
            'date_paid',
        ]

    def get_date_billed(self, obj):
        return obj.date_billed.strftime('%b. %d, %Y') if obj.date_billed else ''

    def get_date_paid(self, obj):
        return obj.date_paid.strftime('%b %d, %Y - %I:%M%p').lower() if obj.date_paid else ''
    


class BillingActivitySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name')
    grade = serializers.CharField(source='student.grade')

    class Meta:
        model = Billing
        fields = [
            'student_name',
            'grade',
            'total_amount',
            'date_billed',
            'date_paid',
        ]
