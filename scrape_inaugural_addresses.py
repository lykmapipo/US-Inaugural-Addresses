"""
Scrape inaugural addresses from The American Presidency Project website.

Usage::

    pip install requests beautifulsoup4 joblib fake-useragent
    python scrape_inaugural_addresses.py

"""

import logging
import re
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from joblib import Parallel, delayed

INAUGURALS_SOURCE_URL = (
    "https://www.presidency.ucsb.edu/documents/presidential-documents-archive-guidebook/inaugural-addresses"  # noqa
)
INAUGURALS_URL_SELECTOR = "div.field-body > table > tbody > tr > td > a[href*=inaugural]"
INAUGURAL_PRESIDENT_SELECTOR = "div.field-docs-person > div > div.field-title > h3.diet-title"
INAUGURAL_YEAR_SELECTOR = "div.field-docs-start-date-time > span"
INAUGURAL_SPEECH_SELECTOR = "div.field-docs-content"

DATASET_BASE_PATH = Path("./data")
DATASET_RAW_PATH = DATASET_BASE_PATH / "raw"
DATASET_INAUGURAL_ADDRESSES_PATH = DATASET_RAW_PATH / "inaugural-addresses"

PARALLEL_NUM_JOBS = -1
PARALLEL_VERBOSITY_LEVEL = 10

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

REQUEST_USER_AGENT_OS = ["linux"]  # ["windows", "macos", "linux"]
REQUEST_USER_AGENT_BROWSERS = ["chrome"]  # ["chrome", "edge", "firefox", "safari"]
REQUEST_BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36",  # noqa
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua-mobile": "?0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}


def _configure_logging():
    """Configure basic multiprocessing loggging."""
    if len(logging.getLogger().handlers) == 0:
        logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)


def _slugify(text=None):
    """Convert a text to a URL-safe slug."""
    slug = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug).strip("-")
    slug = slug.lower()
    return slug


def scrape_inaugural_urls():
    """Scrape and yield url for each inaugural."""
    _configure_logging()

    # request inagural addresses table/list
    ua = UserAgent(os=REQUEST_USER_AGENT_OS, browsers=REQUEST_USER_AGENT_BROWSERS)
    headers = {**REQUEST_BASE_HEADERS, **{"user-agent": ua.googlechrome}}
    urls_response = requests.get(INAUGURALS_SOURCE_URL, headers=headers)
    urls_soup = BeautifulSoup(urls_response.text, "lxml")

    # scrape url for each inagural address
    urls_tags = urls_soup.select(INAUGURALS_URL_SELECTOR)
    for url_tag in urls_tags:
        url_href = url_tag.get("href") or None
        if url_href:
            yield url_href.strip()


def scrape_inaugural(url=None):
    """Scrape and save text of an inaugural."""
    _configure_logging()

    # request inagural address
    logging.info(f"Scraping inaugural address {url} ...")
    ua = UserAgent(os=REQUEST_USER_AGENT_OS, browsers=REQUEST_USER_AGENT_BROWSERS)
    headers = {**REQUEST_BASE_HEADERS, **{"user-agent": ua.googlechrome}}
    inagural_response = requests.get(url, headers=headers)
    inagural_soup = BeautifulSoup(inagural_response.text, "lxml")

    # parse president name
    president_name_tag = inagural_soup.select_one(INAUGURAL_PRESIDENT_SELECTOR)
    president_name = president_name_tag.text.strip()

    # parse inagural year
    year_tag = inagural_soup.select_one(INAUGURAL_YEAR_SELECTOR)
    year = year_tag.text.strip()
    year = year.split(",")[-1].strip() if year else None

    # parse inagural speech
    speech_tag = inagural_soup.select_one(INAUGURAL_SPEECH_SELECTOR)
    speech = speech_tag.text.strip()

    # save inaugural speech into text file {year}-{president}.txt
    if president_name and year and speech:
        inagural_file_path = "-".join([year, president_name])
        inagural_file_path = _slugify(inagural_file_path)
        inagural_file_path = DATASET_INAUGURAL_ADDRESSES_PATH / f"{inagural_file_path}.txt"
        inagural_file_path.expanduser().resolve()
        inagural_file_path.parent.mkdir(exist_ok=True, parents=True)
        logging.info(f"Saving inagural address at {inagural_file_path}")
        with open(inagural_file_path, "w") as inagural_file:
            inagural_file.write(speech)

    logging.info(f"Scraping inaugural address {url} finished.")


_configure_logging()
logging.info("Start.")

logging.info("Scraping inaugural addresses urls ...")
inaugural_urls = scrape_inaugural_urls()
logging.info("Scraping inaugural addresses urls finished.")

logging.info("Scraping inaugural addresses data ...")
Parallel(n_jobs=PARALLEL_NUM_JOBS, verbose=PARALLEL_VERBOSITY_LEVEL)(
    delayed(scrape_inaugural)(url=inaugural_url) for inaugural_url in inaugural_urls
)
logging.info("Scraping inaugural addresses data finished.")

logging.info("Done.")
