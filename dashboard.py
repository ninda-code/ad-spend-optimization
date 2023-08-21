import streamlit as st
from pydantic import BaseModel
from typing import List
from AdvertisingModel import OptimizationInput, optimize_budget_func
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

products = ["Clothing","Beauty", "Home Decor"]
num_channels = 3
num_products = 3

# Helper function
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
        results = {
        'Channel': [],
        'ROAS': [],
        'Budget': [],
        'Clicks': [],
        'Transactions': [],
        'Revenue': [],
        'Budget %': [],
        'Clicks %': [],
        'Transactions %': [],
        'Revenue %': []}

        total_budget_allocated = sum(allocations)
        total_clicks = sum(allocations[i] / cost_per_click[i] for i in range(num_channels))

        total_transactions = sum(conversion_rates[p][i] * allocations[i] / cost_per_click[i] for p in range(num_products) for i in range(num_channels))
        total_revenue = sum(avg_ticket_size[p][i] * conversion_rates[p][i] * allocations[i] / cost_per_click[i] for p in range(num_products) for i in range(num_channels))
        
        for i in range(num_channels):
            channel_budget = allocations[i]
            clicks = channel_budget / cost_per_click[i]
            transactions = sum(conversion_rates[p][i] * clicks for p in range(num_products))
            revenue = sum(avg_ticket_size[p][i] * conversion_rates[p][i] * channel_budget / cost_per_click[i] for p in range(num_products))
            roas = revenue/channel_budget
            
            budget_percent = (channel_budget / total_budget_allocated) * 100
            clicks_percent = (clicks / total_clicks) * 100
            transactions_percent = (transactions / total_transactions) * 100
            revenue_percent = (revenue / total_revenue) * 100
            
            results['Channel'].append(f'Channel {i + 1}')
            results['ROAS'].append(roas)
            results['Budget'].append(channel_budget)
            results['Clicks'].append(clicks)
            results['Transactions'].append(transactions)
            results['Revenue'].append(revenue)
            results['Budget %'].append(budget_percent)
            results['Clicks %'].append(clicks_percent)
            results['Transactions %'].append(transactions_percent)
            results['Revenue %'].append(revenue_percent)

        summary_df = pd.DataFrame(results)
        formatted_df = pd.DataFrame(summary_df[['Channel','Budget','Clicks','Transactions','Revenue']]).style.format(precision=2, thousands=",", decimal=".") 

        metric_val = [total_revenue,total_budget_allocated,total_revenue/total_budget_allocated]
        metric_name = ["Total Revenue","Total Ad Spend","ROAS"]
        metric_col = st.columns(3)
        for c in range(2):
            metric_col[c].metric(metric_name[c], "$ {:,.2f}".format(metric_val[c]))
        metric_col[2].metric(metric_name[2], "{:,.2f}".format(metric_val[2]))


        ## st.subheader("Budget Allocation by Channel")
        budget_col = st.columns(3)
        for c in range(3):
            budget_col[c].metric(f'Channel {c + 1} Budget', "$ {:,.2f}".format(allocations[c]))
        
        st.divider()
        
        st.subheader("ROAS by Channel")
        roas_col = st.columns(3)
        for c in range(3):
            roas_col[c].metric(f'Channel {c + 1}', "{:,.2f}".format(summary_df['ROAS'][c]))

        
        st.subheader("Channel Performance")
        df_plot = pd.melt(summary_df[['Channel','Budget %','Clicks %','Transactions %','Revenue %']],id_vars='Channel',var_name='Metrics', value_name='Value')
        fig = px.bar(df_plot, x="Channel", color="Metrics",
             y='Value',
             barmode='group',
             height=600
            )
        st.plotly_chart(fig)
        st.table(formatted_df)


    else:
        st.write("No solution found.")