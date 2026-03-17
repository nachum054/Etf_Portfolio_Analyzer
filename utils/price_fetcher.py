# Fetches and processes ETF price and portfolio summary data using yfinance

import pandas as pd
import yfinance as yf


# Fetches current market prices for a list of tickers using Yahoo Finance
# Uses multiple fallback strategies to handle rate limiting
def get_prices(tickers: list) -> dict:
    import time
    prices = {}

    # Fetches all tickers at once using yf.download as primary method
    try:
        import yfinance as yf
        if len(tickers) == 1:
            data = yf.download(tickers[0], period="5d", progress=False, auto_adjust=True)
        else:
            data = yf.download(tickers, period="5d", progress=False, auto_adjust=True)

        if not data.empty:
            close = data["Close"]
            if len(tickers) == 1:
                # Single ticker returns a Series
                last_price = float(close.dropna().iloc[-1])
                prices[tickers[0].upper()] = round(last_price, 2)
            else:
                # Multiple tickers returns a DataFrame
                for ticker in tickers:
                    try:
                        col = close[ticker].dropna()
                        if not col.empty:
                            prices[ticker.upper()] = round(float(col.iloc[-1]), 2)
                    except Exception:
                        pass
    except Exception:
        pass

    # Falls back to individual Ticker fetch for any that failed
    for ticker in tickers:
        if ticker.upper() in prices:
            continue

        for attempt in range(3):
            try:
                data = yf.Ticker(ticker)
                try:
                    price = data.fast_info.last_price
                except Exception:
                    price = None

                if not price or price <= 0:
                    hist = data.history(period="5d")
                    if not hist.empty:
                        price = round(float(hist["Close"].iloc[-1]), 2)

                if price and price > 0:
                    prices[ticker.upper()] = round(price, 2)
                    break

            except Exception:
                pass

            time.sleep(1)

        if ticker.upper() not in prices:
            prices[ticker.upper()] = None

    return prices


# Builds a summary DataFrame with price, value, and weight for each holding
def build_portfolio_summary(portfolio_rows: list, prices: dict) -> pd.DataFrame:
    rows = []
    raw_values = []

    for row in portfolio_rows:
        ticker = row["ticker"].upper().strip()
        quantity = row["quantity"]

        if not ticker or quantity <= 0:
            continue

        price = prices.get(ticker)

        if price:
            value = round(price * quantity, 2)
        else:
            value = None

        raw_values.append(value)

        rows.append({
            "Ticker": ticker,
            "Quantity": quantity,
            "Price ($)": f"${price:,.2f}" if price else "N/A",
            "Value ($)": f"${value:,.2f}" if value else "N/A",
            "_raw_value": value,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Calculates each holding's weight as a percentage of total portfolio value
    total_value = sum(v for v in raw_values if v is not None)
    df["Weight (%)"] = df["_raw_value"].apply(
        lambda x: f"{round((x / total_value) * 100, 2)}%" if x else "N/A"
    )

    df = df.drop(columns=["_raw_value"])

    return df