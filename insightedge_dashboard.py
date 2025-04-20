import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="InsightEdge Dashboard", layout="wide")
st.title("📊 InsightEdge: Sales & Expense Analyzer")

uploaded_file = st.file_uploader("Upload a Sales, Expense, or Mixed file (CSV, Excel, JSON)", type=["csv", "xlsx", "json"])

if uploaded_file:
    try:
        # Load File
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith(".json"):
            df = pd.read_json(uploaded_file)

        st.subheader("📄 Raw Data Preview")
        st.write(df.head())

        # Ensure Date column
        if "Date" not in df.columns:
            possible_date_cols = [col for col in df.columns if "date" in col.lower()]
            if possible_date_cols:
                df["Date"] = pd.to_datetime(df[possible_date_cols[0]])
            else:
                st.error("No 'Date' column found.")
                st.stop()
        else:
            df["Date"] = pd.to_datetime(df["Date"])

        # Standardize Amount
        if "Amount" not in df.columns:
            possible_amt = [col for col in df.columns if "amount" in col.lower() or "total" in col.lower()]
            if possible_amt:
                df["Amount"] = df[possible_amt[0]]
            else:
                st.error("No 'Amount' or 'Total Price' column found.")
                st.stop()

        # Handle Type
        if "Type" not in df.columns:
            st.warning("No 'Type' column found. Select what this file contains:")
            selected_type = st.radio("Select File Type", ["Sales", "Expense"])
            df["Type"] = selected_type
        else:
            df["Type"] = df["Type"].str.strip().str.capitalize()
            st.success(f"✅ Detected data types: {', '.join(df['Type'].unique())}")

        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        date_range = st.sidebar.date_input("Filter by Date", [df["Date"].min().date(), df["Date"].max().date()])
        type_filter = st.sidebar.multiselect("Type", options=df["Type"].unique(), default=df["Type"].unique())

        # Optional breakdown filters
        breakdown_options = []
        for opt in ["Product", "Category", "Customer"]:
            if opt in df.columns:
                breakdown_options.append(opt)
        breakdown_choice = st.sidebar.selectbox("Breakdown By (for charts)", options=["None"] + breakdown_options)

        view_mode = st.sidebar.radio("Trend View", ["Monthly", "Weekly"])

        df_filtered = df[
            (df["Date"] >= pd.to_datetime(date_range[0])) &
            (df["Date"] <= pd.to_datetime(date_range[1])) &
            (df["Type"].isin(type_filter))
        ]

        # KPIs
        total_sales = df_filtered[df_filtered["Type"] == "Sales"]["Amount"].sum()
        total_expenses = df_filtered[df_filtered["Type"] == "Expense"]["Amount"].sum()
        net_profit = total_sales - total_expenses

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Total Sales", f"{total_sales:,.2f}")
        kpi2.metric("🧾 Total Expenses", f"{total_expenses:,.2f}")
        kpi3.metric("📈 Net Profit", f"{net_profit:,.2f}")

        # Time-based trend
        df_filtered["Month"] = df_filtered["Date"].dt.to_period("M").astype(str)
        df_filtered["Week"] = df_filtered["Date"].dt.to_period("W").astype(str)

        time_col = "Month" if view_mode == "Monthly" else "Week"
        trend_df = df_filtered.groupby([time_col, "Type"])["Amount"].sum().reset_index()

        fig = px.line(trend_df, x=time_col, y="Amount", color="Type", title=f"{view_mode} Trends: Sales vs Expenses")
        st.plotly_chart(fig, use_container_width=True)

        # Optional Breakdown
        if breakdown_choice != "None":
            pie_df = df_filtered.groupby([breakdown_choice])["Amount"].sum().reset_index()
            fig2 = px.pie(pie_df, names=breakdown_choice, values="Amount", title=f"{breakdown_choice} Breakdown (Pie Chart)")
            st.plotly_chart(fig2, use_container_width=True)

        # Heatmap
        df_filtered["Hour"] = df_filtered["Date"].dt.hour
        df_filtered["DayOfWeek"] = df_filtered["Date"].dt.dayofweek
        df_filtered["DayName"] = df_filtered["DayOfWeek"].apply(lambda x: calendar.day_name[x])

        heat_df = df_filtered.groupby(["DayName", "Hour"])["Amount"].sum().reset_index()
        heat_pivot = heat_df.pivot(index="DayName", columns="Hour", values="Amount").fillna(0)
        heat_pivot = heat_pivot.reindex([
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ])

        heatmap = go.Figure(data=go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns,
            y=heat_pivot.index,
            colorscale='Viridis'
        ))
        heatmap.update_layout(title="🕒 Activity Heatmap (Day vs Hour)", xaxis_title="Hour", yaxis_title="Day of Week")
        st.plotly_chart(heatmap, use_container_width=True)

        # Forecasting (Using Linear Regression)
        df_filtered['DateOrdinal'] = df_filtered['Date'].map(pd.Timestamp.toordinal)
        df_sales = df_filtered[df_filtered['Type'] == 'Sales']

        model = LinearRegression()
        model.fit(df_sales[['DateOrdinal']], df_sales['Amount'])

        # Predicting future sales for next 30 days
        future_dates = pd.date_range(df_sales['Date'].max(), periods=30, freq='D')
        future_dates_ordinal = future_dates.map(pd.Timestamp.toordinal)

        forecasted_sales = model.predict(future_dates_ordinal.values.reshape(-1, 1))

        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Forecasted Sales': forecasted_sales
        })

        # Plot forecasted sales
        forecast_fig = px.line(forecast_df, x='Date', y='Forecasted Sales', title="📉 Forecasted Sales for the Next 30 Days")
        st.plotly_chart(forecast_fig, use_container_width=True)

        # Excel Export
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_filtered.to_excel(writer, index=False, sheet_name="Filtered Data")
            forecast_df.to_excel(writer, index=False, sheet_name="Forecast Data")
            writer.save()

        st.sidebar.download_button(
            "⬇ Export to Excel", output.getvalue(), file_name="filtered_data_and_forecast.xlsx", mime="application/vnd.ms-excel"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📥 Upload your file to get started.")
