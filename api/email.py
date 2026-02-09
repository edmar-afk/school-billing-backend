from django.core.mail import send_mail
from django.conf import settings

def send_simple_email(subject, message, to_emails):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        to_emails,
        fail_silently=False,
    )
