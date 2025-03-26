import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def calculate_payment_plan(first_payment_date_str, course_end_date_str, total_cost, num_payments, course_started):
    first_payment_date = datetime.strptime(first_payment_date_str, "%d-%m-%Y")
    course_end_date = datetime.strptime(course_end_date_str, "%d-%m-%Y")

    finance_fee = 149
    late_fee = 149 if course_started else 0
    downpayment = 499 if course_started else 199
    remaining_balance = total_cost - downpayment + finance_fee + late_fee

    monthly_payment = round(remaining_balance / num_payments, 2) if num_payments > 1 else remaining_balance
    payment_schedule = [("Immediate Downpayment", downpayment)]
    if course_started:
        payment_schedule.append(("+£149 Late Fee", 149))

    for i in range(num_payments):
        payment_date = first_payment_date + relativedelta(months=i)
        if payment_date > course_end_date:
            break
        payment_schedule.append((payment_date.strftime("%-d %B %Y"), monthly_payment))

    return payment_schedule, downpayment, finance_fee, late_fee, monthly_payment

st.set_page_config(page_title="Payment Plan Calculator", layout="centered")
st.markdown("""
    <style>
    .stApp {
        font-family: 'Segoe UI', sans-serif;
        background-color: var(--background-color, #f9f9f9);
    }
    .block-container {
        padding: 2rem;
        background-color: var(--card-bg-color, #ffffff);
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .payment-line {
        padding: 0.3rem 0;
        border-bottom: 1px solid #eee;
    }
    html[data-theme="dark"] .stApp {
        --background-color: #0e1117;
        --card-bg-color: #1e1e1e;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📘 Payment Plan Calculator")

EXCEL_URL = "https://www.dropbox.com/scl/fi/qldz8wehdhzd4x05hostg/Products-with-Start-Date-Payment-Plan.xlsx?rlkey=ktap7w88dmoeohd7vwyfdwsl3&st=8v58uuiq&dl=1"

try:
    df = pd.read_excel(EXCEL_URL, engine="openpyxl")
    df.columns = df.columns.str.strip().str.lower()

    if all(col in df.columns for col in ["product name", "course start date", "course end date", "tuition pricing", "ecommerce enrollment deadline"]):
        today = datetime.today()
        df = df[pd.to_datetime(df["ecommerce enrollment deadline"], errors='coerce', dayfirst=True) >= today]

        categories = {
            "All Courses": pd.concat([
                df[df["product name"].str.contains("SQE1", case=False, na=False)],
                df[df["product name"].str.contains("SQE2", case=False, na=False)],
                df[df["product name"].str.contains("Complete SQE", case=False, na=False)]
            ]).drop_duplicates(),
            "SQE1": df[df["product name"].str.contains("SQE1", case=False, na=False)],
            "SQE2": df[df["product name"].str.contains("SQE2", case=False, na=False)],
            "Complete SQE": df[df["product name"].str.contains("Complete SQE", case=False, na=False)]
        }

        selected_category = st.selectbox("Select a Category", list(categories.keys()))
        filtered_df = categories[selected_category]

        search_term = st.text_input("🔍 Filter Courses (optional):").strip().lower()
        filtered_courses = filtered_df[filtered_df["product name"].str.lower().str.contains(search_term)] if search_term else filtered_df

        course_name = st.selectbox("Select a Course", filtered_courses["product name"].unique())
        course_data = filtered_courses[filtered_courses["product name"] == course_name].iloc[0]

        course_start_date = pd.to_datetime(course_data["course start date"], dayfirst=True)
        course_end_date = pd.to_datetime(course_data["course end date"], dayfirst=True)
        enrollment_deadline = pd.to_datetime(course_data["ecommerce enrollment deadline"], dayfirst=True)
        total_cost = float(course_data["tuition pricing"])

        apply_promo = st.checkbox("Do you have a promo code?")
        if apply_promo:
            promo_option = st.radio("Choose Discount Type:", ["Amount Off", "Percent Off"])
            amount_off = percent_off = 0.0
            if promo_option == "Amount Off":
                amount_off = st.number_input("Amount Off (£)", min_value=0.0, value=0.0, key="amount_off")
                total_cost -= amount_off
            elif promo_option == "Percent Off":
                percent_off = st.number_input("Percent Off (%)", min_value=0.0, max_value=100.0, value=0.0, key="percent_off")
                total_cost -= (percent_off / 100.0) * total_cost

        first_payment_date = datetime(today.year, today.month, 1) + relativedelta(months=1)
        downpayment_is_499 = today >= datetime.combine(course_start_date, datetime.min.time())
        course_started = today > datetime.combine(course_start_date, datetime.min.time())

        earliest_allowed_payment = course_end_date - relativedelta(months=12)
        if first_payment_date < earliest_allowed_payment:
            first_payment_date = datetime(earliest_allowed_payment.year, earliest_allowed_payment.month, 1)

        months_until_exam = (course_end_date.year - first_payment_date.year) * 12 + (course_end_date.month - first_payment_date.month)
        months_until_exam = max(months_until_exam, 0)
        available_installments = list(range(1, months_until_exam + 1))

        st.markdown("""
        ### 📅 Course Details
        """)
        st.write(f"**Start Date:** {course_start_date.strftime('%-d %B %Y')}")
        st.write(f"**Exam Month:** {course_end_date.strftime('%B %Y')}")
        st.write(f"**Enrollment Deadline:** {enrollment_deadline.strftime('%-d %B %Y')}")
        st.write(f"**Tuition Pricing:** £{total_cost:.2f}")

        if available_installments:
            num_payments = st.selectbox("Select Number of Installments", available_installments)

            if st.button("📊 Calculate Payment Plan"):
                payment_plan, downpayment, finance_fee, late_fee, monthly_payment = calculate_payment_plan(
                    first_payment_date.strftime("%d-%m-%Y"),
                    course_end_date.strftime("%d-%m-%Y"),
                    total_cost,
                    num_payments,
                    downpayment_is_499
                )

                total_paid = downpayment + finance_fee + late_fee + (monthly_payment * num_payments)

                st.markdown("""
                ### 💡 Summary
                """)
                st.success(f"**Downpayment:** £{downpayment:.2f}")
                st.info(f"**Finance Fee:** £{finance_fee:.2f}")
                if late_fee:
                    st.warning(f"**Late Fee:** £{late_fee:.2f}")
                st.write(f"**Monthly Payment:** £{monthly_payment:.2f} × {num_payments} months")
                st.write(f"**Total Paid:** £{total_paid:.2f}")

                st.markdown("""
                ### 📅 Payment Schedule
                <div class='payment-schedule'>
                """, unsafe_allow_html=True)

                for date, amount in payment_plan:
                    st.markdown(f"<div class='payment-line'><strong>{date}:</strong> £{amount:.2f}</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.warning("No available payment months before the exam month.")
    else:
        st.error("Excel file must contain columns: Product Name, Course Start Date, Course End Date, Tuition Pricing, Ecommerce Enrollment Deadline")
except Exception as e:
    st.error(f"Failed to load course data: {e}")
