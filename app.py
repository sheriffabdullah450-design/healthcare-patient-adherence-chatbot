




import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px

DB_NAME = "healthcare.db"


# STEP 1: Create database and table
def create_database():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            medicine_time TEXT NOT NULL,
            medicine_date TEXT,
            adherence_status TEXT DEFAULT 'Pending'
        )
    """)

    columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(medicine_schedule)"
        ).fetchall()
    ]

    if "medicine_date" not in columns:
        cursor.execute(
            "ALTER TABLE medicine_schedule ADD COLUMN medicine_date TEXT"
        )

    if "adherence_status" not in columns:
        cursor.execute(
            "ALTER TABLE medicine_schedule "
            "ADD COLUMN adherence_status TEXT DEFAULT 'Pending'"
        )

    connection.commit()
    connection.close()


# STEP 2: Save a schedule
def save_schedule(patient_name, medicine_name, medicine_time, medicine_date):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO medicine_schedule
        (patient_name, medicine_name, medicine_time, medicine_date)
        VALUES (?, ?, ?, ?)
    """, (
        patient_name,
        medicine_name,
        medicine_time,
        medicine_date
    ))

    connection.commit()
    connection.close()


# STEP 3: Get schedules
def get_schedules():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, patient_name, medicine_name, medicine_time,
               medicine_date, adherence_status
        FROM medicine_schedule
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    connection.close()
    return records


# STEP 4: Delete a schedule
def delete_schedule(schedule_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM medicine_schedule WHERE id = ?",
        (schedule_id,)
    )

    connection.commit()
    connection.close()


# STEP 5: Update medicine status
def update_adherence_status(schedule_id, status):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE medicine_schedule "
        "SET adherence_status = ? WHERE id = ?",
        (status, schedule_id)
    )

    connection.commit()
    connection.close()


# STEP 6: Initialize app
st.set_page_config(
    page_title="Healthcare Adherence Chatbot",
    page_icon="💊",
    layout="wide"
)

create_database()

st.title("Healthcare Patient Adherence Chatbot")

st.info(
    "Educational prototype only. Follow your healthcare "
    "professional's instructions. Do not change medicine doses yourself."
)


# STEP 7: Dashboard
st.subheader("Dashboard")

dashboard_records = get_schedules()

total_schedules = len(dashboard_records)

total_patients = len({
    record[1].strip().lower()
    for record in dashboard_records
})

taken_count = sum(
    1 for record in dashboard_records
    if record[5] == "Taken"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Schedules", total_schedules)

with col2:
    st.metric("Patients", total_patients)

with col3:
    st.metric("Marked as Taken", taken_count)


# STEP 8: Chart
st.subheader("Schedule Overview")

if dashboard_records:
    chart_data = pd.DataFrame(
        dashboard_records,
        columns=[
            "ID", "Patient", "Medicine",
            "Time", "Date", "Status"
        ]
    )

    patient_counts = (
        chart_data.groupby("Patient")
        .size()
        .reset_index(name="Schedules")
    )

    figure = px.bar(
        patient_counts,
        x="Patient",
        y="Schedules",
        title="Schedules per Patient"
    )

    st.plotly_chart(figure, use_container_width=True)
else:
    st.write("Add a sample schedule to see the chart.")


# STEP 9: Add schedule form
st.subheader("Add Medicine Schedule")

with st.form("medicine_form"):
    patient_name = st.text_input("Patient name")
    medicine_name = st.text_input("Prescribed medicine name")
    medicine_time = st.time_input("Prescribed medicine time")
    medicine_date = st.date_input("Schedule Date")

    submitted = st.form_submit_button("Save Schedule")

    if submitted:
        if patient_name.strip() and medicine_name.strip():
            save_schedule(
                patient_name.strip(),
                medicine_name.strip(),
                medicine_time.strftime("%I:%M %p"),
                medicine_date.isoformat()
            )

            st.success("Schedule saved successfully!")
            st.rerun()
        else:
            st.warning("Please enter both names.")


# STEP 10: Search and filter schedules
st.subheader("Saved Schedules")

selected_date = st.date_input(
    "Choose a schedule date",
    key="filter_schedule_date"
)

show_all_dates = st.checkbox(
    "Show schedules from all dates",
    value=True
)

search_patient = st.text_input("Search by patient name")

records = get_schedules()

if not show_all_dates:
    records = [
        record for record in records
        if record[4] == selected_date.isoformat()
    ]

if search_patient.strip():
    records = [
        record for record in records
        if search_patient.strip().lower() in record[1].lower()
    ]


# STEP 11: Download CSV
if records:
    export_data = pd.DataFrame(
        records,
        columns=[
            "ID", "Patient", "Medicine",
            "Time", "Date", "Status"
        ]
    )

    csv_file = export_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Schedules as CSV",
        data=csv_file,
        file_name="medicine_schedules.csv",
        mime="text/csv"
    )


# STEP 12: Display, update and delete schedules
if records:
    for schedule_id, patient, medicine, time, date, status in records:
        with st.container():
            st.write(f"**Patient:** {patient}")
            st.write(f"**Medicine:** {medicine}")
            st.write(f"**Time:** {time}")
            st.write(f"**Date:** {date or 'Not set'}")
            st.caption(f"Medicine Status: {status}")

            if status == "Pending":
                if st.button(
                    "Mark as Taken",
                    key=f"taken_{schedule_id}"
                ):
                    update_adherence_status(
                        schedule_id, "Taken"
                    )
                    st.rerun()
            else:
                st.success("Medicine marked as Taken")

            if st.button(
                "Delete Schedule",
                key=f"delete_{schedule_id}"
            ):
                delete_schedule(schedule_id)
                st.rerun()

            st.divider()
else:
    st.write("No matching schedules found.")


# STEP 12.5: Patient-wise Report Filter

# STEP 12.5: Patient-wise Report Filter
st.subheader("Patient-wise Report")

patient_records = get_schedules()

if patient_records:
    patient_names = sorted(set(
        record[1] for record in patient_records
    ))

    selected_patient = st.selectbox(
        "Select a patient",
        patient_names,
        key="report_patient_filter"
    )

    filtered_patient_records = [
        record for record in patient_records
        if record[1] == selected_patient
    ]

    patient_report = pd.DataFrame(
        filtered_patient_records,
        columns=[
            "ID", "Patient", "Medicine",
            "Time", "Date", "Status"
        ]
    )

    st.dataframe(
        patient_report,
        use_container_width=True,
        hide_index=True
    )

    patient_csv = patient_report.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Patient Report",
        data=patient_csv,
        file_name="patient_adherence_report.csv",
        mime="text/csv",
        key="download_patient_report"
    )

    taken_total = int(
        (patient_report["Status"] == "Taken").sum()
    )
    pending_total = int(
        (patient_report["Status"] == "Pending").sum()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Taken Schedules", taken_total)

    with col2:
        st.metric("Pending Schedules", pending_total)

else:
    st.info("Add a schedule to view patient reports.")

# STEP 13: Medicine Adherence Report
st.subheader("Medicine Adherence Report")

all_records = get_schedules()

if all_records:
    report_data = pd.DataFrame(
        all_records,
        columns=[
            "ID", "Patient", "Medicine",
            "Time", "Date", "Status"
        ]
    )

    total = len(report_data)
    taken = int((report_data["Status"] == "Taken").sum())
    pending = int((report_data["Status"] == "Pending").sum())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Schedules", total)

    with col2:
        st.metric("Taken", taken)

    with col3:
        st.metric("Pending", pending)

    status_chart = (
        report_data["Status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Count")
    )

    figure = px.pie(
        status_chart,
        names="Status",
        values="Count",
        title="Schedule Status Distribution"
    )

    st.plotly_chart(figure, use_container_width=True)

else:
    st.info("Add a medicine schedule to generate a report.")
    
# STEP 14: Medicine Reminder Alert

st.subheader("Medicine Reminder Alert")

reminder_records = get_schedules()

if reminder_records:
    from datetime import datetime

    current_date = datetime.now().date()
    current_time = datetime.now().strftime("%H:%M")

    for record in reminder_records:
        patient = record[1]
        medicine = record[2]
        medicine_time = str(record[3])[:5]
        medicine_date = str(record[4])[:10]
        status = record[5]

        if medicine_date == str(current_date):
            if medicine_time <= current_time and status == "Pending":
                st.warning(
                    f"Reminder: {patient} - "
                    f"{medicine} scheduled at {medicine_time}. "
                    "Please check the medicine schedule."
                )
else:
    st.info("Add a medicine schedule to see reminders.")


# STEP 13: Healthcare assistant
st.subheader("Healthcare Assistant")

question = st.text_input(
    "Ask a general healthcare question"
)

if st.button("Submit Question"):
    if question.strip():
        text = question.lower()

        if "reminder" in text or "schedule" in text:
            st.write(
                "Your saved schedules are shown in the "
                "Saved Schedules section."
            )

        elif "missed" in text or "forgot" in text:
            st.write(
                "Follow the medicine instructions or contact "
                "your doctor or pharmacist about a missed dose. "
                "Do not double a dose unless a healthcare "
                "professional instructs you."
            )

        elif "side effect" in text:
            st.write(
                "Contact your doctor or pharmacist about "
                "possible side effects. Seek urgent medical "
                "help for severe or rapidly worsening symptoms."
            )

        else:
            st.write(
                "I can answer basic questions about schedules "
                "and general medicine safety. For diagnosis, dosage, "
                "or treatment advice, consult a qualified "
                "healthcare professional."
            )
    else:
        st.warning("Please enter a question.")


st.caption(
    "Educational prototype. Not a substitute for professional care."
)

# STEP 15: Medicine Adherence Percentage

st.subheader("Medicine Adherence Percentage")

adherence_records = get_schedules()

if adherence_records:
    total = len(adherence_records)

    taken = sum(
        1 for record in adherence_records
        if record[5] == "Taken"
    )

    pending = total - taken

    adherence_percentage = (taken / total) * 100

    st.metric(
        "Overall Adherence",
        f"{adherence_percentage:.1f}%"
    )

    st.progress(taken / total)

    st.write(f"Total schedules: {total}")
    st.write(f"Taken: {taken}")
    st.write(f"Pending: {pending}")

else:
    st.info("Add medicine schedules to calculate adherence.")
    
# STEP 16: Patient-wise Adherence Chart

st.subheader("Patient-wise Adherence Chart")

chart_records = get_schedules()

if chart_records:
    chart_df = pd.DataFrame(
        chart_records,
        columns=[
            "ID", "Patient", "Medicine",
            "Time", "Date", "Status"
        ]
    )

    patient_chart = (
        chart_df.groupby("Patient")
        .agg(
            Total=("Status", "count"),
            Taken=("Status", lambda s: (s == "Taken").sum())
        )
        .reset_index()
    )

    patient_chart["Adherence (%)"] = (
        patient_chart["Taken"] /
        patient_chart["Total"] * 100
    ).round(1)

    fig = px.bar(
        patient_chart,
        x="Patient",
        y="Adherence (%)",
        title="Medicine Adherence by Patient",
        range_y=[0, 100],
        text="Adherence (%)"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Add schedules to view the patient-wise chart.")


