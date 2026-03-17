# Fetches and aggregates sector and asset class data across all ETFs using yfinance

import yfinance as yf
import pandas as pd

# Maps yfinance sector keys to clean display names
SECTOR_LABELS = {
    "realestate": "Real Estate",
    "consumer_cyclical": "Consumer Cyclical",
    "basic_materials": "Basic Materials",
    "consumer_defensive": "Consumer Defensive",
    "technology": "Technology",
    "communication_services": "Communication Services",
    "financial_services": "Financial Services",
    "utilities": "Utilities",
    "industrials": "Industrials",
    "energy": "Energy",
    "healthcare": "Healthcare",
}

# Maps yfinance asset class keys to clean display names
ASSET_CLASS_LABELS = {
    "stockPosition": "Stocks",
    "bondPosition": "Bonds",
    "cashPosition": "Cash",
    "preferredPosition": "Preferred",
    "convertiblePosition": "Convertible",
    "otherPosition": "Other",
}


# Detects the real asset type for ETFs that yfinance has no fund data for
# Uses quoteType, category, and longName from yfinance info
def detect_asset_type(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        quote_type = info.get("quoteType", "").upper()
        category = info.get("category", "") or ""
        long_name = info.get("longName", "") or ""

        # Detects cryptocurrency
        if quote_type == "CRYPTOCURRENCY":
            return "Crypto"
        if "digital asset" in category.lower() or "crypto" in category.lower():
            return "Crypto"
        if "bitcoin" in long_name.lower() or "ethereum" in long_name.lower() or "crypto" in long_name.lower():
            return "Crypto"

        # Detects precious metals
        if any(word in long_name.lower() for word in ["gold", "silver", "platinum", "palladium"]):
            return "Precious Metals"
        if "commodit" in category.lower():
            return "Commodities"

        # Detects bonds
        if "bond" in category.lower() or "fixed income" in category.lower():
            return "Bonds"
        if "bond" in long_name.lower() or "treasury" in long_name.lower():
            return "Bonds"

        # Detects real estate
        if "real estate" in category.lower() or "reit" in category.lower():
            return "Real Estate"

        return "Other"

    except Exception:
        return "Other"


# Fetches sector weightings for a single ETF ticker
# Returns a dict like {'Technology': 0.33, 'Healthcare': 0.10, ...}
def get_sector_weightings(ticker: str) -> dict:
    try:
        etf = yf.Ticker(ticker)
        raw = etf.funds_data.sector_weightings
        if not raw:
            return {}
        return {
            SECTOR_LABELS.get(k, k): v
            for k, v in raw.items()
            if v > 0.001
        }
    except Exception:
        return {}


# Fetches asset class breakdown for a single ETF ticker
# Uses smart detection for ETFs with no fund data or generic "Other" classification
def get_asset_classes(ticker: str) -> dict:
    try:
        etf = yf.Ticker(ticker)
        raw = etf.funds_data.asset_classes
        if not raw:
            asset_type = detect_asset_type(ticker)
            return {asset_type: 1.0}
        if hasattr(raw, "iloc"):
            raw = raw.iloc[0].to_dict()
        result = {
            ASSET_CLASS_LABELS.get(k, k): v
            for k, v in raw.items()
            if v > 0.001
        }
        if not result:
            asset_type = detect_asset_type(ticker)
            return {asset_type: 1.0}

        # If the only meaningful allocation is "Other", run smart detection
        # to replace it with a more meaningful label like Crypto, Precious Metals etc.
        if list(result.keys()) == ["Other"] or (
            "Other" in result and result.get("Stocks", 0) == 0
        ):
            asset_type = detect_asset_type(ticker)
            # Replaces Other with the detected asset type
            result = {
                k if k != "Other" else asset_type: v
                for k, v in result.items()
            }

        return result

    except Exception:
        asset_type = detect_asset_type(ticker)
        return {asset_type: 1.0}


# Builds aggregated sector allocation across all ETFs
# Returns a DataFrame with columns: Sector, Allocation ($), Allocation (%)
def build_sector_allocation(summary_df: pd.DataFrame) -> pd.DataFrame:
    from utils.holdings_fetcher import parse_value

    sector_totals = {}

    for _, row in summary_df.iterrows():
        ticker = row["Ticker"]
        etf_value = parse_value(row["Value ($)"])

        if etf_value == 0:
            continue

        asset_classes = get_asset_classes(ticker)
        stock_allocation = asset_classes.get("Stocks", 0)

        if stock_allocation == 0:
            continue

        sectors = get_sector_weightings(ticker)
        if not sectors:
            continue

        # Calculates each sector's dollar contribution
        # Formula: ETF value x stock allocation x sector weight
        equity_value = etf_value * stock_allocation
        for sector, weight in sectors.items():
            contribution = equity_value * weight
            sector_totals[sector] = sector_totals.get(sector, 0) + contribution

    if not sector_totals:
        return pd.DataFrame()

    total = sum(sector_totals.values())
    rows = [
        {
            "Sector": sector,
            "Allocation ($)": value,
            "Allocation (%)": (value / total) * 100,
        }
        for sector, value in sorted(sector_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return pd.DataFrame(rows)


# Builds aggregated asset class breakdown across all ETFs
# Returns a DataFrame with columns: Asset Class, Allocation ($), Allocation (%)
def build_asset_class_allocation(summary_df: pd.DataFrame) -> pd.DataFrame:
    from utils.holdings_fetcher import parse_value

    asset_totals = {}
    total_portfolio_value = sum(
        parse_value(row["Value ($)"])
        for _, row in summary_df.iterrows()
        if row["Value ($)"] != "N/A"
    )

    for _, row in summary_df.iterrows():
        ticker = row["Ticker"]
        etf_value = parse_value(row["Value ($)"])

        if etf_value == 0:
            continue

        asset_classes = get_asset_classes(ticker)
        for asset_class, weight in asset_classes.items():
            contribution = etf_value * weight
            asset_totals[asset_class] = asset_totals.get(asset_class, 0) + contribution

    if not asset_totals:
        return pd.DataFrame()

    rows = [
        {
            "Asset Class": asset_class,
            "Allocation ($)": value,
            "Allocation (%)": (value / total_portfolio_value) * 100,
        }
        for asset_class, value in sorted(asset_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return pd.DataFrame(rows)