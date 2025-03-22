from QuestradeAPI.Chronos import Chronos
from autogluon.timeseries import TimeSeriesDataFrame
import pandas as pd

# Initialize Chronos without API for read-only operations
chronos = Chronos()

print("Getting all market data...")
all_md = chronos.get_all_market_data()
print("Market data column types:")
print(all_md.dtypes)

print("\nCreating TimeSeriesDataFrame...")
try:
    train_data = TimeSeriesDataFrame.from_data_frame(
        all_md,
        id_column="symbol",
        timestamp_column="start"
    )
    print("\nSuccess! TimeSeriesDataFrame created!")
    print("Shape:", train_data.shape)
    print("Sample data:")
    print(train_data.head())
except Exception as e:
    print(f"\nError creating TimeSeriesDataFrame: {e}") 