import os
import sys
from dotenv import load_dotenv
from contextlib import suppress
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError

from database import init_db, save_job

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
    with suppress(TimeoutError):
        page.wait_for_load_state("networkidle")

    page.fill('input[name="login[username]"]', email)

    is_gmail = email.lower().endswith("@gmail.com")
    if is_gmail:
        print("Gmail detected. Continuing with Google...")
        page.get_by_role("button", name="Continue with Google").click()
        page.wait_for_load_state("networkidle")
        print("Google sign-in flow opened.")
        return

    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    page.fill('input[name="login[password]"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("Login successful!")


def scrape_jobs(page, max_jobs=10):
    print(f"Navigating to jobs page (max {max_jobs} jobs)...")
    page.goto(f"{UPWORK_URL}/nx/jobs/search/")
    page.wait_for_load_state("networkidle")

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
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()
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
        finally:
            browser.close()


if __name__ == "__main__":
    main()
