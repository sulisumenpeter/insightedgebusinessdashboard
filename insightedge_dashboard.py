        # Time-based trend
        df_filtered["Month"] = df_filtered["Date"].dt.to_period("M").astype(str)
        df_filtered["Week"] = df_filtered["Date"].dt.to_period("W").astype(str)
        df_filtered["Day"] = df_filtered["Date"].dt.date.astype(str)  # Add day for daily view

        time_col = "Month" if view_mode == "Monthly" else "Week"
        trend_df = df_filtered.groupby([time_col, "Type"])["Amount"].sum().reset_index()

        fig = px.line(trend_df, x=time_col, y="Amount", color="Type", title=f"{view_mode} Trends: Sales vs Expenses")
        st.plotly_chart(fig, use_container_width=True)

        # New: Daily Sales vs Expense Bar Chart
        daily_df = df_filtered.groupby(["Day", "Type"])["Amount"].sum().reset_index()
        fig_daily = px.bar(
            daily_df,
            x="Day",
            y="Amount",
            color="Type",
            barmode="group",
            title="📅 Daily Sales vs Expenses"
        )
        fig_daily.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_daily, use_container_width=True)
