import streamlit as st
import sqlite3
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

def create_sample_database():
    """Create a sample SQLite database with oceanographic data"""
    conn = sqlite3.connect('oceanographic_data.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        lat REAL,
        lon REAL,
        temp REAL,
        salinity REAL,
        rhodamine REAL,
        pH REAL
    )
    ''')
    
    # Generate sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM sensor_data')
    if cursor.fetchone()[0] == 0:
        # Generate 1000 sample records over the last 24 hours
        base_time = datetime.now() - timedelta(hours=24)
        
        # Simulate a moving platform (e.g., research vessel)
        base_lat, base_lon = 42.3601, -71.0589  # Boston area
        
        sample_data = []
        for i in range(1000):
            timestamp = base_time + timedelta(minutes=i * 1.44)  # ~1000 points over 24 hours
            
            # Simulate movement
            lat = base_lat + np.sin(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
            lon = base_lon + np.cos(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
            
            # Simulate realistic oceanographic data
            temp = 15 + 5 * np.sin(i * 0.02) + np.random.normal(0, 0.5)
            salinity = 35 + 2 * np.sin(i * 0.015) + np.random.normal(0, 0.2)
            rhodamine = max(0, 10 + 5 * np.sin(i * 0.03) + np.random.normal(0, 1))
            ph = 8.1 + 0.3 * np.sin(i * 0.025) + np.random.normal(0, 0.05)
            
            sample_data.append((timestamp, lat, lon, temp, salinity, rhodamine, ph))
        
        cursor.executemany('''
        INSERT INTO sensor_data (timestamp, lat, lon, temp, salinity, rhodamine, pH)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        
        conn.commit()
    
    conn.close()

def get_data_from_db(since_timestamp=None):
    """Fetch data from SQLite database"""
    conn = sqlite3.connect('oceanographic_data.db')
    
    if since_timestamp:
        query = '''
        SELECT * FROM sensor_data 
        WHERE timestamp > ? 
        ORDER BY timestamp
        '''
        df = pd.read_sql_query(query, conn, params=(since_timestamp,))
    else:
        query = 'SELECT * FROM sensor_data ORDER BY timestamp'
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    
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
    """Create timeseries plot for selected parameters"""
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
        height=200 * len(selected_params),
        title="Time Series Data",
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time", row=len(selected_params), col=1)
    
    return fig

def create_map_plot(df):
    """Create map showing latest positions"""
    if df.empty:
        return go.Figure()
    
    # Get the latest 100 points for the track
    recent_data = df.tail(100)
    
    fig = go.Figure()
    
    # Add track line
    fig.add_trace(go.Scattermapbox(
        lat=recent_data['lat'],
        lon=recent_data['lon'],
        mode='lines',
        line=dict(width=2, color='blue'),
        name='Track',
        hoverinfo='skip'
    ))
    
    # Add latest position
    if not df.empty:
        latest = df.iloc[-1]
        fig.add_trace(go.Scattermapbox(
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
    
    # Calculate center point
    if not recent_data.empty:
        center_lat = recent_data['lat'].mean()
        center_lon = recent_data['lon'].mean()
    else:
        center_lat, center_lon = 42.3601, -71.0589
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=12
        ),
        height=400,
        title="Current Position and Track"
    )
    
    return fig

# Initialize database
create_sample_database()

# Streamlit UI
st.title("🌊 Oceanographic Data Visualizer")
st.markdown("Real-time visualization of oceanographic sensor data")

# Sidebar controls
st.sidebar.header("Configuration")

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
    default=['temp', 'salinity']
)

# Resampling options
st.sidebar.subheader("Data Resampling")
resample_options = {
    'No resampling': None,
    '1 minute': '1T',
    '5 minutes': '5T',
    '15 minutes': '15T',
    '1 hour': '1H',
    '6 hours': '6H',
    '1 day': '1D'
}

selected_resample = st.sidebar.selectbox(
    "Resample to:",
    list(resample_options.keys()),
    index=0
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

# Main content area
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Data Status")
    status_container = st.empty()

with col1:
    st.subheader("Controls")
    
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
        st.write(f"**Last update:** {st.session_state.last_update.strftime('%H:%M:%S')}")
        st.write(f"**Latest data:** {df.index[-1].strftime('%H:%M:%S')}")
        st.write(f"**Next update in:** {max(0, update_frequency - int((datetime.now() - st.session_state.last_update).total_seconds()))} seconds")
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
