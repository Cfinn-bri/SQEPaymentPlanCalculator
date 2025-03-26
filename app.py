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

    remaining_balance = total_cost - downpayment + late_fee
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

st.set_page_config(page_title="Payment Plan Calculator", layout="centered")
st.markdown("""
    <style>
    body {
        background-color: #f0f4f8;
    }
    .stApp {
        font-family: 'Segoe UI', sans-serif;
        background-color: var(--background-color, #f0f4f8);
    }
    .block-container {
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    .payment-line {
        padding: 0.4rem 0;
        border-bottom: 1px solid #e0e0e0;
        font-size: 1.05rem;
    }
    .info-popup {
        background-color: #fff8e6;
        border: 2px solid #ffb300;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(255, 179, 0, 0.25);
        font-size: 0.95rem;
    }
    .stButton > button {
        background-color: #0066cc;
        color: white;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #004c99;
    }
    html[data-theme="dark"] .stApp {
        --background-color: #0e1117;
        --card-bg-color: #1e1e1e;
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
