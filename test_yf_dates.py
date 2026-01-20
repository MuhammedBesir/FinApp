import yfinance as yf
from datetime import datetime, timedelta

print("Testing yfinance with dates...")
end_date = datetime.now()
start_date = end_date - timedelta(days=200)

print(f"Start: {start_date}, End: {end_date}")

try:
    df = yf.download("THYAO.IS", start=start_date, end=end_date, progress=False)
    print("Download successful")
    print(df.head())
except Exception as e:
    print(f"Error: {e}")
