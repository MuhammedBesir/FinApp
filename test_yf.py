import yfinance as yf
print("Testing yfinance...")
try:
    df = yf.download("THYAO.IS", period="1mo", progress=False)
    print("Download successful")
    print(df.head())
except Exception as e:
    print(f"Error: {e}")
