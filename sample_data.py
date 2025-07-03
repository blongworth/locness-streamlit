import duckdb
import numpy as np
from datetime import datetime, timedelta

def create_sample_database(db_path='oceanographic_data.duckdb', sample_frequency_hz=1, num_samples=1000):
    con = duckdb.connect(db_path)
    con.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            timestamp TIMESTAMP,
            lat DOUBLE,
            lon DOUBLE,
            temp DOUBLE,
            salinity DOUBLE,
            rhodamine DOUBLE,
            pH DOUBLE
        )
    ''')
    # Check if table is empty
    count = con.execute('SELECT COUNT(*) FROM sensor_data').fetchone()[0]
    if count == 0:
        delta_seconds = 1.0 / sample_frequency_hz if sample_frequency_hz > 0 else 1.0
        base_time = datetime.now() - timedelta(seconds=delta_seconds * num_samples)
        base_lat, base_lon = 42.3601, -71.0589  # Boston area
        sample_data = []
        for i in range(num_samples):
            timestamp = base_time + timedelta(seconds=i * delta_seconds)
            lat = base_lat + np.sin(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
            lon = base_lon + np.cos(i * 0.01) * 0.1 + np.random.normal(0, 0.01)
            temp = 15 + 5 * np.sin(i * 0.02) + np.random.normal(0, 0.5)
            salinity = 35 + 2 * np.sin(i * 0.015) + np.random.normal(0, 0.2)
            rhodamine = min(500, np.random.exponential(scale=1.25))
            ph = 8.1 + 0.3 * np.sin(i * 0.025) + np.random.normal(0, 0.05)
            sample_data.append((timestamp, lat, lon, temp, salinity, rhodamine, ph))
        con.executemany('''
            INSERT INTO sensor_data (timestamp, lat, lon, temp, salinity, rhodamine, pH)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
    con.close()

def add_sample_row(db_path='oceanographic_data.duckdb'):
    import numpy as np
    from datetime import datetime
    con = duckdb.connect(db_path)
    last = con.execute('SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1').fetchone()
    if last:
        _, last_time, last_lat, last_lon, _, _, _, _ = last
        timestamp = datetime.now()
        lat = last_lat + np.random.normal(0, 0.001)
        lon = last_lon + np.random.normal(0, 0.001)
        temp = 15 + 5 * np.sin(timestamp.timestamp() * 0.02) + np.random.normal(0, 0.5)
        salinity = 35 + 2 * np.sin(timestamp.timestamp() * 0.015) + np.random.normal(0, 0.2)
        rhodamine = min(500, np.random.exponential(scale=1.25))
        ph = 8.1 + 0.3 * np.sin(timestamp.timestamp() * 0.025) + np.random.normal(0, 0.05)
        con.execute('''
            INSERT INTO sensor_data (timestamp, lat, lon, temp, salinity, rhodamine, pH)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [timestamp, lat, lon, temp, salinity, rhodamine, ph])
    con.close()
