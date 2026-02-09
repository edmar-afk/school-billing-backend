# utils.py
import qrcode
from io import BytesIO
from django.core.files import File

def generate_qr_code(user, pension_status):
    qr_data = f"Name: {user.first_name} {user.last_name}\n"
    qr_data += f"Mobile: {user.profile.mobile_num}\n"
    qr_data += f"Address: {user.profile.address}\n"
    qr_data += f"Pension Status: {pension_status.status}\n"
    qr_data += f"Date Submitted: {pension_status.date_submitted.strftime('%Y-%m-%d')}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return File(buffer, name=f"{user.username}_qr_code.png")
