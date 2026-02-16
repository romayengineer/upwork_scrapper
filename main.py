import sys
import config
import locator
from time import sleep
from contextlib import suppress
from database import init_db, save_job
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs


def login(page):

    if not config.UPWORK_EMAIL:
        print("Error: Please set config.UPWORK_EMAIL in .env file")
        sys.exit(1)

    if not config.UPWORK_PASSWORD:
        print("Error: Please set config.UPWORK_PASSWORD in .env file")
        sys.exit(1)

    print("Logging in to Upwork...")

    page.goto(config.LOGIN_URL)
    if page.url != config.LOGIN_URL:
        locator.profile(page).wait_for(timeout=20000)
        print("already login")
        return

    locator.button_continue(page).wait_for(timeout=5000)

    is_gmail = config.UPWORK_EMAIL.lower().endswith("@gmail.com")
    if is_gmail is False:
        raise NotImplementedError("Login implemented for gmail only")

    print("Gmail detected. Continuing with Google...")
    print("Google sign-in flow opened.")

    with page.expect_popup() as popup_info:
        locator.button_login_google(page).click()
        new_page = popup_info.value
        try:
            locator.input_email(new_page).wait_for(timeout=10000)
            locator.input_email(new_page).fill(config.UPWORK_EMAIL, timeout=5000)
            new_page.get_by_text("Siguiente").click()
            locator.input_password(new_page).wait_for(timeout=5000)
            locator.input_password(new_page).fill(config.UPWORK_PASSWORD, timeout=5000)
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
        context = p.chromium.launch_persistent_context(
            channel="chrome",
            headless=False,
            user_data_dir=config.USER_DATA_DIR,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
            ],
        )
        page = context.new_page()

        login(page)
        search_and_scrap(page)


def search_and_scrap(page):

    keywords = config.SEARCH_KEYWORDS

    for keyword in keywords:
        scrap_pages(page, keyword)


def goto_search_page(page, keyword, page_number=1):
    page.goto(f"{config.SEARCH_URL}/?q={keyword}&page={page_number}")


def click_next_page(page, keyword, new_page_num):
    locator.button_next(page).wait_for(timeout=5000)
    locator.button_next(page).click()


def loop_over_pages(page, keyword, search_func, next_page_func):
    page_num = 1

    while True:
        try:
            locator.jobs(page).first.wait_for(timeout=20000)

            # extract page details
            search_func(page, page_num)

            next_page_func(page, keyword, page_num + 1)

            # wait before checking page parameter if page number
            # does not exist then it will change from number to infinity
            # instead of returning 404
            sleep(5)

            new_page_num = get_page_number(page) or 1

            if new_page_num <= page_num:
                print(f"page number did not increase")
                break

            page_num = new_page_num

            if page_num and page_num >= config.MAX_PAGE_NUMBER + 1:
                print("reached maximum page number")
                break

        except TimeoutError as e:
            print(f"Error during scraping: {e}")

    return page_num


def search_func(page, page_num):
    saved_count = 0

    jobs = scrape_jobs(page)

    for job in jobs:
        if save_job(job):
            saved_count += 1

    print(f"\nPage {page_num} Saved {saved_count} new jobs to database.\n")


def scrap_pages(page, keyword):
    print(f"searching for jobs '{keyword}'\n")

    goto_search_page(page, keyword, page_number=1)

    loop_over_pages(page, keyword, search_func, goto_search_page)

    print(f"search for {keyword} finished")


if __name__ == "__main__":
    main()
