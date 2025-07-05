import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from locness_app.config import update_frequency as UPDATE_FREQUENCY, resample as RESAMPLE, file_path as FILE_PATH
from locness_app.data import DataManager
from locness_app.plots import create_timeseries_plot, create_map_plot

# Page configuration
st.set_page_config(
    page_title="Oceanographic Data Visualizer",
    page_icon="🌊",
    layout="wide"
)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = pd.DataFrame()
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager(FILE_PATH)

def get_data_for_plotting(time_cutoff=None, resample_freq=None):
    return st.session_state.data_manager.get_data_for_plotting(time_cutoff, resample_freq)

# Streamlit UI

# Sidebar controls
st.sidebar.header("Configuration")

# Update frequency
try:
    update_frequency = int(UPDATE_FREQUENCY)
except Exception:
    update_frequency = 10
update_frequency = st.sidebar.slider(
    "Update Frequency (seconds)",
    min_value=1,
    max_value=60,
    value=update_frequency,
    help="How often to check for new data"
)

# Data selection
st.sidebar.subheader("Data Selection")
available_params = ['temp', 'salinity', 'rhodamine', 'ph']
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

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)

# Manual refresh button
if st.sidebar.button("Refresh Now"):
    st.session_state.last_update = datetime.now() - timedelta(seconds=update_frequency)

# Data Status
st.sidebar.subheader("Data Status")
status_container = st.sidebar.empty()

# Main content area
col1, col2 = st.columns([2, 1])

# Create containers for dynamic content
map_container = st.empty()
plot_container = st.empty()
stats_container = st.empty()

# Initialize or update data
time_since_update = (datetime.now() - st.session_state.last_update).total_seconds()

if auto_refresh and time_since_update >= update_frequency:
    cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
    resample_freq = resample_options[selected_resample]
    df = get_data_for_plotting(cutoff_time, resample_freq)
    st.session_state.data_cache = df
    st.session_state.last_update = datetime.now()
    st.rerun()
elif st.session_state.data_cache.empty:
    cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
    resample_freq = resample_options[selected_resample]
    df = get_data_for_plotting(cutoff_time, resample_freq)
    st.session_state.data_cache = df
else:
    df = st.session_state.data_cache

# Update status
with status_container:
    if not df.empty:
        st.success(f"✅ Data loaded: {len(df)} records")
        st.markdown(
            f"✅ Data loaded: {len(df)} records  \n"
            f"**Last update:** {st.session_state.last_update.strftime('%H:%M:%S')}  \n"
            f"**Latest data:** {df.index[-1].strftime('%H:%M:%S')}  \n"
            f"**Next update in:** {max(0, update_frequency - int((datetime.now() - st.session_state.last_update).total_seconds()))} seconds"
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
