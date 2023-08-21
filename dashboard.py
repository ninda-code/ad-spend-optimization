import streamlit as st
from pydantic import BaseModel
from typing import List
from AdvertisingModel import OptimizationInput, optimize_budget_func
import numpy as np
import locale
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

locale.setlocale(locale.LC_ALL, '')
products = ["Clothing","Beauty", "Home Decor"]
num_channels = 3
num_products = 3


def str_to_2darray(s):
    rows = s.strip().split('\n')
    return [list(map(float, row[1:-1].split(', '))) for row in rows]
# Streamlit UI
st.title('Marketing Budget Allocation Optimization')

# Create input form in the sidebar using Pydantic model
with st.sidebar:
    st.header('Input Parameters')
    conversion_rates = st.text_area('Conversion Rates', value="[0.04, 0.01, 0.015]\n[0, 0.03, 0.015]\n[0.01, 0, 0.015]")
    avg_ticket_size = st.text_area('Average Ticket Size', value="[25, 55, 55]\n[0, 60, 70]\n[40, 0, 80]")
    cost_per_click = st.text_area('Cost per Click', value="[1.1, 1.6, 1.9]")
    total_budget = st.slider('Total Budget', 5000, 20000, 10000)
    min_budget_percent = st.slider('Minimum Budget Percentage per Channel', 5, 30, 15) / 100
    min_transactions_per_product = [st.number_input(f"Minimum Transactions for {prod} Product:", 
                             min_value = 0, 
                             max_value = 100, 
                             step= 1,
                             key = "min_trx_for_"+str(prod)) 
                             for prod in products]
    min_clicks = st.slider('Minimum Clicks', 5000, 15000, 7000)
    max_cost_percent = st.slider('Maximum Cost Percentage', 50, 90, 80) / 100
    


if st.sidebar.button('Optimize'):
    # Parse input data
    conversion_rates = str_to_2darray(conversion_rates)
    avg_ticket_size = str_to_2darray(avg_ticket_size)
    cost_per_click = eval(cost_per_click)

    input_data = OptimizationInput(
        conversion_rates=conversion_rates,
        avg_ticket_size=avg_ticket_size,
        cost_per_click=cost_per_click,
        total_budget=total_budget,
        min_budget_percent=min_budget_percent,
        min_transactions_per_product=min_transactions_per_product,
        min_clicks=min_clicks,
        max_cost_percent=max_cost_percent
    )
   

    # Run optimization
    allocations, revenue = optimize_budget_func(input_data)

    if allocations is not None:
        revenue_fmt = locale.format_string("%.2f", float(revenue), grouping=True)
        adspend_fmt = locale.format_string("%.2f", float(np.sum(allocations)), grouping=True)
        roas_fmt = locale.format_string("%.2f", float(revenue/np.sum(allocations)), grouping=True)
        budget_vars = allocations
        r1_col1, r1_col2, r1_col3 = st.columns(3)
        r1_col1.metric("Revenue", revenue_fmt)
        r1_col2.metric("Ad Spend", adspend_fmt )
        r1_col3.metric("ROAS",roas_fmt )

        r2_col1, r2_col2= st.columns(2)
        revenue_data = np.zeros((num_products, num_channels))
        for p in range(num_products):
            for i in range(num_channels):
                revenue_data[p][i] = (avg_ticket_size[p][i] * conversion_rates[p][i] * budget_vars[i]/ cost_per_click[i])

        # Calculate ROAS for each channel
        roas_data = np.zeros(num_channels)
        for i in range(num_channels):
            roas_data[i] = revenue_data[:, i].sum() / budget_vars[i]

        roas_df = pd.DataFrame({"Channel": [f'Channel {i + 1}' for i in range(num_channels)], "ROAS": roas_data})

        
        revenue_df = pd.DataFrame(revenue_data, columns=[f'Channel {i + 1}' for i in range(num_channels)],
                                index=[f'Product {p + 1}' for p in range(num_products)])

        # Create a stacked bar chart using Streamlit
        r2_col1.subheader("Revenue by Product")
        r2_col1.caption("xx")
        r2_col1.bar_chart(revenue_df)
        r2_col1.write(revenue_df) 

        r2_col2.subheader("ROAS by Channel")
        r2_col2.caption("xx")
        r2_col2.bar_chart(roas_df)
        r2_col2.write(roas_df) 




        st.write("Optimal budget allocation per channel:")
        for i, allocation in enumerate(allocations):
            st.write(f"Budget for channel {i + 1}: {allocation:.2f}")
        st.write("Total profit:", revenue)

    else:
        st.write("No solution found.")