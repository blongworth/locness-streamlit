import duckdb
import sqlite3
import pandas as pd
from datetime import datetime
import os

class DataManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.is_sqlite = db_path.endswith('.sqlite') or db_path.endswith('.db')
        if not self.is_sqlite:
            self.conn = duckdb.connect(db_path)
        else:
            self.conn = None  # Will connect as needed

    def get_data_relation(self, time_cutoff=None, resample_freq=None):
        base_query = "SELECT * FROM sensor_data"
        params = []
        if time_cutoff:
            base_query += " WHERE timestamp >= ?"
            params.append(time_cutoff)
        base_query += " ORDER BY timestamp"
        if resample_freq and not self.is_sqlite:
            query = f'''
                SELECT 
                    time_bucket('{resample_freq}', timestamp) AS timestamp,
                    AVG(lat) AS lat,
                    AVG(lon) AS lon,
                    AVG(temp) AS temp,
                    AVG(salinity) AS salinity,
                    AVG(rhodamine) AS rhodamine,
                    AVG(ph) AS ph
                    AVG(ph_ma) AS ph_ma
                FROM ({base_query})
                GROUP BY 1
                ORDER BY 1
            '''
            return query, params
        else:
            return base_query, params

    def get_data_for_plotting(self, time_cutoff=None, resample_freq=None):
        if self.is_sqlite:
            # SQLite: no time_bucket, so do resampling in pandas
            conn = sqlite3.connect(self.db_path)
            query, params = self.get_data_relation(time_cutoff, None)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                if resample_freq:
                    agg_dict = {
                        'lat': 'mean',
                        'lon': 'mean',
                        'temp': 'mean',
                        'salinity': 'mean',
                        'rhodamine': 'mean',
                        'ph': 'mean',
                        'ph_ma': 'mean'
                    }
                    df = df.resample(resample_freq).agg(agg_dict).dropna()
            return df
        else:
            query, params = self.get_data_relation(time_cutoff, resample_freq)
            df = self.conn.execute(query, params).df()
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            return df

    def close(self):
        if self.conn:
            self.conn.close()
