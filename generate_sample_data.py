import argparse
from sample_data import create_sample_database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample oceanographic data in a DuckDB database.")
    parser.add_argument('--db', type=str, default='oceanographic_data.duckdb', help='Path to DuckDB database file (default: oceanographic_data.db)')
    parser.add_argument('--freq', type=float, default=1.0, help='Sample frequency in Hz (default: 1.0)')
    parser.add_argument('--num', type=int, default=1000, help='Number of samples to generate (default: 1000)')
    args = parser.parse_args()

    print(f"Generating {args.num} samples at {args.freq} Hz in {args.db} ...")
    create_sample_database(db_path=args.db, sample_frequency_hz=args.freq, num_samples=args.num)
    print("Done.")
