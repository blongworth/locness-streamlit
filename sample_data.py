import sqlite3
from datetime import datetime, timedelta
import numpy as np

def create_sample_database(db_path='oceanographic_data.db', sample_frequency_hz=1, num_samples=1000):
    """Create a sample SQLite database with oceanographic data

    Args:
        db_path (str): Path to the SQLite database file.
        sample_frequency_hz (float): Frequency of samples per second.
        num_samples (int): Number of samples to generate.
    """
    conn = sqlite3.connect(db_path)
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
        # Calculate time delta between samples
        if sample_frequency_hz > 0:
            delta_seconds = 1.0 / sample_frequency_hz
        else:
            delta_seconds = 1.0
        base_time = datetime.now() - timedelta(seconds=delta_seconds * num_samples)
        base_lat, base_lon = 42.3601, -71.0589  # Boston area
        sample_data = []
        for i in range(num_samples):
            timestamp = base_time + timedelta(seconds=i * delta_seconds)
            lat = base_lat + np.sin(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
            lon = base_lon + np.cos(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
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

def add_sample_row(db_path='oceanographic_data.db'):
    """Add a single new row of sample data at the current time (simulate 1Hz)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Get last row for continuity
    cursor.execute('SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1')
    last = cursor.fetchone()
    if last:
        _, last_time, last_lat, last_lon, _, _, _, _ = last
        last_time = datetime.fromisoformat(last_time)
        i = int((datetime.now() - last_time).total_seconds())
        base_lat, base_lon = last_lat, last_lon
    else:
        i = 0
        base_lat, base_lon = 42.3601, -71.0589
        last_time = datetime.now()
    timestamp = datetime.now()
    lat = base_lat + np.sin(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
    lon = base_lon + np.cos(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
    temp = 15 + 5 * np.sin(i * 0.02) + np.random.normal(0, 0.5)
    salinity = 35 + 2 * np.sin(i * 0.015) + np.random.normal(0, 0.2)
    rhodamine = max(0, 10 + 5 * np.sin(i * 0.03) + np.random.normal(0, 1))
    ph = 8.1 + 0.3 * np.sin(i * 0.025) + np.random.normal(0, 0.05)
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, lat, lon, temp, salinity, rhodamine, pH)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, lat, lon, temp, salinity, rhodamine, ph))
    conn.commit()
    conn.close()
