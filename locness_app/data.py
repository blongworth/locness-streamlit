import sqlite3
import pandas as pd
import streamlit as st

def get_data_relation(db_path, time_cutoff=None):
    base_query = "SELECT * FROM sensor_data"
    params = []
    if time_cutoff:
        base_query += " WHERE timestamp >= ?"
        params.append(time_cutoff)
    base_query += " ORDER BY timestamp"
    return base_query, params

#@st.cache_data(ttl=3600, show_spinner=True)
def get_data_for_plotting(db_path, time_cutoff=None, resample_freq=None):
    conn = sqlite3.connect(db_path)
    query, params = get_data_relation(db_path, time_cutoff)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        if resample_freq:
            columns_to_aggregate = ['lat', 'lon', 'temp', 'salinity', 'rhodamine', 'ph', 'ph_ma']
            df = df.resample(resample_freq).mean()[columns_to_aggregate].dropna()
    return df

def get_total_records(db_path):
    """Fetch the total number of records in the data source."""
    conn = sqlite3.connect(db_path)
    query = "SELECT COUNT(*) FROM sensor_data"
    cursor = conn.cursor()
    cursor.execute(query)
    total_records = cursor.fetchone()[0]
    conn.close()
    return total_records
