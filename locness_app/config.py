import os
import toml

DEFAULTS = {
    "update_frequency": 10,
    "resample": "1min",
    "file_path": "oceanographic_data.duckdb"
}

CONFIG_FILE = "config.toml"

if os.path.exists(CONFIG_FILE):
    config = toml.load(CONFIG_FILE)
else:
    config = {}

def get_config_value(key):
    env_key = key.upper()
    if env_key in os.environ:
        val = os.environ[env_key]
        if key == "update_frequency":
            try:
                return int(val)
            except Exception:
                pass
        return val
    if key in config:
        return config[key]
    return DEFAULTS[key]

update_frequency = get_config_value("update_frequency")
resample = get_config_value("resample")
file_path = get_config_value("file_path")
db_table = get_config_value("db_table")
