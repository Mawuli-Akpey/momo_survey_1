import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import pydeck as pdk
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
# Ensure correct UTC parsing
df['start'] = pd.to_datetime(df['start'], utc=True, errors='coerce')
df['end'] = pd.to_datetime(df['end'], utc=True, errors='coerce')

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

df_filtered = df[(df['start'].dt.date >= start_date) & (df['end'].dt.date <= end_date)]

# Enumerator filter
enumerator_options = df_filtered['Enumerator'].dropna().unique()
selected_enumerator = st.sidebar.selectbox("Select Enumerator", options=['All'] + list(enumerator_options))

if selected_enumerator != 'All':
    df_filtered = df_filtered[df_filtered['Enumerator'] == selected_enumerator]

# Calculate form completion time
df_filtered['completion_time'] = (df_filtered['end'] - df_filtered['start']).dt.total_seconds() / 60

#########################
# 1) Plotly Scatter Map #
#########################

geo_df = df_filtered.dropna(subset=['_start-geopoint_latitude', '_start-geopoint_longitude'])
if not geo_df.empty:
    fig_map = px.scatter_mapbox(
        geo_df,
        lat="_start-geopoint_latitude",
        lon="_start-geopoint_longitude",
        hover_name="Enumerator",
        title="Geolocation of Survey Responses by Enumerator",
        mapbox_style="open-street-map",
        zoom=12,  # Adjust zoom level for better visibility
        color="Enumerator",
        size_max=15
    )
    st.subheader("📍 Enumerator Locations")
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No geolocation data available for mapping.")

#########################################
# 2) PyDeck Flight PathLayer + Numbered Annotations #
#########################################

if not df_filtered.empty:
    route_data = df_filtered.dropna(subset=["_start-geopoint_latitude", "_start-geopoint_longitude"])
    route_data = route_data.sort_values(by=['Enumerator','start']).reset_index(drop=True)

    layers = []

    # Color dictionary for enumerators
    color_map = {
        "Shadrach": [255, 0, 0],
        "Hetty": [0, 255, 0],
        "Charles Agyarko": [0, 0, 255],
        "Patience": [255, 165, 0],
        "Charles Aidoo": [139, 0, 139]
    }

    annotation_data = []

    for enumerator, group in route_data.groupby('Enumerator'):
        group = group.sort_values('start').reset_index(drop=True)

        if len(group) > 1:
            arc_data = [{
                "start": [group.iloc[i]['_start-geopoint_longitude'], group.iloc[i]['_start-geopoint_latitude']],
                "end": [group.iloc[i+1]['_start-geopoint_longitude'], group.iloc[i+1]['_start-geopoint_latitude']],
                "Enumerator": enumerator
            } for i in range(len(group) - 1)]

            arc_layer = pdk.Layer(
                "ArcLayer",
                data=arc_data,
                get_source_position="start",
                get_target_position="end",
                get_source_color=f"[{color_map.get(enumerator,[200,30,0])[0]}, {color_map.get(enumerator,[200,30,0])[1]}, {color_map.get(enumerator,[200,30,0])[2]}, 160]",
                get_target_color=f"[{color_map.get(enumerator,[200,30,0])[0]}, {color_map.get(enumerator,[200,30,0])[1]}, {color_map.get(enumerator,[200,30,0])[2]}, 160]",
                width_min_pixels=3,
                pickable=True
            )
            layers.append(arc_layer)

        for i, row in group.iterrows():
            annotation_data.append({
                "Enumerator": enumerator,
                "order": str(i+1),
                "lat": row['_start-geopoint_latitude'],
                "lon": row['_start-geopoint_longitude']
            })

    text_layer = pdk.Layer(
        "TextLayer",
        data=annotation_data,
        get_position=["lon", "lat"],  # Correct position format
        get_text="order",
        get_color="[0, 0, 0]",  # Black text for visibility
        get_size=18,  # Bigger text for clarity
        get_alignment_baseline="center",
        get_anchor="middle",
        pickable=True
    )
    layers.append(text_layer)

    tooltip = {
        "html": """
<b>Enumerator:</b> {Enumerator}<br/>
<b>Order:</b> {order}
""",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    view_state = pdk.ViewState(
        latitude=route_data['_start-geopoint_latitude'].mean(),
        longitude=route_data['_start-geopoint_longitude'].mean(),
        zoom=12,  # Adjust zoom level for better visibility
        pitch=50
    )

    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=layers,
        tooltip=tooltip
    )

    st.subheader("✈ Enumerator Flight Paths with Order Numbers")
    st.pydeck_chart(deck)
else:
    st.warning("No valid geolocation data available for mapping routes.")










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

plot_distribution("What was the total MOMO business income earned during a typical month after paying all expenses (including wages of employees), but not including any income you [owner] paid yourself? ", "Distribution of Income")

# Bar Chart: Count of "Consider the last 7 days/ last week: How often did you decline a customer’s transaction due to insufficient liquidity on your e-credit or cash-in-hand? "
decline_count = df_filtered["Consider the last 7 days/ last week: How often did you decline a customer’s transaction due to insufficient liquidity on your e-credit or cash-in-hand? "].value_counts()
plot_annotated_bar(decline_count, "Frequency of Declined Transaction in Past 7 days")

# Bar Chart: Count of " If the MNO provided more clarification regarding the computation of your cash-in commission, how would it affect your happiness/satisfaction with your work?"
satisfaction_count = df_filtered[" If the MNO provided more clarification regarding the computation of your cash-in commission, how would it affect your happiness/satisfaction with your work?"].value_counts()
plot_annotated_bar(satisfaction_count, "Satisfation Rating of Cash-in Computation Clarification")

# Bar Chart: Count of "Do you believe it is good to post tariffs to improve transparency?"
transparency = df_filtered["Do you believe it is good to post tariffs to improve transparency?"].value_counts()
plot_annotated_bar(transparency, "Thoughts on Transparency")

# Bar Chart: Count of "Does receiving lower than expected cash-in commission encourage you to charge higher tariffs?"
tariff1 = df_filtered["Does receiving lower than expected cash-in commission encourage you to charge higher tariffs?"].value_counts()
plot_annotated_bar(tariff1, "How Cash-in Commission Affects Charges on Tarriffs")
