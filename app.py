import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def calculate_payment_plan(first_payment_date_str, course_end_date_str, total_cost, num_payments, course_start_date):
    first_payment_date = datetime.strptime(first_payment_date_str, "%d-%m-%Y")
    course_end_date = datetime.strptime(course_end_date_str, "%d-%m-%Y")
    course_end_month = datetime(course_end_date.year, course_end_date.month, 1)

    today = datetime.today()
    course_start_month = datetime(course_start_date.year, course_start_date.month, 1)

    downpayment = 500 if today >= course_start_month else 199
    late_fee = 149 if today > course_start_date else 0
    finance_fee = 149

    remaining_balance = total_cost - downpayment
    monthly_payment = round((remaining_balance + finance_fee) / num_payments, 2)

    payment_schedule = [("Immediate Downpayment", downpayment)]
    if late_fee:
        payment_schedule.append(("+£149 Late Fee", 149))

    for i in range(num_payments):
        payment_date = first_payment_date + relativedelta(months=i)
        if payment_date > course_end_month:
            break
        payment_schedule.append((payment_date.strftime("%-d %B %Y"), monthly_payment))

    return payment_schedule, downpayment, finance_fee, late_fee, monthly_payment

# -------------------- Streamlit App UI --------------------

st.set_page_config(page_title="Payment Plan Calculator", layout="centered")

st.markdown("""
    <style>
body {
    background-color: #eef2f6;
}
.stApp {
    font-family: 'Segoe UI', sans-serif;
}
.block-container {
    padding: 3rem;
    background-color: #ffffff;
    border-radius: 20px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.1);
    margin-top: 2rem;
}
.payment-line {
    padding: 0.6rem 0;
    border-bottom: 1px solid #d1d5db;
    font-size: 1.1rem;
    color: #1e293b;
}
.info-popup {
    background-color: #fff7ed;
    border-left: 6px solid #f97316;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 6px 20px rgba(249, 115, 22, 0.15);
    font-size: 1rem;
    line-height: 1.6;
    color: #1e293b;
}
.stButton > button {
    background: linear-gradient(to right, #3b82f6, #2563eb);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    border: none;
    font-size: 1rem;
    transition: background 0.3s ease, transform 0.2s ease;
}
.stButton > button:hover {
    background: linear-gradient(to right, #2563eb, #1d4ed8);
    transform: translateY(-1px);
}
h1, h2, h3, .markdown-text-container h3 {
    color: #1e293b;
    margin-bottom: 0.75rem;
}
html[data-theme="dark"] .block-container {
    background-color: #111827;
    color: #f3f4f6;
}
html[data-theme="dark"] .payment-line {
    border-bottom: 1px solid #374151;
    color: #e5e7eb;
}
html[data-theme="dark"] .info-popup {
    background-color: #1f2937;
    border-left: 6px solid #fb923c;
    color: #f9fafb;
    box-shadow: 0 6px 20px rgba(249, 115, 22, 0.15);
}
html[data-theme="dark"] h1, html[data-theme="dark"] h2, html[data-theme="dark"] h3 {
    color: #f3f4f6;
}
html[data-theme="dark"] .stButton > button {
    background: linear-gradient(to right, #60a5fa, #3b82f6);
    color: white;
}
html[data-theme="dark"] .stButton > button:hover {
    background: linear-gradient(to right, #3b82f6, #2563eb);
}
    </style>
""", unsafe_allow_html=True)

st.title("📘 Payment Plan Calculator")

with st.expander("ℹ️ Fee & Cohort Info"):
    st.markdown("""
    <div class="info-popup">
    <strong>Late Fee:</strong> £149 (Added after start date)<br>
    <strong>Finance Fee:</strong> £149 (Always included and calculated into schedule)<br>
    <strong>Down-payment:</strong> £199 but becomes £500 on the 1st of Course Start Month
    <hr>
    <strong>What do the year-numbers mean at the end of product names?</strong><br>
    <em>YEAR-COHORT</em>
    <ul>
        <li><strong>SQE1</strong><br>
        2026-1 = Exam in January 2026<br>
        2026-2 = Exam in July 2026</li>
        <li><strong>SQE2</strong><br>
        2026-1 = Exam in January 2026<br>
        2026-2 = Exam in April 2026<br>
        2026-3 = Exam in July 2026<br>
        2026-4 = Exam in October 2026</li>
        <li><strong>Complete Packages</strong><br>
        These run off the SQE1 dates, even though they will run later into SQE2. This is due to a technical reason with the PSP.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# -------------------- Load & Filter Courses --------------------

EXCEL_URL = "https://www.dropbox.com/scl/fi/qldz8wehdhzd4x05hostg/Products-with-Start-Date-Payment-Plan.xlsx?rlkey=ktap7w88dmoeohd7vwyfdwsl3&st=8v58uuiq&dl=1"

try:
    df = pd.read_excel(EXCEL_URL, engine="openpyxl")
    df.columns = df.columns.str.strip().str.lower()

    if all(col in df.columns for col in ["product name", "course start date", "course end date", "tuition pricing", "ecommerce enrollment deadline"]):
        today = datetime.today()
        df["ecommerce enrollment deadline"] = pd.to_datetime(df["ecommerce enrollment deadline"], dayfirst=True, errors='coerce')
        df = df[df["ecommerce enrollment deadline"] >= today - pd.Timedelta(days=14)].copy()
        df["recently_closed"] = df["ecommerce enrollment deadline"] < today
        df["display name"] = df.apply(
            lambda row: f"{row['product name']} (Recently Closed)" if row["recently_closed"] else row["product name"],
            axis=1
        )

        categories = {
            "All Courses": df,
            "SQE1": df[df["display name"].str.contains("SQE1", case=False, na=False)],
            "SQE2": df[df["display name"].str.contains("SQE2", case=False, na=False)],
            "Complete SQE": df[df["display name"].str.contains("Complete SQE", case=False, na=False)]
        }

        selected_category = st.selectbox("Select a Category", list(categories.keys()))
        filtered_df = categories[selected_category]

        search_term = st.text_input("🔍 Filter Courses (optional):").strip().lower()
        filtered_courses = filtered_df[filtered_df["display name"].str.lower().str.contains(search_term)] if search_term else filtered_df

        course_name = st.selectbox("Select a Course", filtered_courses["display name"].unique())
        course_data = filtered_courses[filtered_courses["display name"] == course_name].iloc[0]

        course_start_date = pd.to_datetime(course_data["course start date"], dayfirst=True)
        course_end_date = pd.to_datetime(course_data["course end date"], dayfirst=True)
        enrollment_deadline = pd.to_datetime(course_data["ecommerce enrollment deadline"], dayfirst=True)
        total_cost = float(course_data["tuition pricing"])

        apply_promo = st.checkbox("Do you have a promo code?")
        if apply_promo:
            promo_option = st.radio("Choose Discount Type:", ["Amount Off", "Percent Off"])
            if promo_option == "Amount Off":
                amount_off = st.number_input("Amount Off (£)", min_value=0.0, value=0.0)
                total_cost -= amount_off
            elif promo_option == "Percent Off":
                percent_off = st.number_input("Percent Off (%)", min_value=0.0, max_value=100.0, value=0.0)
                total_cost -= (percent_off / 100.0) * total_cost

        is_flexible = "Complete SQE Prep Flexible" in course_name

        if is_flexible:
            start_month = datetime(course_start_date.year, course_start_date.month, 1)
            if today < start_month:
                first_payment_date = start_month
            else:
                first_payment_date = datetime(today.year, today.month, 1) + relativedelta(months=1)

            penalty_start = datetime(enrollment_deadline.year, enrollment_deadline.month, 1) + relativedelta(months=1)
            months_since = max(0, (today.year - penalty_start.year) * 12 + today.month - penalty_start.month)
            max_installments = max(1, 12 - months_since)
        else:
            first_payment_date = datetime(today.year, today.month, 1) + relativedelta(months=1)
            earliest_allowed_payment = course_end_date - relativedelta(months=11)
            if first_payment_date < earliest_allowed_payment:
                first_payment_date = datetime(earliest_allowed_payment.year, earliest_allowed_payment.month, 1)

            months_until_exam = (course_end_date.year - first_payment_date.year) * 12 + (course_end_date.month - first_payment_date.month) + 1
            max_installments = min(12, months_until_exam)

        available_installments = list(range(1, max_installments + 1))

        st.markdown("### 📅 Course Details")
        st.write(f"**Start Date:** {course_start_date.strftime('%-d %B %Y')}")
        st.write(f"**Exam Month:** {course_end_date.strftime('%B %Y')}")
        st.write(f"**Enrollment Deadline:** {enrollment_deadline.strftime('%-d %B %Y')}")
        st.write(f"**Tuition Pricing:** £{total_cost:.2f}")

        if available_installments:
            num_payments = st.selectbox("Select Number of Installments", available_installments)

            if st.button("📊 Calculate Payment Plan"):
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
