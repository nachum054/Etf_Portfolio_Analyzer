import os
from dotenv import load_dotenv

# Loads environment variables from the .env file
load_dotenv()

# Retrieves the Massive API key stored safely in .env
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY", "")

# Base URL for all Massive API calls
MASSIVE_BASE_URL = "https://api.massive.com/etf-global/v1"