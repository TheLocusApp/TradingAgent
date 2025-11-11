import yfinance as yf
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

df = yf.download(
    "TSLA", 
    start=start_date, 
    end=end_date, 
    interval='1h',
    progress=False
)

print("DataFrame shape:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nColumn type:", type(df.columns))
print("\nFirst few rows:")
print(df.head())
print("\nDataFrame info:")
print(df.info())
