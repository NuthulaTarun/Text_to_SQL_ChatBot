from google.cloud import bigquery
import ast
import re
import os
import json
from typing import List, Set


def get_result(query):
    client = bigquery.Client(project=os.getenv("PROJECT"))
    # Set the default dataset in the query job configuration
    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{os.getenv('PROJECT')}.{os.getenv('DATASET_POC')}"
    )
    # Run the query to get the result
    query_job = client.query(query, job_config=job_config)

    # Wait for the query to complete
    result = query_job.result()

    # Initialize an empty list to store row dictionaries
    rows = []

    # Iterate over the rows in the result
    for row in result:
        # Convert each row to a dictionary
        row_dict = {field.name: row[field.name] for field in result.schema}
        rows.append(row_dict)

    return rows


def normalize_whitespace(query):
    # Replace multiple whitespace characters (including newlines) with a single space
    return re.sub(r"\s+", " ", query)


def extract_select_statements(query):
    query = normalize_whitespace(query)
    return find_select_statements(query)


def find_select_statements(query, start_pos=0):
    select_statements = []
    select_pattern = re.compile(
        r"(select\s+)(.*?)(\s+from\s+|\s*$)", re.IGNORECASE | re.DOTALL
    )

    while True:
        match = select_pattern.search(query, start_pos)
        if not match:
            break

        select_statement = match.group(0).strip()
        select_statements.append(select_statement)

        # Find nested SELECT statements within the current one
        from_end_pos = match.end()
        nested_select_statements = find_select_statements(query, from_end_pos)
        select_statements.extend(nested_select_statements)

        start_pos = from_end_pos

    return select_statements


def validate_and_correct_sql(sql: str, valid_columns: Set[str]) -> str:
    def process_select(select_stmt: str) -> str:
        # Extract columns from the SELECT statement
        columns_match = re.search(
            r"\bSELECT\s+(.*?)(?:\s+FROM|\s*$)", select_stmt, re.IGNORECASE | re.DOTALL
        )
        if not columns_match:
            return select_stmt

        columns = columns_match.group(1)
        column_list = re.split(r",\s*(?=(?:[^()]*\([^()]*\))*[^()]*$)", columns)
        valid_column_list = []

        has_star = False
        for col in column_list:
            col = col.strip()

            # Handle * separately
            if col == "*":
                has_star = True
                valid_column_list.append(col)
                continue

            # Handle aggregate functions and special cases
            agg_match = re.match(
                r"(AVG|SUM|COUNT|MAX|MIN|ROW_NUMBER|ROUND|CAST|DATE_TRUNC|COALESCE)\s*\((.*?)\)", col, re.IGNORECASE
            )
            if agg_match or "OVER" in col.upper():
                valid_column_list.append(col)
                continue

            # Check if the column is valid
            if col in valid_columns:
                valid_column_list.append(col)

        # If we have a star, keep it at the beginning of the list
        if has_star:
            valid_column_list = ["*"] + [col for col in valid_column_list if col != "*"]

        # Replace the original columns with the valid ones
        return select_stmt.replace(columns, ", ".join(valid_column_list))

    # Process the entire SQL statement
    corrected_sql = process_select(sql.lower())

    return corrected_sql


def modified_query(query, project_id, dataset_id):
    if "join" in query.lower():
        return normalize_whitespace(query).strip()  
    valid_columns = get_valid_columns(
        project_id=project_id,
        dataset_id=dataset_id,
        table_name=get_table_name(query=query),
    )
    subqueries = find_select_statements(query)
    modified_query_dict = {}
    if len(subqueries) > 0:
        # correcting sub queries
        for i in subqueries:
            modified_query_dict[i] = validate_and_correct_sql(i, valid_columns)
        for k, v in modified_query_dict.items():
            query = query.replace(k, v)
    return normalize_whitespace(query).strip()


def get_valid_columns(project_id, dataset_id, table_name):
    client = bigquery.Client(project=project_id)
    parts = table_name.split(".")

    if len(parts) == 3:
        project_id, dataset_id, table_name = parts
    elif len(parts) == 2:
        dataset_id, table_name = parts
    elif len(parts) == 1:
        table_name = parts[0]
    else:
        raise ValueError("Table name format is not correct.")

    table_id = f"{project_id}.{dataset_id}.{table_name}"

    table = client.get_table(table_id)
    return {field.name.lower() for field in table.schema}


def get_table_name(query):
    if "cleaned_public_events_data" in query:
        return "cleaned_public_events_data"
    elif "google_ads_data" in query:
        return "google_ads_data"    
    else:
        raise ValueError("Table name could not be found in the query.")