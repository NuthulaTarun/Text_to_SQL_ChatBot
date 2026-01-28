# import libraries
from google.cloud import bigquery
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

# import pymoo library
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.core.repair import Repair

load_dotenv()

# Initialize a BigQuery client
client = bigquery.Client()


def get_bigquery_data(project_id, dataset_id, table_name, sql_query):
    # Construct a full table ID
    table_full_id = f"{project_id}.{dataset_id}.{table_name}"

    # Query the table and load the data into a Pandas DataFrame
    query = f"{sql_query} {table_full_id}"
    df = client.query(query).to_dataframe()
    return df


project_id = os.getenv("PROJECT")
dataset_id = os.getenv("DATASET_POC")

# getting ads data
ads_table = "google_ads_data"
ads_query = "SELECT * FROM "
df_ads = get_bigquery_data(project_id, dataset_id, ads_table, ads_query)

# aggregating ads data at search_keyword to get sum of total cost
df_ads.columns = df_ads.columns.str.strip().str.replace(" ", "_").str.lower()
df_ads["sum_cost"] = df_ads.groupby("search_keyword")["cost"].transform("sum")
df_ads_aggregated = df_ads[["search_keyword", "sum_cost"]].drop_duplicates()

# getting events data
events_table = "cleaned_public_events_data"
events_query = "SELECT transactions, keyword, transactionRevenue FROM "
df_events = get_bigquery_data(project_id, dataset_id, events_table, events_query)

# aggregating events data at keyword to get sum of total transactionRevenue
df_events_aggregated = (
    df_events[df_events.transactions > 0]
    .groupby("keyword")["transactionRevenue"]
    .sum()
    .reset_index()
)

# joining aggregated ads and events data
df_final_aggregated = df_events_aggregated.merge(
    df_ads_aggregated, left_on="keyword", right_on="search_keyword", how="left"
)
df_final_aggregated = df_final_aggregated.dropna(subset=["search_keyword", "sum_cost"])

### optimization code ###
# Defining list of variables
costs = df_final_aggregated["sum_cost"].values
revenues = df_final_aggregated["transactionRevenue"].values
keywords = df_final_aggregated["keyword"]

total_budget = 1000  # Example total budget limit
cost_increase_factor = 2


# Define the custom optimization problem
class KeywordOptimizationProblem(Problem):
    def __init__(self, costs, revenues, total_budget):
        self.costs = costs
        self.revenues = revenues
        self.total_budget = total_budget
        super().__init__(n_var=len(costs), n_obj=1, n_constr=0, xl=0, xu=total_budget)

    def _evaluate(self, X, out, *args, **kwargs):
        # Avoid spending on keywords with zero espend_allocationpected revenue
        X = np.where(self.revenues > 0, X, 0)

        # Compute total revenue and total impression share
        # total_revenue = np.sum(X * self.revenues, axis=1)

        # Store per-keyword revenue and impression share
        revenue_per_keyword = X * self.revenues

        # Objective functions (negated to maximize)
        out["F"] = -np.column_stack([costs])

        # Store the per-keyword allocations and results
        out["revenue_per_keyword"] = revenue_per_keyword
        out["spend_allocations"] = X


# Define the custom repair operator
class BudgetRepair(Repair):
    def __init__(self, total_budget):
        super().__init__()
        self.total_budget = total_budget
        self.cost_increase_factor = cost_increase_factor
        self.original_costs = costs

    def _do(self, problem, X, **kwargs):
        for i in range(len(X)):
            total_spend = np.sum(X[i])
            if total_spend > self.total_budget:
                X[i] = X[i] * (self.total_budget / total_spend)

        X = np.where(problem.revenues > 0, X, 0)
        return X


def get_optimization_results():
    # Set up the problem
    problem = KeywordOptimizationProblem(costs, revenues, total_budget)

    # Set up the repair operator
    repair = BudgetRepair(total_budget)

    # Set up the algorithm
    algorithm = NSGA2(pop_size=5, repair=repair)

    # Run the optimization
    res = minimize(
        problem, algorithm, termination=("n_gen", 200), seed=1, save_history=True
    )

    # Extract the best solution
    best_solution_idx = np.argmin(
        res.F
    )  # Find the index of the best solution based on revenue

    # getting spend values
    best_spend_allocations = res.X[best_solution_idx]
    best_revenue_per_keyword = best_spend_allocations * revenues

    # storing results in dataframe
    result_df = pd.DataFrame()
    result_df["Search_keyword"] = keywords
    result_df["Calculated_Spend"] = best_spend_allocations
    result_df["Expected_revenue"] = best_revenue_per_keyword
    result_df = result_df.sort_values(by=["Calculated_Spend"], ascending= False).reset_index(drop=True)
    return result_df
