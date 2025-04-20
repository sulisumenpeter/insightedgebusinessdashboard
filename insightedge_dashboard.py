import streamlit as st 
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="InsightEdge Dashboard", layout="wide")
st.title("📊 InsightEdge: Sales & Expense Analyzer")

uploaded_file = st.file_uploader("Upload a Sales, Expense, or Mixed file (CSV, Excel, JSON)", type=["csv", "xlsx", "json"])

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Data')
    processed_data = output.getvalue()
    return processed_data

if uploaded_file:
    try:
        # Load file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith(".json"):
            df = pd.read_json(uploaded_file)

        st.subheader("📄 Raw Data Preview")
        st.write(df.head())

        # Date conversion
        if "Date" not in df.columns:
            possible_date_cols = [col for col in df.columns if "date" in col.lower()]
            if possible_date_cols:
                df["Date"] = pd.to_datetime(df[possible_date_cols[0]])
            else:
                st.error("No 'Date' column found.")
                st.stop()
        else:
            df["Date"] = pd.to_datetime(df["Date"])

        # Amount normalization
        if "Amount" not in df.columns:
            possible_amt = [col for col in df.columns if "amount" in col.lower() or "total" in col.lower()]
            if possible_amt:
                df["Amount"] = df[possible_amt[0]]
            else:
                st.error("No 'Amount' or 'Total Price' column found.")
                st.stop()

        # Type column check
        if "Type" not in df.columns:
            selected_type = st.radio("Select File Type", ["Sales", "Expense"])
            df["Type"] = selected_type
        else:
            df["Type"] = df["Type"].str.strip().str.capitalize()

        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        date_range = st.sidebar.date_input("Filter by Date", [df["Date"].min().date(), df["Date"].max().date()])
        type_filter = st.sidebar.multiselect("Type", options=df["Type"].unique(), default=df["Type"].unique())

        product_col = next((col for col in df.columns if "product" in col.lower()), None)
        category_col = next((col for col in df.columns if "category" in col.lower()), None)
        customer_col = next((col for col in df.columns if "customer" in col.lower() or "client" in col.lower()), None)

        if product_col:
            product_filter = st.sidebar.multiselect("Product", options=df[product_col].dropna().unique())
            if product_filter:
                df = df[df[product_col].isin(product_filter)]
        if category_col:
            category_filter = st.sidebar.multiselect("Category", options=df[category_col].dropna().unique())
            if category_filter:
                df = df[df[category_col].isin(category_filter)]
        if customer_col:
            customer_filter = st.sidebar.multiselect("Customer", options=df[customer_col].dropna().unique())
            if customer_filter:
                df = df[df[customer_col].isin(customer_filter)]

        df_filtered = df[
            (df["Date"] >= pd.to_datetime(date_range[0])) &
            (df["Date"] <= pd.to_datetime(date_range[1])) &
            (df["Type"].isin(type_filter))
        ]

        # KPIs
        total_sales = df_filtered[df_filtered["Type"] == "Sales"]["Amount"].sum() if "Sales" in df_filtered["Type"].values else 0
        total_expenses = df_filtered[df_filtered["Type"] == "Expense"]["Amount"].sum() if "Expense" in df_filtered["Type"].values else 0
        net_profit = total_sales - total_expenses

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Total Sales", f"{total_sales:,.2f}")
        kpi2.metric("🧾 Total Expenses", f"{total_expenses:,.2f}")
        kpi3.metric("📈 Net Profit", f"{net_profit:,.2f}")

        # Time grouping toggle
        st.subheader("📆 Time Series Analysis")
        group_freq = st.radio("Group By", ["Monthly", "Weekly"], horizontal=True)
        df_filtered["Period"] = df_filtered["Date"].dt.to_period("M" if group_freq == "Monthly" else "W").dt.start_time

        df_time = df_filtered.groupby(["Period", "Type"])["Amount"].sum().reset_index()
        fig_time = px.line(df_time, x="Period", y="Amount", color="Type", markers=True,
                           title=f"{group_freq} Sales vs Expenses Trend")
        st.plotly_chart(fig_time, use_container_width=True)

        # Optional charts
        st.subheader("📌 Breakdown Charts")
        if product_col:
            prod_fig = px.bar(df_filtered, x=product_col, y="Amount", color="Type", barmode="group",
                              title="Amount by Product")
            st.plotly_chart(prod_fig, use_container_width=True)
        if category_col:
            cat_fig = px.bar(df_filtered, x=category_col, y="Amount", color="Type", barmode="group",
                             title="Amount by Category")
            st.plotly_chart(cat_fig, use_container_width=True)
        if customer_col:
            cust_fig = px.bar(df_filtered, x=customer_col, y="Amount", color="Type", barmode="group",
                              title="Amount by Customer")
            st.plotly_chart(cust_fig, use_container_width=True)

        # Excel Export
        excel_data = convert_df_to_excel(df_filtered)
        st.sidebar.download_button("⬇ Download as Excel", data=excel_data, file_name="filtered_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📥 Upload your file to get started.")
