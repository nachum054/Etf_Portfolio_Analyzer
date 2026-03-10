import pandas as pd
import yfinance as yf

# Fetches current market prices for a list of tickers using Yahoo Finance
def get_prices(tickers: list) -> dict:
    prices = {}

    for ticker in tickers:
        try:
            # Fetches ticker data from Yahoo Finance
            data = yf.Ticker(ticker)
            info = data.fast_info

            # Retrieves the last traded price
            price = info.last_price

            if price and price > 0:
                prices[ticker.upper()] = round(price, 2)
            else:
                prices[ticker.upper()] = None

        except Exception as e:
            # Stores None if the ticker is invalid or unavailable
            prices[ticker.upper()] = None

    return prices


# Builds a summary DataFrame with price, value, and weight for each holding
def build_portfolio_summary(portfolio_rows: list, prices: dict) -> pd.DataFrame:
    rows = []
    raw_values = []

    for row in portfolio_rows:
        ticker = row["ticker"].upper().strip()
        quantity = row["quantity"]

        # Skips empty or invalid rows
        if not ticker or quantity <= 0:
            continue

        price = prices.get(ticker)

        # Calculates the total value for this holding
        if price:
            value = round(price * quantity, 2)
        else:
            value = None

        # Stores raw numeric value for weight calculation
        raw_values.append(value)

        rows.append({
            "Ticker": ticker,
            "Quantity": quantity,
            "Price ($)": f"${price:,.2f}" if price else "N/A",
            "Value ($)": f"${value:,.2f}" if value else "N/A",
            "_raw_value": value
        })

    # Converts the rows list into a DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Calculates each holding's weight as a percentage of total portfolio value
    total_value = sum(v for v in raw_values if v is not None)
    df["Weight (%)"] = df["_raw_value"].apply(
        lambda x: f"{round((x / total_value) * 100, 2)}%" if x else "N/A"
    )

    # Removes the helper column used for calculations
    df = df.drop(columns=["_raw_value"])

    return df