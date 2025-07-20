import sqlite3
import pandas as pd
import streamlit as st

def get_data_relation(db_path, db_table, time_cutoff=None):
    base_query = f"SELECT * FROM {db_table}"
    params = []
    if time_cutoff:
        # Ensure time_cutoff is an integer timestamp
        if isinstance(time_cutoff, pd.Timestamp) or hasattr(time_cutoff, 'timestamp'):
            time_cutoff = int(time_cutoff.timestamp())
        base_query += " WHERE datetime_utc >= ?"
        params.append(time_cutoff)
    base_query += " ORDER BY datetime_utc"
    return base_query, params

@st.cache_data(ttl=3600, show_spinner=True)
def get_data_for_plotting(db_path, db_table, time_cutoff=None, resample_freq=None):
    conn = sqlite3.connect(db_path)
    query, params = get_data_relation(db_path, db_table, time_cutoff)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty:
        df['datetime_utc'] = pd.to_datetime(df['datetime_utc'], unit='s')
        df.set_index('datetime_utc', inplace=True)
        if resample_freq:
            columns_to_aggregate = [col for col in df.columns if col != 'datetime_utc']
            df = df.resample(resample_freq).mean()[columns_to_aggregate].dropna()
    return df

def get_total_records(db_path, db_table):
    """Fetch the total number of records in the data source."""
    conn = sqlite3.connect(db_path)
    query = f"SELECT COUNT(*) FROM {db_table}"
    cursor = conn.cursor()
    cursor.execute(query)
    total_records = cursor.fetchone()[0]
    conn.close()
    return total_records

def update_with_new_data(db_path, db_table, current_df):
    """Check for new data in the database since the last timestamp in current_df and append it."""
    if current_df.empty:
        return get_data_for_plotting(db_path, db_table)
    last_timestamp = current_df.index.max()
    # Convert last_timestamp to integer seconds
    if isinstance(last_timestamp, pd.Timestamp) or hasattr(last_timestamp, 'timestamp'):
        last_timestamp = int(last_timestamp.timestamp())
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {db_table} WHERE datetime_utc > ? ORDER BY datetime_utc"
    new_data = pd.read_sql_query(query, conn, params=[last_timestamp])
    conn.close()
    if not new_data.empty:
        new_data['datetime_utc'] = pd.to_datetime(new_data['datetime_utc'], unit='s')
        new_data.set_index('datetime_utc', inplace=True)
        updated_df = pd.concat([current_df, new_data])
        updated_df = updated_df[~updated_df.index.duplicated(keep='last')]
        return updated_df
    return current_df
