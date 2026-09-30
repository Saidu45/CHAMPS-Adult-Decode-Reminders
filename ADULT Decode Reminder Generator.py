import pandas as pd
from datetime import datetime, timedelta
import calendar
import os

FILE = "ADULT_Decode_Tracker.xlsx"
SHEET = "Decode Tasks"


def nth_weekday(year, month, weekday, occurrence):
    """Return the nth weekday in a month. Monday=0 ... Sunday=6."""
    date = datetime(year, month, 1)
    days_to_weekday = (weekday - date.weekday()) % 7
    return date + timedelta(days=days_to_weekday + 7 * (occurrence - 1))


def last_weekday(year, month, weekday):
    """Return the last requested weekday in a month. Monday=0 ... Sunday=6."""
    last_day = calendar.monthrange(year, month)[1]
    date = datetime(year, month, last_day)
    while date.weekday() != weekday:
        date -= timedelta(days=1)
    return date


def adult_decode_dates(year, month):
    """Adult Decode occurs on the second Friday and last Friday every month."""
    second_friday = nth_weekday(year, month, weekday=4, occurrence=2)
    last_friday = last_weekday(year, month, weekday=4)
    return [
        ("Second Friday", second_friday),
        ("Last Friday", last_friday),
    ]


def generate_schedule(decode_date):
    """
    Build all activities around one Adult Decode date.

    Interpretation used:
    - Data Team generates case packets 3 weeks before decode.
    - Network Pathology report is requested 6 weeks before case-packet generation,
      therefore 9 weeks (63 days) before decode.
    - Decode-week memo is scheduled for Monday of decode week.
    """
    return [
        {
            "DATE": decode_date - timedelta(days=63),
            "ASSIGNED PERSON": "Rashid",
            "ACTIVITY": "Send request for Network Pathology report",
        },
        {
            "DATE": decode_date - timedelta(days=21),
            "ASSIGNED PERSON": "Data Team",
            "ACTIVITY": "Generate Adult Decode case packets",
        },
        {
            "DATE": decode_date - timedelta(days=14),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Send Adult Decode case packets to SMEs",
        },
        {
            "DATE": decode_date - timedelta(days=4),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Send stakeholder memo for Dr. Ike's signature",
        },
        {
            "DATE": decode_date - timedelta(days=3),
            "ASSIGNED PERSON": "SMEs",
            "ACTIVITY": "SMEs submit Adult Decode reports",
        },
        {
            "DATE": decode_date - timedelta(days=2),
            "ASSIGNED PERSON": "Rashid",
            "ACTIVITY": "Send consensus document to Adult Decode panelists (SMEs)",
        },
        {
            "DATE": decode_date,
            "ASSIGNED PERSON": "Pathology Team",
            "ACTIVITY": "ADULT Decode",
        },
        {
            "DATE": decode_date + timedelta(days=3),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Send Service Completion Form to Dr. Bassey",
        },
        {
            "DATE": decode_date + timedelta(days=3),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Upload Adult Decode report to REDCap",
        },
        {
            "DATE": decode_date + timedelta(days=3),
            "ASSIGNED PERSON": "Drs. Andrew/Aziz",
            "ACTIVITY": "Send Adult Decode results to Surveillance Team",
        },
    ]


def load_existing_progress():
    """Preserve STATUS and REMINDER SENT if the tracker is regenerated."""
    if not os.path.exists(FILE):
        return {}

    try:
        old = pd.read_excel(FILE, sheet_name=SHEET)
        if old.empty:
            return {}

        old["DECODE DATE"] = pd.to_datetime(old["DECODE DATE"]).dt.normalize()
        progress = {}
        for _, row in old.iterrows():
            key = (
                row["DECODE DATE"],
                str(row["DECODE CYCLE"]),
                str(row["ACTIVITY"]),
            )
            progress[key] = {
                "STATUS": row.get("STATUS", "Pending"),
                "REMINDER SENT": row.get("REMINDER SENT", "No"),
            }
        return progress
    except Exception:
        return {}


def build_tracker():
    today = pd.Timestamp.today().normalize()
    current_year = today.year
    existing_progress = load_existing_progress()
    all_tasks = []

    # Generate current year and next year.
    for year in [current_year, current_year + 1]:
        for month in range(1, 13):
            for cycle_name, decode_date in adult_decode_dates(year, month):
                decode_ts = pd.Timestamp(decode_date).normalize()

                for task in generate_schedule(decode_date):
                    task_date = pd.Timestamp(task["DATE"]).normalize()

                    # Keep future activities only. This still retains post-decode
                    # tasks for a decode that has just occurred.
                    if task_date < today:
                        continue

                    key = (decode_ts, cycle_name, task["ACTIVITY"])
                    saved = existing_progress.get(key, {})

                    all_tasks.append(
                        {
                            "DATE": task_date,
                            "YEAR": decode_date.year,
                            "DECODE MONTH": calendar.month_name[decode_date.month],
                            "DECODE CYCLE": cycle_name,
                            "DECODE DATE": decode_ts,
                            "ASSIGNED PERSON": task["ASSIGNED PERSON"],
                            "ACTIVITY": task["ACTIVITY"],
                            "STATUS": saved.get("STATUS", "Pending"),
                            "REMINDER SENT": saved.get("REMINDER SENT", "No"),
                            "LAST REMINDER SENT": saved.get("LAST REMINDER SENT", ""),
                        }
                    )

    df = pd.DataFrame(all_tasks)

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "ID", "DATE", "YEAR", "DECODE MONTH", "DECODE CYCLE",
                "DECODE DATE", "ASSIGNED PERSON", "ACTIVITY", "STATUS",
                "REMINDER SENT", "LAST REMINDER SENT"
            ]
        )
    else:
        df = df.sort_values(["DATE", "DECODE DATE", "ACTIVITY"]).reset_index(drop=True)
        df.insert(0, "ID", range(1, len(df) + 1))

    df.to_excel(FILE, sheet_name=SHEET, index=False)

    print("ADULT Decode Tracker generated successfully")
    print("Decode frequency: second Friday and last Friday of every month")
    print(f"Total future activities: {len(df)}")
    print(f"Tracker file: {os.path.abspath(FILE)}")


if __name__ == "__main__":
    build_tracker()