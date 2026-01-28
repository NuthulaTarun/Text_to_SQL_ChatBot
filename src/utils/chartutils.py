import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.constants import CHART_RESPONSE

def format_string(input_string):
    prepositions_conjunctions = {
        "on",
        "in",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "and",
        "or",
        "but",
        "if",
        "while",
        "of",
        "as",
    }

    words = input_string.split("_")
    formatted_words = []

    for i, word in enumerate(words):
        if word in prepositions_conjunctions and i != 0:
            formatted_words.append(word)
        else:
            formatted_words.append(word.capitalize())

    return " ".join(formatted_words)


def generate_chart(df, intent_type, plot_columns):
    try:
        if intent_type == "forecasting":
            
            column_values = df["column"].unique().tolist()
            for i in column_values:
                if i!= "forecasted_value":
                    feature = i
                
            df["column"] = df["column"].apply(lambda x: "current" if x==feature else "forecast")      
            # Define a color map
            color_map = {
                "current": "blue",
                "forecast": "green",
            }

            # Plot the line chart
            fig = px.line(
                df,
                x="date",
                y="value",
                color="column",
                title=f'Current vs Forecasted values for {feature}',
                color_discrete_map=color_map,
                template="seaborn",
                markers=True,
            )
        else:
            if intent_type != "optimization":
                df = df[plot_columns].reset_index(drop=True)
            if len(df.columns) == 2:
                if (df.dtypes[1] in ["int64", "int32", "float64"] 
                    and len(df) > 1):
                    fig = px.bar(
                        df,
                        x=df.columns[0],
                        y=df.columns[1],
                        title=f"{format_string(df.columns[1])} by {format_string(df.columns[0])}",
                        template="plotly_white",
                        color=df.columns[0],
                    )
                elif (
                    df.dtypes[0] in ["int64", "int32", "float64"]
                    and df.dtypes[1] in ["int64", "int32", "float64"]
                    and len(df) > 1
                ):
                    fig = px.line(
                        df,
                        x=df.columns[0],
                        y=df.columns[1],
                        title=f"{format_string(df.columns[-1])} Over {format_string(df.columns[0])}, {format_string(df.columns[1])}",
                        template="seaborn",
                        color=df.columns[1],
                        markers=True,
                    )
                else:
                    print(CHART_RESPONSE)
                    return
            elif len(df.columns) >= 3:
                if (
                    df.dtypes[0] in ["object"]
                    and df.dtypes[1] in ["int64", "int32", "float64"]
                    and df.dtypes[-1] in ["int64", "int32", "float64"]
                ):
                    fig = px.bar(
                        df,
                        x=df.columns[0],
                        y=df.columns[-1],
                        title=f"{format_string(df.columns[0])} Over {format_string(df.columns[-1])}",
                        template="ggplot2",
                        color=df.columns[1],
                    )
                elif (
                    df.dtypes[0] in ["object"]
                    and df.dtypes[1] in ["object"]
                    and df.dtypes[-1] in ["int64", "int32", "float64"]
                ):
                    fig = px.line(
                        df,
                        x=df.columns[0],
                        y=df.columns[-1],
                        title=f"{format_string(df.columns[-1])} Over {format_string(df.columns[0])}, {format_string(df.columns[1])}",
                        template="seaborn",
                        color=df.columns[1],
                        markers=True,
                    )
                else:
                    print(CHART_RESPONSE)
                    return
            else:
                print(CHART_RESPONSE)
                return

        # Update layout to center the title and improve readability
        fig.update_layout(
            title={
                "text": fig.layout.title.text,  # Reapply the title
                # 'y': 0.9,  # Adjust vertical position if needed
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title=format_string(df.columns[0]),  # Format x-axis title
            yaxis_title=format_string(df.columns[-1]),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        print(f"exception at generating chart {e}")
        print(CHART_RESPONSE)
        return
