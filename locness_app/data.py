import duckdb
import pandas as pd
from datetime import datetime

class DataManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

    def get_data_relation(self, time_cutoff=None, resample_freq=None):
        base_query = "SELECT * FROM sensor_data"
        params = []
        if time_cutoff:
            base_query += " WHERE timestamp >= ?"
            params.append(time_cutoff)
        base_query += " ORDER BY timestamp"
        if resample_freq:
            query = f'''
                SELECT 
                    time_bucket('{resample_freq}', timestamp) AS timestamp,
                    AVG(lat) AS lat,
                    AVG(lon) AS lon,
                    AVG(temp) AS temp,
                    AVG(salinity) AS salinity,
                    AVG(rhodamine) AS rhodamine,
                    AVG(pH) AS pH
                FROM ({base_query})
                GROUP BY 1
                ORDER BY 1
            '''
            return query, params
        else:
            return base_query, params

    def get_data_for_plotting(self, time_cutoff=None, resample_freq=None):
        query, params = self.get_data_relation(time_cutoff, resample_freq)
        df = self.conn.execute(query, params).df()
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        return df

    def close(self):
        self.conn.close()
