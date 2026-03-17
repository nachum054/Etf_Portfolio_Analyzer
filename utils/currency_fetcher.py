# Fetches live currency exchange rates from the Frankfurter API (no API key required)

import requests

# Defines the list of supported currencies with their display names
SUPPORTED_CURRENCIES = {
    "USD": "US Dollar",
    "ILS": "Israeli Shekel",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "INR": "Indian Rupee",
    "BRL": "Brazilian Real",
    "MXN": "Mexican Peso",
    "SGD": "Singapore Dollar",
    "HKD": "Hong Kong Dollar",
    "NOK": "Norwegian Krone",
    "SEK": "Swedish Krona",
    "DKK": "Danish Krone",
    "NZD": "New Zealand Dollar",
    "ZAR": "South African Rand",
    "KRW": "South Korean Won",
    "TRY": "Turkish Lira",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "THB": "Thai Baht",
    "MYR": "Malaysian Ringgit",
    "IDR": "Indonesian Rupiah",
    "PHP": "Philippine Peso",
    "PLN": "Polish Zloty",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "RON": "Romanian Leu",
    "CLP": "Chilean Peso",
    "COP": "Colombian Peso",
    "PEN": "Peruvian Sol",
    "ARS": "Argentine Peso",
}

# Fetches the exchange rate from USD to the target currency
# Returns the rate as a float, or None if the request fails
def get_exchange_rate(target_currency: str) -> float | None:
    if target_currency == "USD":
        return 1.0

    try:
        url = f"https://api.frankfurter.app/latest?from=USD&to={target_currency}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["rates"][target_currency]
    except Exception:
        return None

# Returns the currency symbol for display purposes
def get_currency_symbol(currency_code: str) -> str:
    symbols = {
        "USD": "$",
        "ILS": "₪",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$",
        "CHF": "Fr",
        "CNY": "¥",
        "INR": "₹",
        "BRL": "R$",
        "MXN": "MX$",
        "SGD": "S$",
        "HKD": "HK$",
        "NOK": "kr",
        "SEK": "kr",
        "DKK": "kr",
        "NZD": "NZ$",
        "ZAR": "R",
        "KRW": "₩",
        "TRY": "₺",
        "AED": "د.إ",
        "SAR": "﷼",
        "THB": "฿",
        "MYR": "RM",
        "IDR": "Rp",
        "PHP": "₱",
        "PLN": "zł",
        "CZK": "Kč",
        "HUF": "Ft",
        "RON": "lei",
        "CLP": "CLP$",
        "COP": "COL$",
        "PEN": "S/",
        "ARS": "AR$",
    }
    return symbols.get(currency_code, currency_code)