from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from .serializers import StudentSerializer, BillingSerializer, BillingCreateSerializer, BillingActivitySerializer, TreasurerSerializer
from .models import Students, Billing, MailSent, Treasurers
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
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from datetime import timedelta

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
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        tuition_fee = request.data.get("tuition_fee", 0)
        miscellaneous_fee = request.data.get("miscellaneous_fee", 0)
        penalties = request.data.get("penalties", 0)
        discounts = request.data.get("discounts", 0)
        payment_method = request.data.get("payment_method", "Not Set")
        grades = request.data.get("grades", [])

        total_amount = (
            float(tuition_fee)
            + float(miscellaneous_fee)
            + float(penalties)
            - float(discounts)
        )

        billed_student_ids = Billing.objects.values_list(
            "student_id",
            flat=True,
        )

        students = (
            Students.objects.filter(
                grade__in=grades,
            )
            .exclude(status__iexact="Pending")
            .exclude(id__in=billed_student_ids)
        )

        billings = [
            Billing(
                student=student,
                tuition_fee=tuition_fee,
                miscellaneous_fee=miscellaneous_fee,
                penalties=penalties,
                discounts=discounts,
                total_amount=total_amount,
                payment_method=payment_method,
                payment_status="Pending",
                status="Pending",
            )
            for student in students
        ]

        Billing.objects.bulk_create(billings)

        pending_students = Students.objects.filter(
            grade__in=grades,
            status__iexact="Pending",
        ).count()

        already_billed_students = Students.objects.filter(
            grade__in=grades,
            id__in=billed_student_ids,
        ).count()

        return Response(
            {
                "message": f"{len(billings)} billing records created.",
                "excluded_pending_students": pending_students,
                "excluded_already_billed_students": already_billed_students,
            },
            status=status.HTTP_201_CREATED,
        )
    

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
        return Billing.objects.filter(payment_status='Paid').select_related('student')
    
    
class BillingDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [AllowAny]
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    lookup_field = "id"

    def perform_update(self, serializer):
        old_billing = Billing.objects.get(pk=serializer.instance.pk)

        old_total = (
            Decimal(old_billing.tuition_fee) +
            Decimal(old_billing.miscellaneous_fee) +
            Decimal(old_billing.penalties) -
            Decimal(old_billing.discounts)
        )

        instance = serializer.save()

        new_total = (
            Decimal(instance.tuition_fee) +
            Decimal(instance.miscellaneous_fee) +
            Decimal(instance.penalties) -
            Decimal(instance.discounts)
        )

        paid_amount = old_total - new_total

        student = instance.student

        if instance.payment_status == "Paid":
            subject = "Payment Completed"

            message = (
                f"Hello {student.full_name},\n\n"
                f"Your payment has been fully received.\n\n"
                f"Amount Paid: {paid_amount:.2f}\n"
                f"TOTAL AMOUNT: {new_total:.2f} remaining\n"
                f"Payment Status: {instance.payment_status}\n"
                f"Date Paid: {instance.date_paid}\n\n"
                f"Thank you."
            )

        else:
            subject = "Partial Payment Received"

            message = (
                f"Hello {student.full_name},\n\n"
                f"We received your payment.\n\n"
                f"Amount Paid: {paid_amount:.2f}\n"
                f"TOTAL AMOUNT: {new_total:.2f} remaining\n"
                f"Payment Status: {instance.payment_status}\n\n"
                f"Please complete your remaining balance.\n\n"
                f"Thank you."
            )

        print("\n========== EMAIL PREVIEW ==========")
        print("TO:", student.email)
        print("SUBJECT:", subject)
        print("MESSAGE:")
        print(message)
        print("===================================\n")

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student.email],
            fail_silently=False,
        )
    
    
class UpdateStudentStatusView(APIView):
    permission_classes = [AllowAny]
    def patch(self, request, pk):
        try:
            student = Students.objects.get(pk=pk)
        except Students.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Status is required"}, status=400)

        student.status = new_status
        student.save()

        return Response({"status": student.status})
    
    
class UpdateBillingStatusView(APIView):
    permission_classes = [AllowAny]
    def patch(self, request, pk):
        try:
            billing = Billing.objects.get(pk=pk)
        except Billing.DoesNotExist:
            return Response({"error": "Billing not found"}, status=404)

        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Status is required"}, status=400)

        billing.status = new_status
        billing.save()

        return Response({"status": billing.status})
    

class SendBillingRemindersView(View):
    def get(self, request):

        today = timezone.now().date()

        billings = Billing.objects.filter(
            payment_status="Pending",
            email_sent=False
        )

        sent = []

        for billing in billings:
            due_date = billing.date_billed + timedelta(days=7)
            days_left = (due_date - today).days

            if days_left < 1:
                continue

            if days_left > 7:
                continue

            send_mail(
                subject=f"Precious Gems Elementary School Billing Reminder - {days_left} Day(s) Left",
                message="",
                html_message=f"""
                <div style="font-family: Arial, sans-serif; background:#f5f7fb; padding:20px;">
                    <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:10px; border:1px solid #eee;">

                        <h2 style="color:#2c3e50;">Payment Reminder</h2>

                        <p style="font-size:16px; color:#333;">
                            Hello <b>{billing.student.full_name}</b>,
                        </p>

                        <p style="font-size:15px; color:#444;">
                            You have <b style="color:#e67e22;">{days_left} day(s) left</b> to pay your billing balance.
                        </p>

                        <div style="background:#f1f1f1; padding:15px; border-radius:8px; margin:15px 0;">
                            <p style="margin:0; font-size:15px;">
                                <b>Total Balance:</b> ₱{billing.total_amount}
                            </p>
                            <p style="margin:0; font-size:15px;">
                                <b>Date Billed:</b> {billing.date_billed}
                            </p>
                            <p style="margin:0; font-size:15px;">
                                <b>Due Date:</b> {due_date}
                            </p>
                            <p style="margin:0; font-size:15px;">
                                <b>Status:</b> {billing.payment_status}
                            </p>
                        </div>

                        <p style="font-size:14px; color:#555;">
                            Please settle your payment to avoid inconvenience.
                        </p>

                        <div style="text-align:center; margin-top:20px;">
                            <span style="display:inline-block; padding:10px 20px; background:#3498db; color:white; border-radius:5px;">
                                Thank you for your cooperation
                            </span>
                        </div>

                    </div>
                </div>
                """,
                from_email=None,
                recipient_list=[billing.student.email],
                fail_silently=False
            )

            billing.email_sent = True
            billing.save()

            sent.append(billing.student.email)

        return JsonResponse({
            "sent_count": len(sent),
            "sent_to": sent
        })
        
        
        


class NotifyStudentsByGradeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, grade):
        billings = Billing.objects.filter(
            student__grade=grade,
            payment_status="Pending"
        ).select_related("student")

        sent_count = 0

        for billing in billings:
            student = billing.student

            message = f"""
Hello {student.full_name} from grade {student.grade},

This is a billing reminder.

You currently have an unpaid balance.

Billing Details:

Tuition Fee: {billing.tuition_fee}
Miscellaneous Fee: {billing.miscellaneous_fee}
Penalties: {billing.penalties}

TOTAL AMOUNT: {billing.total_amount}

Payment Status: {billing.payment_status}

Please settle your balance on time.

Thank you.
"""

            send_mail(
                subject="School Billing Reminder",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=False,
            )

            sent_count += 1

        return JsonResponse({
            "message": "Notifications sent successfully",
            "grade": grade,
            "emails_sent": sent_count
        })
        


class TreasurerCreateView(generics.CreateAPIView):
    queryset = Treasurers.objects.all()
    serializer_class = TreasurerSerializer
    permission_classes = [AllowAny]
        
class TreasurerListView(generics.ListAPIView):
    queryset = Treasurers.objects.all()
    serializer_class = TreasurerSerializer
    permission_classes = [AllowAny]


class TreasurerUpdateView(generics.UpdateAPIView):
    queryset = Treasurers.objects.all()
    serializer_class = TreasurerSerializer
    permission_classes = [AllowAny]


class TreasurerDeleteView(generics.DestroyAPIView):
    queryset = Treasurers.objects.all()
    serializer_class = TreasurerSerializer
    permission_classes = [AllowAny]
    
    
