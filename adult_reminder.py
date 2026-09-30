"""
ADULT Decode Reminder System - DAILY REMINDER MODE

Behavior:
- First reminder is sent 1 day before the scheduled date.
- A reminder is sent once per day while the task is not Completed.
- Marking the task Completed stops all future reminders.
- Reminders automatically stop after the scheduled date.
- Run this script once each day using Windows Task Scheduler, GitHub Actions,
  or another scheduler.
"""

import os
import pandas as pd
from outlook_email_adult import send_email

FILE = "ADULT_Decode_Tracker.xlsx"
SHEET = "Decode Tasks"

# Number of days before the due date to start reminders.
# 1 means the first reminder is sent the day before.
REMINDER_DAYS_BEFORE = 1

EMAILS = {
    "Rashid": "rkoroma@emory.edu",
    "Drs. Andrew/Aziz": "amosera@emory.edu;saaziz2@emory.edu",
    "Seyi": "obalog2@emory.edu",
    "Pathology Team": "adaram2@emory.edu",
    "Dr. Bassey": "ibassey@emory.edu",
    "Data Team": "skamar3@emory.edu",
    "SMEs": "skamar3@emory.edu",
}


def get_person_name(assigned_person):
    if assigned_person == "SMEs":
        return "Adult Decode SMEs"

    if "/" in assigned_person:
        first_person = assigned_person.split("/")[0].strip()
        if first_person.startswith("Drs."):
            first_person = (
                "Dr. " + first_person.replace("Drs.", "", 1).strip()
            )
        return first_person

    if "Team" in assigned_person:
        return assigned_person

    return assigned_person


def create_email_body(row):
    person_name = get_person_name(row["ASSIGNED PERSON"])
    activity_date = row["DATE"].strftime("%d %B %Y")
    decode_date = row["DECODE DATE"].strftime("%d %B %Y")

    days_until = (row["DATE"] - pd.Timestamp.today().normalize()).days

    if days_until == 0:
        timing = "This activity is due TODAY."
    elif days_until == 1:
        timing = "This activity is due TOMORROW."
    else:
        timing = f"This activity is due in {days_until} day(s)."

    return f"""Dear {person_name},

This is a reminder from the CHAMPS ADULT Decode Management System.

Activity:
{row['ACTIVITY']}

Assigned Person:
{row['ASSIGNED PERSON']}

Scheduled Date:
{activity_date}

Adult Decode Date:
{decode_date} ({row['DECODE CYCLE']})

Current Status:
{row['STATUS']}

{timing}

Please complete this activity and update its status to "Completed" in the ADULT Decode Management System.

Reminders will continue daily until the activity is marked as Completed, but will automatically stop after the scheduled date.

Best Regards,
CHAMPS Data Management Team
"""


def send_reminders():
    print("=" * 70)
    print("ADULT Decode Reminder System - DAILY REMINDER MODE")
    print("=" * 70)

    if not os.path.exists(FILE):
        print(f"File not found: {FILE}")
        print(f"Current directory: {os.getcwd()}")
        return

    try:
        df = pd.read_excel(FILE, sheet_name=SHEET)
        print(f"Loaded {len(df)} activities from {FILE}")
    except Exception as exc:
        print(f"Error loading tracker: {exc}")
        return

    df["DATE"] = pd.to_datetime(df["DATE"]).dt.normalize()
    df["DECODE DATE"] = pd.to_datetime(df["DECODE DATE"]).dt.normalize()

    # This column records the date of the most recent reminder.
    # It allows the system to send one reminder per day rather than one reminder ever.
    if "LAST REMINDER SENT" not in df.columns:
        df["LAST REMINDER SENT"] = ""

    df["LAST REMINDER SENT"] = (
        df["LAST REMINDER SENT"].fillna("").astype(str)
    )

    today = pd.Timestamp.today().normalize()
    today_text = today.strftime("%Y-%m-%d")

    reminder_start = df["DATE"] - pd.Timedelta(days=REMINDER_DAYS_BEFORE)

    eligible = df[
        (today >= reminder_start)
        & (today <= df["DATE"])
        & (df["STATUS"] != "Completed")
        & (df["LAST REMINDER SENT"] != today_text)
    ].copy()

    print(f"Today: {today_text}")
    print(f"Reminder starts: {REMINDER_DAYS_BEFORE} day(s) before due date")
    print(f"Eligible reminders today: {len(eligible)}")

    if eligible.empty:
        print("No reminders need to be sent today.")
        return

    emails_sent = 0
    failed_emails = 0

    for index, row in eligible.iterrows():
        assigned_person = row["ASSIGNED PERSON"]
        recipient = EMAILS.get(assigned_person, "").strip()

        print("-" * 70)
        print(f"Activity ID: {row.get('ID', 'Task')}")
        print(f"Task: {row['ACTIVITY']}")
        print(f"Assigned to: {assigned_person}")
        print(f"Due date: {row['DATE'].strftime('%d %B %Y')}")
        print(f"Status: {row['STATUS']}")

        if not recipient:
            print(f"No email configured for '{assigned_person}'")
            failed_emails += 1
            continue

        subject = f"ADULT Decode Reminder: {row['ACTIVITY']}"
        body = create_email_body(row)

        try:
            print(f"Sending to: {recipient}")
            send_email(recipient, subject, body)

            df.loc[index, "LAST REMINDER SENT"] = today_text

            # Keep the old column for compatibility with your existing tracker.
            if "REMINDER SENT" in df.columns:
                df.loc[index, "REMINDER SENT"] = "Yes"

            emails_sent += 1
            print("Reminder sent successfully.")

        except Exception as exc:
            failed_emails += 1
            print(f"Failed to send reminder: {exc}")

    if emails_sent > 0:
        try:
            df.to_excel(FILE, sheet_name=SHEET, index=False)
            print(f"Updated tracker: {emails_sent} reminder(s) recorded.")
        except Exception as exc:
            print(f"Error saving tracker: {exc}")

    print("=" * 70)
    print("REMINDER CHECK COMPLETED")
    print(f"Emails sent: {emails_sent}")
    print(f"Failed: {failed_emails}")
    print("=" * 70)


if __name__ == "__main__":
    send_reminders()
