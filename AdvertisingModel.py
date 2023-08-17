# Import libraries
from pydantic import BaseModel
from typing import List
import gurobipy as gp
from gurobipy import GRB
import numpy as np


class OptimizationInput(BaseModel):
    conversion_rates: List[List[float]]
    avg_ticket_size: List[List[float]]
    cost_per_click: List[float]
    total_budget: float
    min_budget_percent : float
    min_transactions_per_product: List[int]
    min_clicks: int
    max_cost_percent: float

# test
def optimize_budget_func(input_data: OptimizationInput):
    # Extract input data from the Pydantic model
    total_budget = input_data.total_budget
    min_budget_percent = input_data.min_budget_percent
    min_transactions_per_product = input_data.min_transactions_per_product
    min_clicks = input_data.min_clicks
    max_cost_percent = input_data.max_cost_percent
    conversion_rates = input_data.conversion_rates
    avg_ticket_size = input_data.avg_ticket_size
    cost_per_click = input_data.cost_per_click

    # Create model
    model = gp.Model()

    # Add decision variables for budget allocation per channel
    num_channels = 3
    num_products = 3
    budget_vars = model.addVars(num_channels, lb=0.0, vtype=GRB.CONTINUOUS, name='budget')

    # Set the objective function (maximize revenue)
    model.setObjective(gp.quicksum(((avg_ticket_size[p][i] * conversion_rates[p][i] * budget_vars[i] / cost_per_click[i]) for p in range(num_products) for i in range(num_channels))) , GRB.MAXIMIZE)

    # Set the total budget constraint
    model.addConstr(gp.quicksum(budget_vars[i] for i in range(num_channels)) <= total_budget, name='total_budget')

    # Add constraint for at least 15% budget per channel
    for i in range(num_channels):
        model.addConstr(budget_vars[i] >= min_budget_percent * total_budget, name=f'min_budget_channel_{i + 1}')

    # Add constraint for total transactions per product
    for p in range(num_products):  # Products
        model.addConstr(gp.quicksum(conversion_rates[p][i] * budget_vars[i] for i in range(num_channels)) >= min_transactions_per_product[p], name=f'min_conversions_product_{p + 1}')

    # Add constraint for total clicks
    model.addConstr(gp.quicksum(budget_vars[i] / cost_per_click[i] for i in range(num_channels)) >= min_clicks, name='min_clicks')

    # Add constraint for maximum cost
    model.addConstr(gp.quicksum(cost_per_click[i] * budget_vars[i] for i in range(num_channels)) <= max_cost_percent * gp.quicksum(avg_ticket_size[p][i] * budget_vars[i] * conversion_rates[p][i] for p in range(num_products) for i in range(num_channels)), name='max_cost')

    # Optimize the model
    model.optimize()

    if model.status == GRB.OPTIMAL:
        optimal_allocations = [budget_vars[i].x for i in range(num_channels)]
        total_profit = model.objVal
        return optimal_allocations, total_profit
    else:
        return None, None

# Example Usage
if __name__ == "__main__":
    input_data = OptimizationInput(
        conversion_rates=[[0.04, 0.01, 0.015], [0, 0.03, 0.015], [0.01, 0, 0.015]],
        avg_ticket_size=[[25, 55, 55], [0, 60, 70], [40, 0, 80]],
        cost_per_click=[1.1, 1.6, 1.9],
        total_budget=10000,
        min_budget_percent=0.15,
        min_transactions_per_product=[50, 55, 60],
        min_clicks=7000,
        max_cost_percent=0.80
    )

    allocations, profit = optimize_budget_func(input_data)
    if allocations is not None:
        print("Optimal Budget Allocations:", allocations)
        print("Total Profit:", profit)
    else:
        print("No solution found.")
