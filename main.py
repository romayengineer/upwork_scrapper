import os
import sys
from contextlib import suppress
from urllib.parse import urlparse
from database import init_db, save_job
from dotenv import load_dotenv
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright

UPWORK_URL = "https://www.upwork.com"


def login(page):
    email = os.getenv("UPWORK_EMAIL")
    password = os.getenv("UPWORK_PASSWORD")

    if not email:
        print("Error: Please set UPWORK_EMAIL in .env file")
        sys.exit(1)

    if not password:
        print("Error: Please set UPWORK_PASSWORD in .env file")
        sys.exit(1)

    print("Logging in to Upwork...")
    login_url = f"{UPWORK_URL}/ab/account-security/login"
    page.goto(login_url)
    if page.url != login_url:
        page.locator("#fwh-sidebar-profile").wait_for(timeout=20000)
        print("already login")
        return
    page.locator("#login_password_continue").wait_for(timeout=5000)

    is_gmail = email.lower().endswith("@gmail.com")
    if is_gmail is False:
        raise NotImplementedError("Login implemented for gmail only")
    print("Gmail detected. Continuing with Google...")
    print("Google sign-in flow opened.")
    with page.expect_popup() as popup_info:
        page.locator("#login_google_submit").click()
        new_page = popup_info.value
        try:
            new_page.locator('input[type="identifier"]').wait_for(timeout=5000)
            new_page.locator('input[name="identifier"]').fill(email, timeout=5000)
            new_page.get_by_text("Siguiente").click()
            new_page.locator('input[type="password"]').wait_for(timeout=5000)
            new_page.locator('input[type="password"]').fill(password, timeout=5000)
            new_page.get_by_text("Siguiente").click()
            new_page.locator('div > strong:has-text("Sí")').click(timeout=5000)
        except TimeoutError:
            new_page.locator(f'div[data-email="{email}"]').click(timeout=5000)

    page.locator("#fwh-sidebar-profile").wait_for(timeout=20000)
    print("Login successful!")


class Incomplete(Exception):
    pass

def locator_client(page):
    return page.locator('h5:has-text("About the client")').first

def description_locator(page):
    return page.locator('div[data-test="Description Description"]').first

def description_text(page):
    return description_locator(page).inner_text(timeout=5000)

def title_locator(page):
    for e in page.locator('h4').all():
        text = e.inner_text(timeout=5000)
        if "Featured" not in text:
            return e
    raise Incomplete("no title found")

def title_text(page):
    return title_locator(page).inner_text()


def get_url(page):
    # page url changes on every click of the article
    parse = urlparse(page.url)
    return f"{parse.scheme}://{parse.netloc}{parse.path}"


def scrape_jobs(page, max_jobs=20):

    jobs = []
    job_cards = page.locator('article[data-test="JobTile"]').all()[:max_jobs]

    for card in job_cards:
        try:
            card.click()
            with suppress(TimeoutError, Incomplete):
                title_locator(page).wait_for(timeout=5000)
            with suppress(TimeoutError):
                description_locator(page).wait_for(timeout=5000)
            with suppress(TimeoutError):
                locator_client(page).wait_for(timeout=5000)
            url = get_url(page)
            title = title_text(page)
            description = description_text(page)
            print(url)
            print(title)
            print()
            job_data = {
                "url": url,
                "title": title,
                "description": description,
            }
            jobs.append(job_data)
            page.keyboard.press("Escape")
        except (TimeoutError, Incomplete) as e:
            print(f"Error scraping job: {e}")
            page.keyboard.press("Escape")
            continue

    return jobs


def main():
    load_dotenv()
    init_db()
    print("Database initialized.")

    with sync_playwright() as p:
        user_data_dir = os.getenv("USER_DATA_DIR")
        context = p.chromium.launch_persistent_context(
            channel="chrome",
            headless=False,
            user_data_dir=user_data_dir,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
            ],
        )
        # context = browser.new_context()
        page = context.new_page()

        login(page)

        max_jobs = 10
        print(f"Navigating to jobs page (max {max_jobs} jobs)...")
        page.goto(f"{UPWORK_URL}/nx/search/jobs/?q=python")

        saved_count = 0

        while True:
            try:
                page.locator('article[data-test="JobTile"]').first.wait_for(timeout=5000)

                jobs = scrape_jobs(page)

                for job in jobs:
                    if save_job(job):
                        saved_count += 1

                page.locator('li.air3-pagination-item').nth(1).wait_for(timeout=5000)
                # click next
                page.locator('li.air3-pagination-item').nth(1).click()

                print(f"\nSaved {saved_count} new jobs to database.")
            except TimeoutError as e:
                print(f"Error during scraping: {e}")


if __name__ == "__main__":
    main()
