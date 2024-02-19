import streamlit as st
import pandas as pd
import altair as alt
from db import get_db_conn
import datetime
from dateutil.relativedelta import relativedelta

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

# Group events by month and count the occurrences
df_all_data['month'] = pd.to_datetime(df_all_data['date']).dt.month
month_counts = df_all_data['month'].value_counts().reset_index()
df_all_data['month'] = pd.to_datetime(df_all_data['date']).dt.month_name()
month_counts = df_all_data['month'].value_counts().reset_index()
month_counts.columns = ['Month', 'EventCount']

# Chart: Month of events
st.subheader("What month has the most number of events?")
chart_month = alt.Chart(month_counts).mark_bar().encode(
    x=alt.X('EventCount:Q', title='Number of Events'),
    y=alt.Y('Month:N', title='Month', sort='-x')
).properties(width=600, height=400)
st.altair_chart(chart_month)

# Group events by day of the week and count the occurrences
df_all_data['day_of_week'] = pd.to_datetime(df_all_data['date']).dt.day_name()
day_counts = df_all_data['day_of_week'].value_counts().reset_index()
day_counts.columns = ['DayOfWeek', 'EventCount']

# Chart: Day of the week with most events
st.subheader("What day of the week has the most number of events?")
chart_day = alt.Chart(day_counts).mark_bar().encode(
    x=alt.X('EventCount:Q', title='Number of Events'),
    y=alt.Y('DayOfWeek:N', title='Day of the Week', sort='-x')
).properties(width=600, height=400)
st.altair_chart(chart_day)

# Group events by location and count the occurrences
location_counts = df_all_data['location'].value_counts().reset_index()
location_counts.columns = ['Location', 'EventCount']

# Chart: Location of events
st.subheader("Where are events often held?")
chart_location = alt.Chart(location_counts).mark_bar().encode(
    x=alt.X('EventCount:Q', title='Number of Events'),
    y=alt.Y('Location:N', title='Event Location', sort='-x')
).properties(width=600, height=400)
st.altair_chart(chart_location)

# Feature: Data Filtering and Sorting

# Category filter
include_all_categories = st.checkbox("Include All Categories")
if include_all_categories:
    selected_category = df_all_data['event_type'].unique()
else:
    selected_category = st.multiselect("Select categories", df_all_data['event_type'].unique())

# Location filter
include_all_locations = st.checkbox("Include All Locations")
if include_all_locations:
    selected_location = df_all_data['location'].unique()
else:
    selected_location = st.multiselect("Select locations", df_all_data['location'].unique())

# Temperature filter
include_all_temperatures = st.checkbox("Include All Temperatures")
if include_all_temperatures:
    selected_temperature_min = float(df_all_data['temperature'].min())
    selected_temperature_max = float(df_all_data['temperature'].max())
else:
    temperature_range = st.slider("Select temperature range", float(df_all_data['temperature'].min()), float(df_all_data['temperature'].max()), (float(df_all_data['temperature'].min()), float(df_all_data['temperature'].max())))
    selected_temperature_min, selected_temperature_max = temperature_range


# Date range selector
include_all_dates = st.checkbox("Include All Dates")
if include_all_dates:
    start_date = datetime.datetime.now().date()
    end_date = datetime.datetime.now().date() + relativedelta(months=6)
else:
    start_date = st.date_input("Select start date")
    end_date = st.date_input("Select end date")

# Convert start_date and end_date to datetime objects
start_date = datetime.datetime(start_date.year, start_date.month, start_date.day)
end_date = datetime.datetime(end_date.year, end_date.month, end_date.day)

# Convert 'date' column to datetime objects
df_all_data['date'] = pd.to_datetime(df_all_data['date'])

# Apply filters
filtered_data = df_all_data[
    (df_all_data['event_type'].isin(selected_category)) &
    (df_all_data['date'].between(start_date, end_date)) &
    (df_all_data['location'].isin(selected_location)) &
    (df_all_data['temperature'].between(selected_temperature_min, selected_temperature_max))
]


# Clear filter button
if st.button("Clear Filter"):
    selected_category = None
    selected_location = None
    selected_temperature_min = float(df_all_data['temperature'].min())
    selected_temperature_max = float(df_all_data['temperature'].max())
    start_date = None
    end_date = None
    filtered_data = df_all_data


# Sort data
sort_by = st.selectbox("Sort by", ['date', 'event_type', 'location', 'temperature'])
sort_order = st.selectbox("Sort order", ['ascending', 'descending'])

if sort_order == 'ascending':
    sorted_data = filtered_data.sort_values(by=sort_by)
else:
    sorted_data = filtered_data.sort_values(by=sort_by, ascending=False)

# Display the filtered and sorted data in a table
st.subheader("Filtered and Sorted Data")
st.write(sorted_data)

# Close the database connection
conn.close()

