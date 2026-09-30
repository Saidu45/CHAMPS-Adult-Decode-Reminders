# send_test_email.py
from outlook_email_adult import send_email

# Send to yourself
send_email(
    "skamar3@emory.edu",  # Your email
    "[TEST] CHILD Decode Reminder System Test",
    """
    This is a test email from the CHILD Decode Reminder System.
    
    If you received this, the email system is working correctly!
    
    Regards,
    CHAMPS Data Management Team
    """
)
print("✅ Test email sent!")