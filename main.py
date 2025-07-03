import streamlit as st
import duckdb
from sample_data import add_sample_row
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import numpy as np

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

def get_data_from_db(since_timestamp=None):
    """Fetch data from DuckDB database"""
    con = duckdb.connect('oceanographic_data.duckdb')
    if since_timestamp:
        query = '''
        SELECT * FROM sensor_data 
        WHERE timestamp > ? 
        ORDER BY timestamp
        '''
        df = con.execute(query, [since_timestamp]).df()
    else:
        query = 'SELECT * FROM sensor_data ORDER BY timestamp'
        df = con.execute(query).df()
    con.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    return df

def resample_data(df, resample_freq):
    """Resample data to specified frequency"""
    if df.empty:
        return df
    
    # Define resampling methods for each column
    agg_dict = {
        'lat': 'mean',
        'lon': 'mean',
        'temp': 'mean',
        'salinity': 'mean',
        'rhodamine': 'mean',
        'pH': 'mean'
    }
    
    return df.resample(resample_freq).agg(agg_dict).dropna()

def create_timeseries_plot(df, selected_params):
    """Create timeseries plot for selected parameters with range slider and selectors, but hide x axis labels"""
    if df.empty:
        return go.Figure()
    
    # Create subplot with secondary y-axis if needed
    fig = make_subplots(
        rows=len(selected_params), 
        cols=1,
        subplot_titles=selected_params,
        shared_xaxes=True,
        vertical_spacing=0.05
    )
    
    colors = px.colors.qualitative.Set1
    
    for i, param in enumerate(selected_params):
        if param in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[param],
                    name=param,
                    line=dict(color=colors[i % len(colors)]),
                    mode='lines+markers',
                    marker=dict(size=3)
                ),
                row=i+1, col=1
            )
    
    fig.update_layout(
        height=150 + 200 * len(selected_params),
        title="Time Series Data",
        showlegend=False,
    )
    
    # Update all x-axes for subplots, but hide axis labels
    for i in range(1, len(selected_params) + 1):
        fig.update_xaxes(
            title_text="",  # Remove axis label
            row=i, col=1,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ) if i == 1 else None,
            rangeslider=dict(visible=(i == len(selected_params))),
            type="date"
        )
    
    return fig

def create_map_plot(df):
    """Create map showing all positions and color-coded parameter values"""
    if df.empty:
        return go.Figure()
    
    # Use all data points for the track
    track_data = df

    fig = go.Figure()
    
    # Color scale for the first selected parameter
    if selected_params and selected_params[0] in track_data.columns:
        color_param = selected_params[0]
        color_vals = track_data[color_param]

        # Compute quantiles for color scaling
        qmin = color_vals.quantile(0.05)
        qmax = color_vals.quantile(0.95)
        # Avoid degenerate colorbar
        if qmin == qmax:
            qmin = color_vals.min()
            qmax = color_vals.max()

        scatter = go.Scattermap(
            lat=track_data['lat'],
            lon=track_data['lon'],
            mode='markers+lines',
            marker=dict(
                size=10,
                color=color_vals,
                colorscale='Viridis',
                cmin=qmin,
                cmax=qmax,
                colorbar=dict(title=color_param.capitalize()),
                showscale=True
            ),
            name=f'Track ({color_param})',
            text=[f"{color_param}: {v:.2f}" for v in color_vals],
            hovertemplate=
                'Lat: %{lat:.4f}<br>' +
                'Lon: %{lon:.4f}<br>' +
                f'{color_param}: %{{marker.color:.2f}}<extra></extra>'
        )
        fig.add_trace(scatter)
    else:
        # Add track line without color scale if no param selected
        fig.add_trace(go.Scattermap(
            lat=track_data['lat'],
            lon=track_data['lon'],
            mode='lines',
            line=dict(width=2, color='blue'),
            name='Track',
            hoverinfo='skip'
        ))
    
    # Add latest position
    if not df.empty:
        latest = df.iloc[-1]
        fig.add_trace(go.Scattermap(
            lat=[latest['lat']],
            lon=[latest['lon']],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Current Position',
            hovertemplate='<b>Current Position</b><br>' +
                         'Lat: %{lat:.4f}<br>' +
                         'Lon: %{lon:.4f}<br>' +
                         f'Temp: {latest["temp"]:.1f}°C<br>' +
                         f'Salinity: {latest["salinity"]:.1f}<br>' +
                         f'pH: {latest["pH"]:.2f}<extra></extra>'
        ))
    
    # Calculate map extent (bounding box)
    if not track_data.empty:
        min_lat = track_data['lat'].min()
        max_lat = track_data['lat'].max()
        min_lon = track_data['lon'].min()
        max_lon = track_data['lon'].max()
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        # Estimate zoom level based on extent (simple heuristic)
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        max_range = max(lat_range, lon_range)
        if max_range < 0.002:
            zoom = 15
        elif max_range < 0.01:
            zoom = 13
        elif max_range < 0.05:
            zoom = 11
        elif max_range < 0.2:
            zoom = 9
        else:
            zoom = 7
    else:
        center_lat, center_lon = 42.3601, -71.0589
        zoom = 12

    fig.update_layout(
        map=dict(
            style="dark",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=800,
        title="Current Position and Track"
    )
    
    return fig



# Streamlit UI

# Sidebar controls
st.sidebar.header("Configuration")

# Add a new sample row at 1Hz (if enabled)
st.sidebar.subheader("Sample Data Generation")
enable_live_sample = st.sidebar.checkbox("Add new sample data at 1Hz (simulated)", value=False)
if enable_live_sample:
    add_sample_row()


# Update frequency
update_frequency = st.sidebar.slider(
    "Update Frequency (seconds)",
    min_value=1,
    max_value=60,
    value=10,
    help="How often to check for new data"
)

# Data selection
st.sidebar.subheader("Data Selection")
available_params = ['temp', 'salinity', 'rhodamine', 'pH']
selected_params = st.sidebar.multiselect(
    "Select parameters to plot",
    available_params,
    default=['rhodamine', 'pH']
)

# Resampling options
st.sidebar.subheader("Data Resampling")
resample_options = {
    'No resampling': None,
    '10 seconds': '10s',
    '1 minute': '1min',
    '5 minutes': '5min',
    '15 minutes': '15min',
    '1 hour': '1H',
    '6 hours': '6H'
}

selected_resample = st.sidebar.selectbox(
    "Resample to:",
    list(resample_options.keys()),
    index=2
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
    # Fetch new data
    cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
    df = get_data_from_db()
    
    # Filter by time range
    if not df.empty:
        df = df[df.index >= cutoff_time]
    
    # Apply resampling if selected
    if resample_options[selected_resample] is not None and not df.empty:
        df = resample_data(df, resample_options[selected_resample])
    
    st.session_state.data_cache = df
    st.session_state.last_update = datetime.now()
    
    # Force rerun to update display
    st.rerun()
elif st.session_state.data_cache.empty:
    # Initial load - fetch data even if auto-refresh is off
    cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
    df = get_data_from_db()
    
    # Filter by time range
    if not df.empty:
        df = df[df.index >= cutoff_time]
    
    # Apply resampling if selected
    if resample_options[selected_resample] is not None and not df.empty:
        df = resample_data(df, resample_options[selected_resample])
    
    st.session_state.data_cache = df
else:
    # Use cached data
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
    # Map
    with map_container:
        st.plotly_chart(create_map_plot(df), use_container_width=True)
    
    # Time series plots
    with plot_container:
        st.plotly_chart(create_timeseries_plot(df, selected_params), use_container_width=True)
    
    # Statistics
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
