# Main entry point for the PortfolioLens Streamlit application

import streamlit as st
import pandas as pd
import plotly.express as px
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
from utils.sector_fetcher import (
    build_sector_allocation,
    build_asset_class_allocation,
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

        failed = [t for t in tickers if prices.get(t) is None]
        if failed:
            st.error(
                f"Could not fetch prices for: {', '.join(failed)}. "
                f"Please check the ticker symbol and try again."
            )
            st.stop()

        summary_df = build_portfolio_summary(holdings, prices)

        total_usd = sum(
            parse_value(v)
            for v in summary_df["Value ($)"]
            if v != "N/A"
        )

        rate = None
        symbol = get_currency_symbol(selected_currency)
        if selected_currency != "USD":
            with st.spinner(f"Fetching {selected_currency} exchange rate..."):
                rate = get_exchange_rate(selected_currency)

        # -- Tabs ------------------------------------------------------------
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Portfolio Summary",
            "🏭 Sectors",
            "🏦 Asset Classes",
            "🔬 Stock Breakdown",
            "🔁 Overlap",
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

            table_height = len(display_df) * 35 + 38
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=table_height)

        # -- Tab 2: Sectors --------------------------------------------------
        with tab2:
            with st.spinner("Fetching sector data..."):
                sector_df = build_sector_allocation(summary_df)

            st.markdown('<div class="card-title">🏭 Equity Sector Allocation</div>', unsafe_allow_html=True)

            if sector_df.empty:
                st.info("No sector data available for equity holdings in your portfolio.")
            else:
                # Pie chart - percent labels inside, bold black font, legend on right
                fig_pie = px.pie(
                    sector_df,
                    names="Sector",
                    values="Allocation (%)",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    height=600,
                    showlegend=True,
                    margin=dict(t=20, b=20, l=20, r=200),
                    legend=dict(
                        font=dict(color="#ffffff", size=12),
                        bgcolor="rgba(0,0,0,0)",
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02,
                    ),
                )
                fig_pie.update_traces(
                    textinfo="percent",
                    textposition="inside",
                    insidetextorientation="horizontal",
                    hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
                    textfont=dict(size=12, color="black", family="Arial Black"),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

                # Horizontal bar chart
                fig_bar = px.bar(
                    sector_df,
                    x="Allocation (%)",
                    y="Sector",
                    orientation="h",
                    text=sector_df["Allocation (%)"].apply(lambda x: f"{x:.1f}%"),
                    color="Sector",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    showlegend=False,
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=80),
                    xaxis=dict(gridcolor="#1e3a5f", ticksuffix="%"),
                    yaxis=dict(gridcolor="#1e3a5f", categoryorder="total ascending"),
                )
                fig_bar.update_traces(
                    textposition="outside",
                    textfont=dict(color="#94a3b8"),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # Sector table
                sector_display = sector_df.copy()
                sector_display["Allocation ($)"] = sector_display["Allocation ($)"].apply(lambda x: f"${x:,.2f}")
                sector_display["Allocation (%)"] = sector_display["Allocation (%)"].apply(lambda x: f"{x:.1f}%")
                table_height = len(sector_display) * 35 + 38
                st.dataframe(sector_display, use_container_width=True, hide_index=True, height=table_height)

        # -- Tab 3: Asset Classes --------------------------------------------
        with tab3:
            with st.spinner("Fetching asset class data..."):
                asset_df = build_asset_class_allocation(summary_df)

            st.markdown('<div class="card-title">🏦 Asset Class Breakdown</div>', unsafe_allow_html=True)

            if asset_df.empty:
                st.info("No asset class data available.")
            else:
                # Pie chart - percent labels inside, bold black font, legend on right
                fig_asset_pie = px.pie(
                    asset_df,
                    names="Asset Class",
                    values="Allocation (%)",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig_asset_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    height=600,
                    showlegend=True,
                    margin=dict(t=20, b=20, l=20, r=200),
                    legend=dict(
                        font=dict(color="#ffffff", size=12),
                        bgcolor="rgba(0,0,0,0)",
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02,
                    ),
                )
                fig_asset_pie.update_traces(
                    textinfo="percent",
                    textposition="inside",
                    insidetextorientation="horizontal",
                    hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
                    textfont=dict(size=12, color="black", family="Arial Black"),
                )
                st.plotly_chart(fig_asset_pie, use_container_width=True)

                # Horizontal bar chart
                fig_asset_bar = px.bar(
                    asset_df,
                    x="Allocation (%)",
                    y="Asset Class",
                    orientation="h",
                    text=asset_df["Allocation (%)"].apply(lambda x: f"{x:.1f}%"),
                    color="Asset Class",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig_asset_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    showlegend=False,
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=80),
                    xaxis=dict(gridcolor="#1e3a5f", ticksuffix="%"),
                    yaxis=dict(gridcolor="#1e3a5f", categoryorder="total ascending"),
                )
                fig_asset_bar.update_traces(
                    textposition="outside",
                    textfont=dict(color="#94a3b8"),
                )
                st.plotly_chart(fig_asset_bar, use_container_width=True)

                # Asset class table
                asset_display = asset_df.copy()
                asset_display["Allocation ($)"] = asset_display["Allocation ($)"].apply(lambda x: f"${x:,.2f}")
                asset_display["Allocation (%)"] = asset_display["Allocation (%)"].apply(lambda x: f"{x:.1f}%")
                table_height = len(asset_display) * 35 + 38
                st.dataframe(asset_display, use_container_width=True, hide_index=True, height=table_height)

        # -- Tab 4: Stock Breakdown ------------------------------------------
        with tab4:
            with st.spinner("Fetching holdings data..."):
                equity_df = build_equity_holdings(summary_df)

            st.markdown('<div class="card-title">📈 Equity Holdings</div>', unsafe_allow_html=True)

            if equity_df.empty:
                st.info("No equity holdings found in your portfolio.")
            else:
                equity_df = equity_df.sort_values(
                    "Exposure ($)", ascending=False
                ).reset_index(drop=True)

                equity_df["% of Portfolio"] = equity_df["Exposure ($)"].apply(
                    lambda x: f"{(x / total_usd) * 100:.2f}%"
                )

                coverage_pct = (equity_df["Exposure ($)"].sum() / total_usd) * 100
                remaining_pct = 100 - coverage_pct

                st.markdown(
                    f'<div style="color:#94a3b8; font-size:0.9rem; margin-bottom:0.75rem;">'
                    f'ℹ️ This analysis is based on the top 10 holdings of each ETF, which together represent '
                    f'<strong style="color:#60a5fa;">{coverage_pct:.1f}%</strong> '
                    f'of your total portfolio. The remaining '
                    f'<strong style="color:#60a5fa;">{remaining_pct:.1f}%</strong> '
                    f'is not shown.</div>',
                    unsafe_allow_html=True,
                )

                equity_display = equity_df.copy()
                equity_display["Exposure ($)"] = equity_display["Exposure ($)"].apply(
                    lambda x: f"${x:,.2f}"
                )

                table_height = len(equity_display) * 35 + 38
                st.dataframe(equity_display, use_container_width=True, hide_index=True, height=table_height)

        # -- Tab 5: Overlap --------------------------------------------------
        with tab5:
            st.markdown('<div class="coming-soon">🚧 Overlap detection coming in Step 5.</div>', unsafe_allow_html=True)

# -- Legal disclaimer --------------------------------------------------------
st.markdown("""
<div class="disclaimer">
    PortfolioLens is for informational purposes only and does not constitute financial advice.
    Data is provided as-is. Always consult a qualified financial advisor before making investment decisions.
</div>
""", unsafe_allow_html=True)