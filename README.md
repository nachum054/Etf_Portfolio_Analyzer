# PortfolioLens

A Streamlit web app that analyzes your ETF portfolio at two levels:
- **ETF level** - weight and value of each ETF you hold
- **Stock level** - real underlying holdings, overlap detection, and sector breakdown

## Features
- Manual input - add ETF tickers and quantities directly
- Screenshot upload - AI extracts tickers and quantities from your broker screenshot automatically
- Sector allocation charts
- Overlap detection between ETFs
- "What if" simulator - see how adding a new ETF changes your portfolio

## Tech Stack
Python, Streamlit, yfinance, Plotly, Pandas

## Data Sources
- ETF holdings and sector data: Massive API
- Price data: yfinance