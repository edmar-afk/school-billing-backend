from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from .serializers import StudentSerializer, BillingSerializer, BillingCreateSerializer, BillingActivitySerializer
from .models import Students, Billing, MailSent
from rest_framework import generics
from rest_framework.generics import RetrieveUpdateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.db.models import Sum
from .serializers import BillingExcelSerializer
from openpyxl import Workbook # type: ignore
from django.http import HttpResponse
from rest_framework.generics import ListAPIView


class BillingExcelExportView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        billings = Billing.objects.select_related('student')
        serializer = BillingExcelSerializer(billings, many=True)

        wb = Workbook()
        ws = wb.active
        ws.title = 'Billing Report'

        if serializer.data:
            raw_headers = serializer.data[0].keys()
            headers = [h.replace('_', ' ').title() for h in raw_headers]
            ws.append(headers)

            for row in serializer.data:
                ws.append(list(row.values()))

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=billing_report.xlsx'

        wb.save(response)
        return response
class SendBillingEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, billing_id):
        try:
            billing = Billing.objects.select_related("student").get(id=billing_id)
        except Billing.DoesNotExist:
            return Response(
                {"detail": "Billing record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        student = billing.student

        def to_decimal(value):
            try:
                return Decimal(value)
            except (InvalidOperation, TypeError):
                return Decimal("0")

        tuition_fee = to_decimal(billing.tuition_fee)
        miscellaneous_fee = to_decimal(billing.miscellaneous_fee)
        penalties = to_decimal(billing.penalties)
        discounts = to_decimal(billing.discounts)

        total_amount = tuition_fee + miscellaneous_fee + penalties - discounts
        billing.total_amount = str(total_amount)
        billing.save(update_fields=["total_amount"])

        # Message to send to student (exclude date_paid)
        subject = "Billing Statement"
        message = (
            f"Hello {student.full_name},\n\n"
            f"Here is your billing summary:\n\n"
            f"Tuition Fee: {tuition_fee}\n"
            f"Miscellaneous Fee: {miscellaneous_fee}\n"
            f"Penalties: {penalties}\n"
            f"Discounts: {discounts}\n"
            f"--------------------------\n"
            f"TOTAL AMOUNT: {total_amount}\n\n"
            f"Date Billed: {billing.date_billed}\n"
            f"Payment Status: {billing.payment_status}\n\n"
            f"Please settle your payment on or before the due date.\n\n"
            f"Thank you."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=False,
        )

        # Description for MailSent (include date_paid)
        description_for_record = (
            f"{message}\n\n"
            f"Date Paid: {billing.date_paid}"
        )

        MailSent.objects.create(
            student_name=student.full_name,
            description=description_for_record
        )

        return Response(
            {
                "detail": "Billing email sent successfully",
                "billing_id": billing.id,
                "total_amount": str(total_amount),
            },
            status=status.HTTP_200_OK
        )

class StudentListView(generics.ListAPIView):
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]

class StudentCreateView(CreateAPIView):
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]


class StudentListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    
    
class StudentUpdateView(UpdateAPIView):
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"
    
    
class StudentDeleteView(DestroyAPIView):
    permission_classes = [AllowAny]
    queryset = Students.objects.all()
    serializer_class = StudentSerializer
    lookup_field = "id"
    
    
    

class BillingCreateView(generics.CreateAPIView):
    queryset = Billing.objects.all()
    serializer_class = BillingCreateSerializer
    permission_classes = [AllowAny]
    

class BillingLists(generics.ListAPIView):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [AllowAny]
    


class BillingPaymentUpdateView(UpdateAPIView):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def get_serializer(self, *args, **kwargs):
        kwargs["partial"] = True
        return super().get_serializer(*args, **kwargs)
    
    
class BillingDeleteView(DestroyAPIView):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"
    
    
class StudentCountView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        count = Students.objects.count()
        return Response(
            {"student_count": count},
            status=status.HTTP_200_OK
        )
        
        
class TotalPaidAmountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        total = Billing.objects.filter(payment_status="Paid").aggregate(
            total_paid=Sum("total_amount")
        )["total_paid"] or 0

        return Response({
            "payment_status": "Paid",
            "total_amount": total
        })
        
        
class MailSentCountView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        total_count = MailSent.objects.count()
        return Response({'total_emails_sent': total_count})


class PaidBillingListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = BillingActivitySerializer

    def get_queryset(self):
        return Billing.objects.filter(payment_status='Paid').select_related('student').first()