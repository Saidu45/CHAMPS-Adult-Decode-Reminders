from outlook_email_adult import send_email


recipient = "skamar3@emory.edu"


subject = "CHILD Decode Test Email"


body = """
Hello,

This is a test email from the CHAMPS CHILD Decode Reminder System.

If you received this message, the email automation is working correctly.

Regards,
CHAMPS Data Management Team
"""


try:

    send_email(
        recipient,
        subject,
        body
    )

    print("Test email sent successfully")

except Exception as e:

    print("Email failed")
    print(e)