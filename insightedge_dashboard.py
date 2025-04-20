import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import base64
import os
from datetime import datetime

st.set_page_config(page_title="InsightEdge: BI Dashboard", layout="wide")
st.title("📊 InsightEdge: Business Intelligence Dashboard")
st.markdown("Upload your JSON, CSV, or Excel file containing both sales and expense records.")

if 'theme' not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

st.button("Toggle Dark/Light Mode", on_click=toggle_theme)

uploaded_file = st.file_uploader("📂 Upload your JSON, CSV, or Excel file", type=["json", "csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith("json"):
            df = pd.read_json(uploaded_file)
        elif uploaded_file.name.endswith("csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith("xlsx"):
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Ensure 'Date' column exists
        if "Date" not in df.columns:
            st.warning("🕒 'Date' column not found. Please select the correct one.")
            possible_dates = [col for col in df.columns if "date" in col.lower()]
            if possible_dates:
                date_column = st.selectbox("Select date column", options=possible_dates)
                df["Date"] = pd.to_datetime(df[date_column])
            else:
                st.error("🚫 No date-like column found.")
                st.stop()
        else:
            df["Date"] = pd.to_datetime(df["Date"])

        # Ensure 'Type' exists to differentiate Sales vs Expenses
        if "Type" not in df.columns:
            st.error("🚫 'Type' column is missing. Please include a column labeled 'Type' with values like 'Sales' or 'Expense'.")
            st.stop()

        # Ensure 'Amount' column exists
        if "Amount" not in df.columns and "Total Price" not in df.columns:
            st.error("🚫 No 'Amount' or 'Total Price' column found.")
            st.stop()
        elif "Amount" not in df.columns:
            df["Amount"] = df["Total Price"]

        df["Type"] = df["Type"].str.capitalize()

        # Sidebar filters
        st.sidebar.header("Filters")
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        date_range = st.sidebar.date_input("Date range", [min_date, max_date], min_value=min_date, max_value=max_date)

        type_filter = st.sidebar.multiselect("Select Type", options=df["Type"].unique(), default=df["Type"].unique())
        category_filter = st.sidebar.multiselect("Category Filter", options=df["Product"].unique() if "Product" in df.columns else [], default=None)

        df_filtered = df[
            (df["Date"].between(date_range[0], date_range[1])) &
            (df["Type"].isin(type_filter))
        ]
        if category_filter and "Product" in df.columns:
            df_filtered = df_filtered[df_filtered["Product"].isin(category_filter)]

        with st.expander("📋 Raw Data Preview"):
            st.dataframe(df_filtered)

        # Summary Calculations
        total_sales = df_filtered[df_filtered["Type"] == "Sales"]["Amount"].sum()
        total_expenses = df_filtered[df_filtered["Type"] == "Expense"]["Amount"].sum()
        net_profit = total_sales - total_expenses

        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        col_kpi1.metric("💰 Total Sales", f"{total_sales:,.2f}")
        col_kpi2.metric("🧾 Total Expenses", f"{total_expenses:,.2f}")
        col_kpi3.metric("📈 Net Profit", f"{net_profit:,.2f}", delta=f"{(net_profit/total_sales*100 if total_sales else 0):.1f}%")

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            sales_data = df_filtered[df_filtered["Type"] == "Sales"]
            if not sales_data.empty:
                fig_sales = px.line(sales_data, x="Date", y="Amount", title="📈 Sales Over Time")
                st.plotly_chart(fig_sales, use_container_width=True)
        with col2:
            expense_data = df_filtered[df_filtered["Type"] == "Expense"]
            if not expense_data.empty:
                fig_exp = px.line(expense_data, x="Date", y="Amount", title="💸 Expenses Over Time", color_discrete_sequence=["red"])
                st.plotly_chart(fig_exp, use_container_width=True)

        if not df_filtered.empty:
            grouped = df_filtered.groupby(["Type", "Date"])["Amount"].sum().reset_index()
            fig_combo = px.area(grouped, x="Date", y="Amount", color="Type", title="📊 Combined Sales & Expenses")
            st.plotly_chart(fig_combo, use_container_width=True)

        st.sidebar.header("Export Filtered Data")
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        csv = convert_df(df_filtered)
        st.sidebar.download_button("⬇️ Download CSV", csv, "filtered_data.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
else:
    st.info("📁 Upload a file to begin analysis.")
