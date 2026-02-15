import os
import sys
from contextlib import suppress
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
    page.goto(f"{UPWORK_URL}/ab/account-security/login")
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

    page.locator("#fwh-sidebar-profile").wait_for(timeout=5000)
    print("Login successful!")


def scrape_jobs(page, max_jobs=10):
    print(f"Navigating to jobs page (max {max_jobs} jobs)...")
    page.goto(f"{UPWORK_URL}/nx/jobs/search/")

    jobs = []
    job_cards = page.locator('section[data-test="job-tile"]').all()[:max_jobs]

    for idx, card in enumerate(job_cards):
        try:
            title_elem = card.locator('a[data-test="job-title"]')
            title = title_elem.inner_text() if title_elem.count() > 0 else ""
            url = title_elem.get_attribute("href") if title_elem.count() > 0 else ""

            if url and not url.startswith("http"):
                url = UPWORK_URL + url

            desc_elem = card.locator('div[data-test="job-description"]')
            description = desc_elem.inner_text() if desc_elem.count() > 0 else ""

            budget_elem = card.locator('span[data-test="budget"]')
            budget = budget_elem.inner_text() if budget_elem.count() > 0 else ""

            skills_elem = card.locator('span[data-test="skill-name"]')
            skills = (
                ", ".join([s.inner_text() for s in skills_elem.all()])
                if skills_elem.count() > 0
                else ""
            )

            category_elem = card.locator('span[data-test="category"]')
            category = category_elem.inner_text() if category_elem.count() > 0 else ""

            posted_elem = card.locator('span[data-test="posted-on"]')
            posted_at = posted_elem.inner_text() if posted_elem.count() > 0 else ""

            client_elem = card.locator('span[data-test="client-info"]')
            client_info = client_elem.inner_text() if client_elem.count() > 0 else ""

            job_data = {
                "url": url,
                "title": title,
                "description": description,
                "budget": budget,
                "skills": skills,
                "category": category,
                "posted_at": posted_at,
                "client_info": client_info,
            }
            jobs.append(job_data)
            print(f"Scraped job {idx + 1}: {title[:50]}...")

        except Exception as e:
            print(f"Error scraping job {idx + 1}: {e}")
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

        try:
            login(page)
            jobs = scrape_jobs(page)

            saved_count = 0
            for job in jobs:
                if save_job(job):
                    saved_count += 1

            print(f"\nScraping complete! Saved {saved_count} new jobs to database.")

        except Exception as e:
            print(f"Error during scraping: {e}")


if __name__ == "__main__":
    main()
