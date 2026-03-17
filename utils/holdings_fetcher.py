# Fetches and processes ETF holdings data using yfinance

import yfinance as yf
import pandas as pd


# Maps yfinance asset class key names to clean display names
ASSET_CLASS_LABELS = {
    "stockPosition": "Stock",
    "bondPosition": "Bond",
    "cashPosition": "Cash",
    "preferredPosition": "Preferred",
    "convertiblePosition": "Convertible",
    "otherPosition": "Other",
}


# Parses a formatted value string like "$18,537.75" into a float
def parse_value(value_str: str) -> float:
    try:
        return float(str(value_str).replace("$", "").replace(",", ""))
    except Exception:
        return 0.0


# Fetches asset class breakdown for a single ETF ticker
# Returns a dict with clean labels e.g. {'Stock': 0.996, 'Cash': 0.002}
def get_asset_classes(ticker: str) -> dict:
    try:
        etf = yf.Ticker(ticker)
        raw = etf.funds_data.asset_classes

        if raw is None:
            return {}

        # Handles both dict and DataFrame formats
        if hasattr(raw, 'iloc'):
            raw = raw.iloc[0].to_dict()

        # Renames keys to clean display labels and filters near-zero values
        return {
            ASSET_CLASS_LABELS.get(k, k): v
            for k, v in raw.items()
            if v > 0.001
        }
    except Exception:
        return {}


# Fetches top holdings for a single ETF ticker
# Returns a DataFrame with columns: Symbol, Name, Holding Percent
def get_top_holdings(ticker: str) -> pd.DataFrame:
    try:
        etf = yf.Ticker(ticker)
        holdings = etf.funds_data.top_holdings
        if holdings is None or holdings.empty:
            return pd.DataFrame()
        holdings = holdings.reset_index()
        holdings.columns = ["Symbol", "Name", "Holding Percent"]
        return holdings
    except Exception:
        return pd.DataFrame()


# Builds the aggregated equity holdings table across all ETFs
# Merges duplicate stocks and calculates correct exposure per stock
def build_equity_holdings(summary_df: pd.DataFrame) -> pd.DataFrame:
    all_holdings = []

    for _, row in summary_df.iterrows():
        ticker = row["Ticker"]
        raw_value = parse_value(row["Value ($)"])

        if raw_value == 0:
            continue

        # Fetches asset class breakdown
        asset_classes = get_asset_classes(ticker)
        stock_allocation = asset_classes.get("Stock", 0)

        # Skips ETFs with no stock exposure
        if stock_allocation == 0:
            continue

        # Fetches top holdings for this ETF
        holdings_df = get_top_holdings(ticker)
        if holdings_df.empty:
            continue

        # Calculates each stock's dollar exposure
        # Formula: ETF value x stock allocation % x holding weight
        for _, h in holdings_df.iterrows():
            exposure = raw_value * stock_allocation * h["Holding Percent"]
            all_holdings.append({
                "Symbol": h["Symbol"],
                "Name": h["Name"],
                "Exposure ($)": exposure,
            })

    if not all_holdings:
        return pd.DataFrame()

    # Merges duplicate stocks that appear in multiple ETFs
    df = pd.DataFrame(all_holdings)
    aggregated = (
        df.groupby(["Symbol", "Name"])
        .agg({"Exposure ($)": "sum"})
        .reset_index()
    )

    return aggregated


# Builds the non-equity section showing bond/gold/crypto/other exposure
# Handles ETFs with no fund data gracefully
def build_non_equity_holdings(summary_df: pd.DataFrame) -> pd.DataFrame:
    non_equity_rows = []

    for _, row in summary_df.iterrows():
        ticker = row["Ticker"]
        raw_value = parse_value(row["Value ($)"])

        if raw_value == 0:
            continue

        asset_classes = get_asset_classes(ticker)

        # If yfinance returns no fund data at all, treats entire value as Other
        if not asset_classes:
            non_equity = {"Other": 1.0}
        else:
            # Filters out Stock and near-zero allocations
            non_equity = {
                k: v for k, v in asset_classes.items()
                if k != "Stock" and v > 0.001
            }

        if not non_equity:
            continue

        non_equity_row = {
            "Ticker": ticker,
            "_raw_value": raw_value,
        }
        for asset_class, allocation in non_equity.items():
            non_equity_row[asset_class] = f"{allocation * 100:.1f}%"
            non_equity_row[f"_{asset_class}_exposure"] = raw_value * allocation

        non_equity_rows.append(non_equity_row)

    if not non_equity_rows:
        return pd.DataFrame()

    return pd.DataFrame(non_equity_rows).fillna("-")