import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


UPWORK_URL = "https://www.upwork.com"

LOGIN_URL = f"{UPWORK_URL}/ab/account-security/login"

SEARCH_URL = f"{UPWORK_URL}/nx/search/jobs"

JOBS_URL = f"{UPWORK_URL}/jobs"

UPWORK_EMAIL = os.getenv("UPWORK_EMAIL")

UPWORK_PASSWORD = os.getenv("UPWORK_PASSWORD")

USER_DATA_DIR = os.getenv("USER_DATA_DIR")

CLUSTER_COUNT = int(os.getenv("CLUSTER_COUNT"))

MAX_PAGE_NUMBER = int(os.getenv("MAX_PAGE_NUMBER"))

SEARCH_KEYWORDS = os.getenv("SEARCH_KEYWORDS")
SEARCH_KEYWORDS = [] if SEARCH_KEYWORDS is None else SEARCH_KEYWORDS.split(",")

BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true")
BROWSER_HEADLESS = BROWSER_HEADLESS.lower() == "true"

DB_PATH = Path(__file__).parent / "jobs.db"
