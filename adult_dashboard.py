import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime, timedelta

FILE = "ADULT_Decode_Tracker.xlsx"
SHEET = "Decode Tasks"

st.set_page_config(
    page_title="ADULT Decode Management",
    page_icon="🧬",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color:#f8fafc; }
    .header {
        background-color:#0f766e;
        padding:20px;
        border-radius:12px;
        color:white;
        margin-bottom:20px;
    }
    .card {
        background:white;
        padding:15px;
        border-radius:10px;
        border:1px solid #e5e7eb;
        text-align:center;
    }
    .card-title { font-size:14px; color:#64748b; }
    .card-value { font-size:30px; font-weight:bold; color:#0f172a; }
    </style>
    """,
    unsafe_allow_html=True,
)


def nth_weekday(year, month, weekday, occurrence):
    date = datetime(year, month, 1)
    days_to_weekday = (weekday - date.weekday()) % 7
    return date + timedelta(days=days_to_weekday + 7 * (occurrence - 1))


def last_weekday(year, month, weekday):
    last_day = calendar.monthrange(year, month)[1]
    date = datetime(year, month, last_day)
    while date.weekday() != weekday:
        date -= timedelta(days=1)
    return date


def adult_decode_dates(year, month):
    return [
        ("Second Friday", pd.Timestamp(nth_weekday(year, month, 4, 2))),
        ("Last Friday", pd.Timestamp(last_weekday(year, month, 4))),
    ]


def get_next_decode():
    today = pd.Timestamp.today().normalize()

    candidates = []
    for month_offset in range(0, 14):
        total_month = today.month - 1 + month_offset
        year = today.year + total_month // 12
        month = total_month % 12 + 1

        for cycle_name, decode_date in adult_decode_dates(year, month):
            decode_date = decode_date.normalize()
            if decode_date >= today:
                candidates.append((decode_date, cycle_name))

    if not candidates:
        return None, None

    return min(candidates, key=lambda item: item[0])


@st.cache_data
def load_data():
    if not os.path.exists(FILE):
        st.error(
            "ADULT_Decode_Tracker.xlsx not found. Run 'ADULT Decode Reminder Generator.py' first."
        )
        st.stop()

    df = pd.read_excel(FILE, sheet_name=SHEET)
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["DECODE DATE"] = pd.to_datetime(df["DECODE DATE"])
    if "LAST REMINDER SENT" not in df.columns:
        df["LAST REMINDER SENT"] = ""
    return df


df = load_data()
today = pd.Timestamp.today().normalize()

st.markdown(
    """
    <div class="header">
        <h1>ADULT Decode Management Dashboard</h1>
        <p>CHAMPS Adult Decode Activity Monitoring System</p>
    </div>
    """,
    unsafe_allow_html=True,
)

total_tasks = len(df)
pending = len(df[df["STATUS"] == "Pending"])
completed = len(df[df["STATUS"] == "Completed"])
overdue = len(df[(df["STATUS"] == "Pending") & (df["DATE"] < today)])

cols = st.columns(4)
summary = [
    ("Total Activities", total_tasks),
    ("Pending", pending),
    ("Completed", completed),
    ("Overdue", overdue),
]

for col, item in zip(cols, summary):
    col.markdown(
        f"""
        <div class="card">
            <div class="card-title">{item[0]}</div>
            <div class="card-value">{item[1]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("Adult Decode Activity Schedule")

col1, col2, col3 = st.columns(3)

with col1:
    selected_month = st.multiselect(
        "Filter by Decode Month",
        sorted(df["DECODE MONTH"].dropna().unique()),
    )

with col2:
    selected_cycle = st.multiselect(
        "Filter by Decode Cycle",
        sorted(df["DECODE CYCLE"].dropna().unique()),
    )

with col3:
    selected_person = st.multiselect(
        "Filter by Responsible Person",
        sorted(df["ASSIGNED PERSON"].dropna().unique()),
    )

filtered = df.copy()
if selected_month:
    filtered = filtered[filtered["DECODE MONTH"].isin(selected_month)]
if selected_cycle:
    filtered = filtered[filtered["DECODE CYCLE"].isin(selected_cycle)]
if selected_person:
    filtered = filtered[filtered["ASSIGNED PERSON"].isin(selected_person)]

display = filtered.sort_values(["DATE", "DECODE DATE"]).copy()
display["DATE"] = display["DATE"].dt.strftime("%d %B %Y")
display["DECODE DATE"] = display["DECODE DATE"].dt.strftime("%d %B %Y")

st.dataframe(
    display[
        [
            "ID", "DATE", "DECODE DATE", "DECODE CYCLE", "ASSIGNED PERSON",
            "ACTIVITY", "STATUS", "REMINDER SENT", "LAST REMINDER SENT"
        ]
    ],
    width="stretch",
    hide_index=True,
)

st.divider()
st.subheader("Update Activity Status")

task_options = {
    int(row["ID"]): f"{int(row['ID'])} - {row['ACTIVITY']} ({row['DATE'].strftime('%d %b %Y')})"
    for _, row in df.iterrows()
}

task_id = st.selectbox(
    "Select Activity",
    options=list(task_options.keys()),
    format_func=lambda x: task_options[x],
)

new_status = st.selectbox("New Status", ["Pending", "Completed", "Delayed"])

if st.button("Save Update", type="primary"):
    df.loc[df["ID"] == task_id, "STATUS"] = new_status
    df.to_excel(FILE, sheet_name=SHEET, index=False)
    st.cache_data.clear()
    st.success("Activity updated successfully")
    st.rerun()

st.divider()
st.subheader("Next ADULT Decode Cycle")

next_decode, next_cycle = get_next_decode()
if next_decode is not None:
    days_left = (next_decode.date() - today.date()).days
    st.info(
        f"""
**Next ADULT Decode Date**  
📅 {next_decode.strftime('%d %B %Y')} ({next_cycle})

**Days Remaining**  
{days_left} days
"""
    )
else:
    st.warning("No upcoming Adult Decode date could be calculated.")

st.divider()
st.subheader("Recently Completed Activities")

completed_tasks = df[df["STATUS"] == "Completed"].sort_values("DATE", ascending=False)
if not completed_tasks.empty:
    completed_display = completed_tasks.copy()
    completed_display["DATE"] = completed_display["DATE"].dt.strftime("%d %B %Y")
    completed_display["DECODE DATE"] = completed_display["DECODE DATE"].dt.strftime("%d %B %Y")
    st.dataframe(
        completed_display[
            ["DATE", "DECODE DATE", "DECODE CYCLE", "ASSIGNED PERSON", "ACTIVITY"]
        ],
        width="stretch",
        hide_index=True,
    )
else:
    st.write("No completed activities yet.")