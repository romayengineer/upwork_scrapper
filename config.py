import os
from dotenv import load_dotenv


load_dotenv()


UPWORK_URL = "https://www.upwork.com"

UPWORK_EMAIL = os.getenv("UPWORK_EMAIL")

UPWORK_PASSWORD = os.getenv("UPWORK_PASSWORD")

USER_DATA_DIR = os.getenv("USER_DATA_DIR")

CLUSTER_COUNT = int(os.getenv("CLUSTER_COUNT"))