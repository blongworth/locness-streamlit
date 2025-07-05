import os
import toml

# Default config values
DEFAULTS = {
    "update_frequency": 10,
    "resample": "1min",
    "file_path": "oceanographic_data.duckdb"
}

CONFIG_FILE = "config.toml"

# Read config from TOML file if it exists
if os.path.exists(CONFIG_FILE):
    config = toml.load(CONFIG_FILE)
else:
    config = {}

def get_config_value(key):
    # 1. Try environment variable (upper case, e.g. UPDATE_FREQUENCY)
    env_key = key.upper()
    if env_key in os.environ:
        val = os.environ[env_key]
        # Convert to int if needed
        if key == "update_frequency":
            try:
                return int(val)
            except Exception:
                pass
        return val
    # 2. Try config file
    if key in config:
        return config[key]
    # 3. Fallback to default
    return DEFAULTS[key]

# Convenience accessors
update_frequency = get_config_value("update_frequency")
resample = get_config_value("resample")
file_path = get_config_value("file_path")
