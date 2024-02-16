import streamlit as st
import pandas as pd
import altair as alt
from db import get_db_conn

# Title
st.title("Seattle Events Dashboard")

# Connect to the database
conn = get_db_conn()

# Feature 1: Data Visualization

# Load data from the database
query = """
    SELECT event_type AS Category, COUNT(*) AS EventCount
    FROM events
    GROUP BY event_type
    ORDER BY EventCount DESC
"""
df_category = pd.read_sql_query(query, conn)

# Chart 1: Category of events
st.subheader("1. What category of events are most common in Seattle?")
chart1 = alt.Chart(df_category).mark_bar().encode(
    x=alt.X('EventCount:Q', title='Number of Events'),
    y=alt.Y('Category:N', title='Event Category', sort='-x')
).properties(width=600, height=400)
st.altair_chart(chart1)

# Chart 2: Number of events per month
query = """
    SELECT EXTRACT(MONTH FROM date) AS Month, COUNT(*) AS EventCount
    FROM events
    GROUP BY Month
    ORDER BY Month
"""
df_month = pd.read_sql_query(query, conn)
st.subheader("2. What month has the most number of events?")
chart2 = alt.Chart(df_month).mark_line(point=True).encode(
    x='Month:O',
    y='EventCount:Q'
).properties(width=600, height=400)
st.altair_chart(chart2)

# Chart 3: Number of events per day of the week
query = """
    SELECT EXTRACT(DOW FROM date) AS DayOfWeek, COUNT(*) AS EventCount
    FROM events
    GROUP BY DayOfWeek
    ORDER BY DayOfWeek
"""
df_day_of_week = pd.read_sql_query(query, conn)
st.subheader("3. What day of the week has the most number of events?")
chart3 = alt.Chart(df_day_of_week).mark_bar().encode(
    x=alt.X('DayOfWeek:O', title='Day of the Week'),
    y=alt.Y('EventCount:Q', title='Number of Events')
).properties(width=600, height=400)
st.altair_chart(chart3)

# Feature 2: Data Controls

# Filter by category
st.sidebar.subheader("Filter by Category")
category_options = df_category['Category'].tolist()
selected_category = st.sidebar.selectbox("Select a category", category_options)

# Filter by date range
st.sidebar.subheader("Date Range Selector")
date_range = st.sidebar.date_input("Select a date range")

# Filter by location
st.sidebar.subheader("Filter by Location")
location_options = df['location'].unique().tolist()
selected_location = st.sidebar.selectbox("Select a location", location_options)

# Filter by weather
st.sidebar.subheader("Filter by Weather")
weather_options = ["Sunny", "Rainy", "Cloudy"]  # Add your weather options
selected_weather = st.sidebar.selectbox("Select weather condition", weather_options)

# Feature 3: Data Display
st.subheader("Filtered Data")
query = f"""
    SELECT *
    FROM events
    WHERE event_type = '{selected_category}'
    AND date >= '{date_range[0]}' AND date <= '{date_range[1]}'
    AND location = '{selected_location}'
    AND weather_forecast = '{selected_weather}'
"""
filtered_df = pd.read_sql_query(query, conn)
st.write(filtered_df)

# Close the database connection
conn.close()
