import pandas as pd
import streamlit as st
from utils.price_fetcher import get_prices, build_portfolio_summary

# Configures the Streamlit page settings
st.set_page_config(
    page_title="PortfolioLens",
    page_icon="📈",
    layout="wide"
)

# Injects custom CSS for a navy finance dashboard with proper contrast
st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0f2341;
            color: #e8edf5;
        }

        /* Page padding */
        .block-container {
            padding: 2rem 4rem;
        }

        /* Main title */
        h1 {
            text-align: center;
            color: #ffffff;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        /* Subtitle */
        .subtitle {
            text-align: center;
            color: #94a3b8;
            font-size: 1rem;
            margin-bottom: 1rem;
        }

        /* Card section header */
        .card-title {
            color: #60a5fa;
            font-size: 1rem;
            font-weight: 700;
            padding-bottom: 0.75rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #2a4a6e;
        }

        /* Column headers */
        .col-header {
            color: #e2e8f0;
            font-size: 0.9rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 0.25rem;
        }

        /* Card container styling via Streamlit container */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #162d4a !important;
            border: 1px solid #2a4a6e !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
        }

        /* Text input */
        .stTextInput input {
            background-color: #1e3a5f !important;
            border: 1px solid #2a4a6e !important;
            border-radius: 6px !important;
            color: #ffffff !important;
            font-size: 0.95rem !important;
        }

        /* Placeholder text */
        .stTextInput input::placeholder {
            color: #6b8cae !important;
            opacity: 1 !important;
        }

        .stTextInput input:focus {
            border-color: #60a5fa !important;
            box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
        }

        /* Number input */
        .stNumberInput input {
            background-color: #1e3a5f !important;
            border: 1px solid #2a4a6e !important;
            border-radius: 6px !important;
            color: #ffffff !important;
        }

        /* Number input +/- buttons */
        .stNumberInput button {
            background-color: #1e3a5f !important;
            color: #60a5fa !important;
            border: 1px solid #2a4a6e !important;
        }

        /* Regular buttons */
        .stButton > button {
            background-color: #1e3a5f;
            color: #60a5fa;
            border: 1px solid #2a4a6e;
            border-radius: 6px;
            font-weight: 600;
        }

        .stButton > button:hover {
            background-color: #2563eb;
            color: #ffffff;
            border-color: #2563eb;
        }

        /* Primary analyze button */
        .stButton > button[kind="primary"] {
            background-color: #0ea5e9;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #0284c7;
        }

        /* File uploader - navy styled */
        [data-testid="stFileUploader"] section {
            background-color: #1e3a5f !important;
            border: 2px dashed #60a5fa !important;
            border-radius: 10px !important;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] * {
            color: #94a3b8 !important;
        }

        [data-testid="stFileUploader"] button {
            background-color: #1e3a5f !important;
            color: #60a5fa !important;
            border: 1px solid #2a4a6e !important;
            border-radius: 6px !important;
        }

        /* Divider */
        hr {
            border-color: #2a4a6e;
            margin: 2rem 0;
        }

        /* Disclaimer footer */
        .disclaimer {
            text-align: center;
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #2a4a6e;
        }
    </style>
""", unsafe_allow_html=True)

# Renders the centered title and subtitle
st.markdown("<h1>📈 PortfolioLens</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analyze your real portfolio exposure - ETFs and individual stocks supported.</p>', unsafe_allow_html=True)

st.divider()

# Renders the manual entry card using a Streamlit container
with st.container(border=True):
    st.markdown('<div class="card-title">📋 Manual Entry</div>', unsafe_allow_html=True)

    # Initializes the portfolio rows in session state if not already set
    if "portfolio_rows" not in st.session_state:
        st.session_state.portfolio_rows = [{"ticker": "", "quantity": 0.0}]

    # Renders the column headers
    col1, col2, col3 = st.columns([2, 2, 1])
    col1.markdown('<p class="col-header">Ticker</p>', unsafe_allow_html=True)
    col2.markdown('<p class="col-header">Quantity</p>', unsafe_allow_html=True)
    col3.markdown('<p class="col-header">Remove</p>', unsafe_allow_html=True)

    # Renders a row for each holding in the portfolio
    for i, row in enumerate(st.session_state.portfolio_rows):
        col1, col2, col3 = st.columns([2, 2, 1])
        st.session_state.portfolio_rows[i]["ticker"] = col1.text_input(
            "Ticker", value=row["ticker"], key=f"ticker_{i}",
            label_visibility="collapsed", placeholder="e.g. SPY, AAPL"
        )
        st.session_state.portfolio_rows[i]["quantity"] = col2.number_input(
            "Quantity", value=row["quantity"], min_value=0.0, key=f"qty_{i}",
            label_visibility="collapsed"
        )
        if col3.button("🗑️ Remove", key=f"delete_{i}"):
            st.session_state.portfolio_rows.pop(i)
            st.rerun()

    # Adds a new empty row to the portfolio
    if st.button("➕ Add Row"):
        st.session_state.portfolio_rows.append({"ticker": "", "quantity": 0.0})
        st.rerun()

    # Adds spacing below the Add Row button
    st.markdown("<br>", unsafe_allow_html=True)

# Renders the screenshot upload card using a Streamlit container
with st.container(border=True):
    st.markdown('<div class="card-title">📸 Upload a Screenshot</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#94a3b8; margin-bottom:0.75rem;">Upload a screenshot of your broker portfolio - AI will extract the tickers and quantities automatically.</p>', unsafe_allow_html=True)

    # Renders the styled file uploader
    uploaded_image = st.file_uploader(
        "Upload screenshot",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )

st.divider()

# Triggers the portfolio analysis
analyze_button = st.button("🔍 Analyze Portfolio", type="primary", use_container_width=True)

if analyze_button:
    # Shows a visual cue to scroll down
    st.markdown("""
        <div style="
            background-color: #162d4a;
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 0.75rem;
            text-align: center;
            color: #0ea5e9;
            font-weight: 700;
            font-size: 1rem;
        ">
            ⬇️ Results are ready - scroll down to view
        </div>
    """, unsafe_allow_html=True)


    # Filters out empty rows
    valid_rows = [
        row for row in st.session_state.portfolio_rows
        if row["ticker"].strip() and row["quantity"] > 0
    ]

    if not valid_rows:
        st.warning("Please enter at least one ticker and quantity before analyzing.")
    else:
        with st.spinner("Fetching live prices..."):
            # Extracts the list of tickers
            tickers = [row["ticker"].upper().strip() for row in valid_rows]

            # Fetches current prices for all tickers
            prices = get_prices(tickers)

            # Builds the portfolio summary DataFrame
            summary_df = build_portfolio_summary(valid_rows, prices)

        if summary_df.empty:
            st.error("Could not fetch prices for any of the tickers. Please check your input.")
        else:
            st.divider()

            # Displays the Level 1 ETF summary section
            st.markdown('<div class="card-title">📊 Portfolio Summary</div>', unsafe_allow_html=True)
            st.markdown('<p style="color:#94a3b8; margin-bottom:1rem;">Shows the weight and value of each ETF or stock you hold directly. Scroll down for Level 2 - your real underlying stock exposure.</p>', unsafe_allow_html=True)

            # Calculates and displays total portfolio value by parsing formatted strings
            raw_total = sum(
                float(v.replace("$", "").replace(",", ""))
                for v in summary_df["Value ($)"]
                if v != "N/A"
            )
            st.metric(label="Total Portfolio Value", value=f"${raw_total:,.2f}")

            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )

# Renders the legal disclaimer footer
st.markdown("""
    <div class="disclaimer">
        PortfolioLens is for informational purposes only and does not constitute financial advice.
        Always consult a qualified financial advisor before making investment decisions.
    </div>
""", unsafe_allow_html=True)