import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

EXCEL_URL = "https://www.dropbox.com/scl/fi/qldz8wehdhzd4x05hostg/Products-with-Start-Date-Payment-Plan.xlsx?rlkey=ktap7w88dmoeohd7vwyfdwsl3&st=8v58uuiq&dl=1"

try:
    df = pd.read_excel(EXCEL_URL, engine="openpyxl")
    df.columns = df.columns.str.strip().str.lower()

    st.write("Loaded columns:", df.columns.tolist())

    # Find and standardize the enrollment deadline column
    deadline_col = None
    for col in df.columns:
        if "enrol" in col and "deadline" in col:
            deadline_col = col
            break

    if not deadline_col:
        st.error("Could not find 'ecommerce enrollment deadline' column.")
        st.stop()

    df[deadline_col] = pd.to_datetime(df[deadline_col], dayfirst=True, errors="coerce")
    df["course start date"] = pd.to_datetime(df["course start date"], dayfirst=True, errors="coerce")
    df["course end date"] = pd.to_datetime(df["course end date"], dayfirst=True, errors="coerce")

    df = df.dropna(subset=["course start date", "course end date", deadline_col])
    df = df.rename(columns={deadline_col: "ecommerce enrollment deadline"})

    # Apply 2-week post-deadline grace period
    today = datetime.today()
    df = df[df["ecommerce enrollment deadline"] >= today - pd.Timedelta(days=14)]
    df["product name tagged"] = df.apply(
        lambda row: f"{row['product name']} (Recently Closed)" if row["ecommerce enrollment deadline"] < today else row["product name"],
        axis=1
    )

    # Select course
    course_name = st.selectbox("Select a Course", df["product name tagged"].unique())
    course_data = df[df["product name tagged"] == course_name].iloc[0]
    raw_name = course_data["product name"]

    course_start_date = course_data["course start date"]
    course_end_date = course_data["course end date"]
    enrollment_deadline = course_data["ecommerce enrollment deadline"]
    total_cost = float(course_data["tuition pricing"])

    is_flexible = "Complete SQE Prep Flexible" in raw_name

    # Calculate max installments and first payment date
    if is_flexible:
        start_month = datetime(course_start_date.year, course_start_date.month, 1)
        if today < start_month:
            first_payment_date = start_month
        else:
            first_payment_date = datetime(today.year, today.month, 1) + relativedelta(months=1)

        penalty_start = datetime(enrollment_deadline.year, enrollment_deadline.month, 1) + relativedelta(months=1)
        months_since = max(0, (today.year - penalty_start.year) * 12 + today.month - penalty_start.month)
        max_installments = max(1, 12 - months_since)
        available_installments = list(range(1, max_installments + 1))
    else:
        first_payment_date = datetime(today.year, today.month, 1) + relativedelta(months=1)
        earliest_allowed_payment = course_end_date - relativedelta(months=11)
        if first_payment_date < earliest_allowed_payment:
            first_payment_date = datetime(earliest_allowed_payment.year, earliest_allowed_payment.month, 1)
        months_until_exam = (course_end_date.year - first_payment_date.year) * 12 + (course_end_date.month - first_payment_date.month) + 1
        available_installments = list(range(1, min(months_until_exam, 12) + 1))

    st.markdown("### 📅 Course Details")
    st.write(f"**Start Date:** {course_start_date.strftime('%-d %B %Y')}")
    st.write(f"**Exam Month:** {course_end_date.strftime('%B %Y')}")
    st.write(f"**Enrollment Deadline:** {enrollment_deadline.strftime('%-d %B %Y')}")
    st.write(f"**Tuition Pricing:** £{total_cost:.2f}")

    if available_installments:
        num_payments = st.selectbox("Select Number of Installments", available_installments)

        if st.button("📊 Calculate Payment Plan"):
            def calculate_payment_plan(first_payment_date_str, course_end_date_str, total_cost, num_payments, course_start_date):
                first_payment_date = datetime.strptime(first_payment_date_str, "%d-%m-%Y")
                course_end_date = datetime.strptime(course_end_date_str, "%d-%m-%Y")
                course_end_month = datetime(course_end_date.year, course_end_date.month, 1)

                today = datetime.today()
                course_start_month = datetime(course_start_date.year, course_start_date.month, 1)

                downpayment = 500 if today >= course_start_month else 199
                late_fee = 149 if today > course_start_date else 0
                finance_fee = 149

                remaining_balance = total_cost - downpayment + late_fee
                monthly_payment = round((remaining_balance + finance_fee) / num_payments, 2)

                payment_schedule = [("Immediate Downpayment", downpayment)]
                if late_fee:
                    payment_schedule.append(("+£149 Late Fee", 149))

                for i in range(num_payments):
                    payment_date = first_payment_date + relativedelta(months=i)
                    payment_schedule.append((payment_date.strftime("%-d %B %Y"), monthly_payment))

                return payment_schedule, downpayment, finance_fee, late_fee, monthly_payment

            plan, downpayment, finance_fee, late_fee, monthly_payment = calculate_payment_plan(
                first_payment_date.strftime("%d-%m-%Y"),
                course_end_date.strftime("%d-%m-%Y"),
                total_cost,
                num_payments,
                course_start_date
            )

            total_paid = downpayment + late_fee + (monthly_payment * num_payments)

            st.markdown("### 💡 Summary")
            st.success(f"**Downpayment:** £{downpayment:.2f}")
            st.info(f"**Finance Fee (spread):** £{finance_fee:.2f}")
            if late_fee:
                st.warning(f"**Late Fee:** £{late_fee:.2f}")
            st.write(f"**Monthly Payment:** £{monthly_payment:.2f} × {num_payments} months")
            st.write(f"**Total Paid:** £{total_paid:.2f}")

            st.markdown("### 📅 Payment Schedule")
            for date, amount in plan:
                st.markdown(f"<div class='payment-line'><strong>{date}:</strong> £{amount:.2f}</div>", unsafe_allow_html=True)
    else:
        st.warning("No available payment months before the exam month.")

except Exception as e:
    st.error(f"Error loading course data: {e}")
