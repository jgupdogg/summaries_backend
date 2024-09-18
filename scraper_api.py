import requests
from dotenv import load_dotenv
import os 
import logging

# Load environment variables from .env file
load_dotenv()

# Constants for the scraper endpoint and headers
SCRAPER_URL = "http://scraper-env.eba-2mfn56ye.us-east-2.elasticbeanstalk.com/scrape"
SCRAPER_KEY = os.getenv('SCRAPER_KEY')

if not SCRAPER_KEY:
    raise ValueError("SCRAPER_KEY not found in environment variables.")

HEADERS = {
    'Access-Token': SCRAPER_KEY,
    'Content-Type': 'application/json'
}


def make_scraper_request(url, use_proxy=True):
    """
    Sends a POST request to the scraper endpoint with the specified URL and proxy settings.

    Args:
        url (str): The URL to scrape.
        use_proxy (bool): Whether to use a proxy for the request.

    Returns:
        str: The HTML content of the scraped page.

    Raises:
        requests.HTTPError: If the request fails.
    """
    payload = {
        "url": url,
        "use_proxy": use_proxy
    }

    try:
        response = requests.post(SCRAPER_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.text  # Assuming the scraper returns HTML content as text
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for URL {url}: {e}")
        raise