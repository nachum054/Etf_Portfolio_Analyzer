# Main entry point for the PortfolioLens Streamlit application

import streamlit as st
import pandas as pd
from utils.price_fetcher import get_prices, build_portfolio_summary
from utils.currency_fetcher import (
    SUPPORTED_CURRENCIES,
    get_exchange_rate,
    get_currency_symbol,
)
from utils.holdings_fetcher import (
    build_equity_holdings,
    parse_value,
)

# -- Page configuration ------------------------------------------------------
st.set_page_config(
    page_title="PortfolioLens",
    page_icon="🔍",
    layout="wide",
)

# -- Custom CSS styling -------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0f2341; }

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 0.25rem;
        text-align: center;
    }

    .sub-title {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        text-align: center;
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #60a5fa;
        margin-bottom: 1rem;
    }

    .disclaimer {
        font-size: 0.75rem;
        color: #94a3b8;
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        border-top: 1px solid #1e3a5f;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 500;
        color: #94a3b8;
        padding: 0.5rem 1.25rem;
    }

    .stTabs [aria-selected="true"] {
        color: #60a5fa !important;
        border-bottom: 2px solid #60a5fa !important;
    }

    .coming-soon {
        color: #64748b;
        font-size: 0.95rem;
        padding: 2rem 0;
    }

    input:focus, select:focus, textarea:focus {
        outline: 2px solid #60a5fa !important;
        outline-offset: 2px !important;
    }

    button:focus {
        outline: 2px solid #60a5fa !important;
        outline-offset: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

# -- App header --------------------------------------------------------------
st.markdown('<div class="main-title">🔍 PortfolioLens</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Analyze your ETF portfolio - see what you really own</div>',
    unsafe_allow_html=True,
)

# -- Manual entry card -------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="card-title">📋 Manual Entry</div>', unsafe_allow_html=True)

    if "rows" not in st.session_state:
        st.session_state.rows = [{"ticker": "", "quantity": 0.0}]

    for i, row in enumerate(st.session_state.rows):
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.session_state.rows[i]["ticker"] = st.text_input(
                "Ticker",
                value=row["ticker"],
                key=f"ticker_{i}",
                placeholder="e.g. SPY",
            ).upper()
        with col2:
            st.session_state.rows[i]["quantity"] = st.number_input(
                "Quantity",
                value=row["quantity"],
                min_value=0.0,
                step=1.0,
                key=f"qty_{i}",
            )
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✕", key=f"remove_{i}", help="Remove this row") and len(st.session_state.rows) > 1:
                st.session_state.rows.pop(i)
                st.rerun()

    st.button(
        "+ Add Row",
        key="add_row",
        on_click=lambda: st.session_state.rows.append({"ticker": "", "quantity": 0.0}),
    )

# -- Currency selector card --------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="card-title">💱 Display Currency</div>', unsafe_allow_html=True)

    currency_options = [f"{code} - {name}" for code, name in SUPPORTED_CURRENCIES.items()]
    selected_option = st.selectbox(
        "Select your preferred currency for portfolio valuation (type to search)",
        options=currency_options,
        index=0,
    )
    selected_currency = selected_option.split(" - ")[0]

# -- Screenshot upload card --------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="card-title">📸 Upload Screenshot</div>', unsafe_allow_html=True)
    st.file_uploader(
        "Upload a screenshot of your portfolio and we'll extract the tickers automatically",
        type=["png", "jpg", "jpeg"],
        key="screenshot",
    )
    st.caption("🚧 AI extraction coming soon")

# -- Keyboard shortcut hint --------------------------------------------------
st.caption("💡 Tip: Tab through all fields, then press Tab + Enter to analyze")

# -- Analyze button ----------------------------------------------------------
analyze_clicked = st.button(
    "🔍 Analyze Portfolio",
    type="primary",
    use_container_width=True,
    help="Press Tab to reach this button, then Enter to run the analysis",
)

# -- Results -----------------------------------------------------------------
if analyze_clicked:
    # Normalizes tickers to uppercase and strips whitespace before any processing
    holdings = [
        {"ticker": r["ticker"].upper().strip(), "quantity": r["quantity"]}
        for r in st.session_state.rows
        if r["ticker"].strip() and r["quantity"] > 0
    ]

    if not holdings:
        st.warning("Please enter at least one ticker and quantity before analyzing.")
    else:
        tickers = [r["ticker"] for r in holdings]

        with st.spinner("Fetching live prices..."):
            prices = get_prices(tickers)

        # Blocks analysis if any ticker price could not be fetched
        failed = [t for t in tickers if prices.get(t) is None]
        if failed:
            st.error(
                f"Could not fetch prices for: {', '.join(failed)}. "
                f"Please check the ticker symbol and try again."
            )
            st.stop()

        # Builds the Level 1 summary DataFrame
        summary_df = build_portfolio_summary(holdings, prices)

        # Calculates total USD value
        total_usd = sum(
            parse_value(v)
            for v in summary_df["Value ($)"]
            if v != "N/A"
        )

        # Fetches exchange rate if a non-USD currency is selected
        rate = None
        symbol = get_currency_symbol(selected_currency)
        if selected_currency != "USD":
            with st.spinner(f"Fetching {selected_currency} exchange rate..."):
                rate = get_exchange_rate(selected_currency)

        # -- Tabs ------------------------------------------------------------
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Portfolio Summary",
            "🔬 Stock Breakdown",
            "🏭 Sectors",
            "🔁 Overlap",
            "🔮 What-If",
        ])

        # -- Tab 1: Portfolio Summary ----------------------------------------
        with tab1:
            if selected_currency != "USD" and rate:
                total_converted = total_usd * rate
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💼 Total Portfolio Value (USD)", f"${total_usd:,.2f}")
                with col2:
                    st.metric(
                        f"💼 Total Portfolio Value ({selected_currency})",
                        f"{symbol}{total_converted:,.2f}",
                    )
            else:
                st.metric("💼 Total Portfolio Value (USD)", f"${total_usd:,.2f}")

            st.markdown("---")

            display_df = summary_df.copy()

            if selected_currency != "USD" and rate:
                raw_values = [
                    parse_value(v) if v != "N/A" else None
                    for v in display_df["Value ($)"]
                ]
                display_df[f"Value ({selected_currency})"] = [
                    f"{symbol}{v * rate:,.2f}" if v is not None else "N/A"
                    for v in raw_values
                ]

            # Calculates table height to show all rows without internal scrolling
            row_height = 35
            header_height = 38
            table_height = len(display_df) * row_height + header_height

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=table_height,
            )

        # -- Tab 2: Stock Breakdown ------------------------------------------
        with tab2:
            with st.spinner("Fetching holdings data..."):
                equity_df = build_equity_holdings(summary_df)

            st.markdown('<div class="card-title">📈 Equity Holdings</div>', unsafe_allow_html=True)

            if equity_df.empty:
                st.info("No equity holdings found in your portfolio.")
            else:
                # Sorts by exposure descending
                equity_df = equity_df.sort_values(
                    "Exposure ($)", ascending=False
                ).reset_index(drop=True)

                # Calculates each stock's % of total portfolio
                equity_df["% of Portfolio"] = equity_df["Exposure ($)"].apply(
                    lambda x: f"{(x / total_usd) * 100:.2f}%"
                )

                # Calculates total coverage of displayed holdings
                coverage_pct = (equity_df["Exposure ($)"].sum() / total_usd) * 100

                # Shows styled note above table
                remaining_pct = 100 - coverage_pct
                st.markdown(
                    f'<div style="color:#94a3b8; font-size:0.9rem; margin-bottom:0.75rem;">'
                    f'ℹ️ This analysis is based on the top 10 holdings of each ETF, which together represent '
                    f'<strong style="color:#60a5fa;">{coverage_pct:.1f}%</strong> '
                    f'of your total portfolio.</div>',
                    unsafe_allow_html=True,
                )

                # Formats exposure column for display
                equity_display = equity_df.copy()
                equity_display["Exposure ($)"] = equity_display["Exposure ($)"].apply(
                    lambda x: f"${x:,.2f}"
                )

                # Calculates table height to show all rows without internal scrolling
                row_height = 35
                header_height = 38
                table_height = len(equity_display) * row_height + header_height

                st.dataframe(
                    equity_display,
                    use_container_width=True,
                    hide_index=True,
                    height=table_height,
                )

        # -- Tab 3: Sectors --------------------------------------------------
        with tab3:
            st.markdown('<div class="coming-soon">🚧 Sector allocation charts coming in Step 4.</div>', unsafe_allow_html=True)

        # -- Tab 4: Overlap --------------------------------------------------
        with tab4:
            st.markdown('<div class="coming-soon">🚧 Overlap detection coming in Step 5.</div>', unsafe_allow_html=True)

        # -- Tab 5: What-If --------------------------------------------------
        with tab5:
            st.markdown('<div class="coming-soon">🚧 What-If simulator coming in Step 6.</div>', unsafe_allow_html=True)

# -- Legal disclaimer --------------------------------------------------------
st.markdown("""
<div class="disclaimer">
    PortfolioLens is for informational purposes only and does not constitute financial advice.
    Data is provided as-is. Always consult a qualified financial advisor before making investment decisions.
</div>
""", unsafe_allow_html=True)