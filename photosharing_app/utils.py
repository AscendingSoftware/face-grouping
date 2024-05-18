import smtplib
from email.message import EmailMessage
from django.conf import settings

def send_notification(email, notification):
    msg = f'{notification} is your notification.'
    email_sender = "ascendingfacegrouping@gmail.com"  # Update with your email
    email_password = 'vofd ytfs tmah ewkh'  # Update with your email password
    email_receiver = email

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = "Notification for Photosharing"
    em.set_content(msg)

    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(email_sender, email_password)
        smtp.send_message(em)
        return True
    except Exception as e:
        print("Error sending notification:", e)
        return False
    
    