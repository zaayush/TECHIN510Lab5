import streamlit as st
import pandas as pd
import altair as alt
from db import get_db_conn

# Title
st.title("Seattle Events Dashboard")

# Connect to the database
conn = get_db_conn()

# Load data from the database
query_all_data = """
    SELECT *
    FROM events
"""
df_all_data = pd.read_sql_query(query_all_data, conn)

# Feature: Data Visualization

# Group events by category and count the occurrences
category_counts = df_all_data['event_type'].value_counts().reset_index()
category_counts.columns = ['Category', 'EventCount']

# Chart: Category of events
st.subheader("What category of events are most common in Seattle?")
chart = alt.Chart(category_counts).mark_bar().encode(
    x=alt.X('EventCount:Q', title='Number of Events'),
    y=alt.Y('Category:N', title='Event Category', sort='-x')
).properties(width=600, height=400)
st.altair_chart(chart)

# Display the data in a table
st.subheader("Seattle Events Data")
st.write(df_all_data)

# Close the database connection
conn.close()
