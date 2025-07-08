import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from locness_app.config import resample as RESAMPLE, file_path as FILE_PATH
from locness_app.data import get_data_for_plotting, get_total_records
from locness_app.plots import create_timeseries_plot, create_map_plot

# TODO: automatically resample if plotting more than MAX_POINTS
# TODO: add more error handling for database connections and queries
# TODO: incremental automatic update
# TODO: threshold exceeded colors
# TODO: threshold exceeded notifications
# TODO: threshold exeeded timing
# TODO: link plot and map for data selection by area or time
# TODO: add csv export
# TODO: add sensor diagnostics (if using primary sqlite database)
# TODO: add drifters
# TODO: add more vis: ph vs rhodamine, salinity vs temperature, etc.

# Page configuration
st.set_page_config(
    page_title="LOCNESS Underway Dashboard",
    page_icon="🌊",
    layout="wide"
)


# Streamlit UI

# Sidebar controls
st.sidebar.header("Configuration")

# Data selection
st.sidebar.subheader("Data Selection")
available_params = ['temp', 'salinity', 'rhodamine', 'ph', 'ph_ma']
selected_params = st.sidebar.multiselect(
    "Select parameters to plot",
    available_params,
    default=['rhodamine', 'ph']
)

# Resampling options
st.sidebar.subheader("Data Resampling")
resample_options = {
    'No resampling': None,
    '10 seconds': '10s',
    '1 minute': '1min',
    '5 minutes': '5min',
    '15 minutes': '15min',
    '1 hour': '1h',
    '6 hours': '6h'
}
default_resample_index = list(resample_options.values()).index(RESAMPLE) if RESAMPLE in resample_options.values() else 2
selected_resample = st.sidebar.selectbox(
    "Resample to:",
    list(resample_options.keys()),
    index=default_resample_index
)

# Time range
st.sidebar.subheader("Time Range")
time_range_hours = st.sidebar.slider(
    "Hours of data to show",
    min_value=1,
    max_value=168,  # 1 week
    value=24
)

# Data Status
st.sidebar.subheader("Data Status")
status_container = st.sidebar.empty()

# Main content area
col1, col2 = st.columns([2, 1])

# Create containers for dynamic content
map_container = st.empty()
plot_container = st.empty()
stats_container = st.empty()

# Update the data query based on user selections
time_cutoff = datetime.now() - timedelta(hours=time_range_hours)
df = get_data_for_plotting(db_path=FILE_PATH, time_cutoff=time_cutoff, resample_freq=resample_options[selected_resample])

last_update = datetime.now()

# Add total number of records in the data source
total_records = get_total_records(db_path=FILE_PATH)
# Update status
with status_container:
    if not df.empty:
        st.success(f"✅ Data loaded: {len(df)} records")
        st.markdown(
            f"✅ Data loaded: {len(df)} records  \n"
            f"**Total records in data source:** {total_records}  \n"
            f"**Last update:** {last_update.strftime('%H:%M:%S')}  \n"
            f"**Latest data:** {df.index[-1].strftime('%H:%M:%S')}  \n"
        )
    else:
        st.warning("⚠️ No data available")

# Display visualizations
if not df.empty and selected_params:
    with map_container:
        st.plotly_chart(create_map_plot(df, selected_params), use_container_width=True)
    with plot_container:
        st.plotly_chart(create_timeseries_plot(df, selected_params), use_container_width=True)
    with stats_container:
        st.subheader("Current Statistics")
        if not df.empty:
            latest_data = df.iloc[-1]
            cols = st.columns(len(selected_params))
            for i, param in enumerate(selected_params):
                with cols[i]:
                    if param in df.columns:
                        value = latest_data[param]
                        mean_val = df[param].mean()
                        st.metric(
                            label=param.capitalize(),
                            value=f"{value:.2f}",
                            delta=f"{value - mean_val:.2f} vs avg"
                        )
elif not selected_params:
    st.info("Please select at least one parameter to visualize from the sidebar.")

# Footer
st.markdown("---")
st.markdown("💡 **Tips:** Use the sidebar to configure update frequency, select parameters, and adjust resampling options.")
