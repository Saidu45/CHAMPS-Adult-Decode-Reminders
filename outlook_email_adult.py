import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv


# ------------------------------------
# Load Environment Variables
# ------------------------------------

load_dotenv()

SENDER_EMAIL = os.getenv("GMAIL_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# ------------------------------------
# Send Email
# ------------------------------------

def send_email(recipients, subject, body):

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL

    # Split multiple recipients separated by ;
    email_list = [
        email.strip()
        for email in recipients.split(";")
        if email.strip()
    ]

    msg["To"] = ", ".join(email_list)

    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp: 

        smtp.starttls()

        smtp.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        smtp.send_message(msg)

    print(f"Email sent to: {', '.join(email_list)}")