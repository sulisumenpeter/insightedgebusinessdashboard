import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="InsightEdge Dashboard", layout="wide")
st.title("📊 InsightEdge: Sales & Expense Analyzer")

uploaded_file = st.file_uploader("Upload a Sales, Expense, or Mixed file (CSV, Excel, JSON)", type=["csv", "xlsx", "json"])

if uploaded_file:
    try:
        # STEP 1: Load file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith(".json"):
            df = pd.read_json(uploaded_file)

        st.subheader("📄 Raw Data Preview")
        st.write(df.head())

        # STEP 2: Check & convert Date
        if "Date" not in df.columns:
            possible_date_cols = [col for col in df.columns if "date" in col.lower()]
            if possible_date_cols:
                df["Date"] = pd.to_datetime(df[possible_date_cols[0]])
            else:
                st.error("No 'Date' column found.")
                st.stop()
        else:
            df["Date"] = pd.to_datetime(df["Date"])

        # STEP 3: Normalize Amount column
        if "Amount" not in df.columns:
            possible_amt = [col for col in df.columns if "amount" in col.lower() or "total" in col.lower()]
            if possible_amt:
                df["Amount"] = df[possible_amt[0]]
            else:
                st.error("No 'Amount' or 'Total Price' column found.")
                st.stop()

        # STEP 4: Handle Type column
        if "Type" not in df.columns:
            st.warning("No 'Type' column found. Select what this file contains:")
            selected_type = st.radio("Select File Type", ["Sales", "Expense"])
            df["Type"] = selected_type
        else:
            df["Type"] = df["Type"].str.strip().str.capitalize()  # Normalize e.g., 'sales' -> 'Sales'
            unique_types = df["Type"].unique()
            st.success(f"✅ Detected data types: {', '.join(unique_types)}")

        # Filters
        st.sidebar.header("🔍 Filters")
        date_range = st.sidebar.date_input("Filter by Date", [df["Date"].min().date(), df["Date"].max().date()])
        type_filter = st.sidebar.multiselect("Type", options=df["Type"].unique(), default=df["Type"].unique())

        df_filtered = df[
            (df["Date"] >= pd.to_datetime(date_range[0])) &
            (df["Date"] <= pd.to_datetime(date_range[1])) &
            (df["Type"].isin(type_filter))
        ]

        # KPIs - check if each type exists to avoid errors
        total_sales = df_filtered[df_filtered["Type"] == "Sales"]["Amount"].sum() if "Sales" in df_filtered["Type"].values else 0
        total_expenses = df_filtered[df_filtered["Type"] == "Expense"]["Amount"].sum() if "Expense" in df_filtered["Type"].values else 0
        net_profit = total_sales - total_expenses

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Total Sales", f"{total_sales:,.2f}")
        kpi2.metric("🧾 Total Expenses", f"{total_expenses:,.2f}")
        kpi3.metric("📈 Net Profit", f"{net_profit:,.2f}")

        # Charts
        if not df_filtered.empty:
            df_grouped = df_filtered.groupby(["Date", "Type"])["Amount"].sum().reset_index()
            fig = px.area(df_grouped, x="Date", y="Amount", color="Type", title="Sales vs Expenses Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected filters.")

        # Download button
        st.sidebar.download_button("⬇ Download Filtered Data", df_filtered.to_csv(index=False).encode("utf-8"), "filtered_data.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📥 Upload your file to get started.")
