import sys
from contextlib import suppress
from database import init_db, save_job
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs
import locator
from config import UPWORK_EMAIL, UPWORK_PASSWORD, USER_DATA_DIR, LOGIN_URL, SEARCH_URL, MAX_PAGE_NUMBER


def login(page):

    if not UPWORK_EMAIL:
        print("Error: Please set UPWORK_EMAIL in .env file")
        sys.exit(1)

    if not UPWORK_PASSWORD:
        print("Error: Please set UPWORK_PASSWORD in .env file")
        sys.exit(1)

    print("Logging in to Upwork...")

    page.goto(LOGIN_URL)
    if page.url != LOGIN_URL:
        locator.profile(page).wait_for(timeout=20000)
        print("already login")
        return

    locator.button_continue(page).wait_for(timeout=5000)

    is_gmail = UPWORK_EMAIL.lower().endswith("@gmail.com")
    if is_gmail is False:
        raise NotImplementedError("Login implemented for gmail only")

    print("Gmail detected. Continuing with Google...")
    print("Google sign-in flow opened.")

    with page.expect_popup() as popup_info:
        locator.button_login_google(page).click()
        new_page = popup_info.value
        try:
            locator.input_email(new_page).wait_for(timeout=20000)
            locator.input_email(new_page).fill(UPWORK_EMAIL, timeout=5000)
            new_page.get_by_text("Siguiente").click()
            locator.input_password(new_page).wait_for(timeout=5000)
            locator.input_password(new_page).fill(UPWORK_PASSWORD, timeout=5000)
            new_page.get_by_text("Siguiente").click()
            locator.select_device(new_page).click(timeout=5000)
        except TimeoutError:
            locator.select_google_account(new_page).click(timeout=5000)

    locator.profile(page).wait_for(timeout=20000)

    print("Login successful!")


def title_text(page):
    return locator.title(page).inner_text(timeout=5000)

def description_text(page):
    return locator.description(page).inner_text(timeout=5000)


def get_url(page):
    # page url changes on every click of the article
    parse = urlparse(page.url)
    return f"{parse.scheme}://{parse.netloc}{parse.path}"

def get_job_url(page):
    parse = urlparse(page.url)
    job_id = parse.path.split("/")[-1]
    assert job_id[0] == "~"
    assert job_id[1:].isdigit()
    return f"https://www.upwork.com/jobs/{job_id}"


def scrape_jobs(page, max_jobs=20):

    jobs = []
    job_cards = locator.jobs(page).all()[:max_jobs]

    for card in job_cards:
        try:
            card.click()
            with suppress(TimeoutError, locator.Incomplete):
                locator.title(page).wait_for(timeout=5000)
            with suppress(TimeoutError):
                locator.description(page).wait_for(timeout=5000)
            with suppress(TimeoutError):
                locator.client(page).wait_for(timeout=5000)
            url = get_job_url(page)
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
        except (TimeoutError, locator.Incomplete) as e:
            print(f"Error scraping job: {e}")
            page.keyboard.press("Escape")
            continue

    return jobs


def get_page_number(page):
    parsed = urlparse(page.url)
    params = dict(parse_qs(parsed.query))
    page_num = params.get("page")
    with suppress(ValueError, TypeError):
        return int(page_num[0])


def main():
    init_db()
    print("Database initialized.")

    with sync_playwright() as p:
        user_data_dir = USER_DATA_DIR
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
        page.goto(f"{SEARCH_URL}/?q=python")

        saved_count = 0

        while True:
            try:
                page_num = get_page_number(page)

                if page_num and page_num >= MAX_PAGE_NUMBER + 1:
                    print("process finished")
                    return

                locator.jobs(page).first.wait_for(timeout=20000)

                jobs = scrape_jobs(page)

                for job in jobs:
                    if save_job(job):
                        saved_count += 1

                locator.button_next(page).wait_for(timeout=5000)
                # click next
                locator.button_next(page).nth(1).click()

                print(f"\nPage {page_num} Saved {saved_count} new jobs to database.")
            except TimeoutError as e:
                print(f"Error during scraping: {e}")


if __name__ == "__main__":
    main()
