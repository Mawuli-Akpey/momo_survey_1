import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import io

# Set Streamlit page configuration
st.set_page_config(page_title="Survey Dashboard", layout="wide")

# Title of the dashboard
st.title("📊 Mobile Money Agent Survey Dashboard")

# API URL
api_url = "https://kf.kobotoolbox.org/api/v2/assets/admPvpSoxSNXxP8KwPuDg3/export-settings/esH4UyhzPw76PJcvLPw8EHk/data.csv"

# Fetch data from API
response = requests.get(api_url)
if response.status_code == 200:
    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), delimiter=";")
else:
    st.error(f"Failed to retrieve data: {response.status_code}")
    st.stop()

# Convert start and end times to datetime
df['start'] = pd.to_datetime(df['start'], errors='coerce')
df['end'] = pd.to_datetime(df['end'], errors='coerce')

# Enumerator mapping
enumerator_mapping = {
    "collect:7McKQdhzVD5lVwAt": "Shadrach",
    "collect:zOVGOiuiKdhvkEFf": "Hetty",
    "collect:NYXsL466TQLkROha": "Charles Agyarko",
    "collect:xdUQW0gruIuCxHeK": "Patience",
    "collect:hglxKjNr4BVzkskU": "Charles Aidoo"
}

df['Enumerator'] = df['deviceid'].map(enumerator_mapping)

# Sidebar Filters
st.sidebar.header("📅 Filter by Date")
start_date = st.sidebar.date_input("Start Date", df['start'].min().date())
end_date = st.sidebar.date_input("End Date", df['end'].max().date())

# Filter DataFrame by date range
df_filtered = df[(df['start'].dt.date >= start_date) & (df['end'].dt.date <= end_date)]

# Calculate Form Completion Time
df_filtered['completion_time'] = (df_filtered['end'] - df_filtered['start']).dt.total_seconds() / 60

# Key Statistics
total_submissions = len(df_filtered)
total_men = df_filtered[df_filtered['Sex of Agent'] == 'Male'].shape[0]
total_women = df_filtered[df_filtered['Sex of Agent'] == 'Female'].shape[0]
avg_completion_time = df_filtered['completion_time'].mean()

# Geolocation Data
geo_df = df_filtered.dropna(subset=['_start-geopoint_latitude', '_start-geopoint_longitude'])

# Display Key Metrics in One Row
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📄 Total Submissions", total_submissions)
col2.metric("👨 Total Men", total_men)
col3.metric("👩 Total Women", total_women)
col4.metric("⏳ Avg Completion Time (mins)", round(avg_completion_time, 2))
col5.metric("🗺️ Entries with Geolocation", len(geo_df))

# Geolocation Mapping
if not geo_df.empty:
    fig_map = px.scatter_mapbox(
        geo_df,
        lat="_start-geopoint_latitude",
        lon="_start-geopoint_longitude",
        hover_name="Enumerator",
        title="Geolocation of Survey Responses by Enumerator",
        mapbox_style="open-street-map",
        zoom=10,
        color="Enumerator",
        size_max=15
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No geolocation data available for mapping.")

# Function to create annotated bar charts
def plot_annotated_bar(data, title):
    fig = px.bar(data, x=data.index, y=data.values, title=title, text_auto=True)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# Bar Chart: Count of submissions per enumerator
enumerator_count = df_filtered["Enumerator"].value_counts()
plot_annotated_bar(enumerator_count, "Submissions Per Enumerator")

# Display DataFrame
st.subheader("📋 Last 10 Survey Responses")
st.dataframe(df_filtered.tail(10))

# Bar Chart: Count of "Are you the owner of this Mobile Money business?"
ownership_count = df_filtered["Are you the owner of this Mobile Money business?"].value_counts()
plot_annotated_bar(ownership_count, "Ownership of Mobile Money Business")

# Bar Chart: Count of "Have you operated this business for more than 6 months?"
operation_count = df_filtered["Have you operated this business for more than 6months?"].value_counts()
plot_annotated_bar(operation_count, "Business Operation Duration (More than 6months)")

# Percentage of "Yes" responses in Ownership and Experience
ownership_yes_percentage = (df_filtered["Are you the owner of this Mobile Money business?"].value_counts(normalize=True) * 100).get("Yes", 0)
operation_yes_percentage = (df_filtered["Have you operated this business for more than 6months?"].value_counts(normalize=True) * 100).get("Yes", 0)

# Display Percentage Metrics
col6, col7 = st.columns(2)
col6.metric("✅ % Owners of MoMo Business", f"{ownership_yes_percentage:.2f}%")
col7.metric("📈 % Experienced Operators (6+ months)", f"{operation_yes_percentage:.2f}%")

# Function to create distribution plots
def plot_distribution(column, title):
    fig = px.histogram(df_filtered, x=column, nbins=20, title=title, text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# Distribution of Age
plot_distribution("How old are you? (In years)", "Distribution of Age")

