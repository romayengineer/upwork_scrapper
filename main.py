import asyncio
import sys
import config
import locator
from contextlib import suppress
from database import init_db, save_job, get_job_by_id
from playwright._impl._errors import TimeoutError
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs


async def login(page):
    if not config.UPWORK_EMAIL:
        print("Error: Please set config.UPWORK_EMAIL in .env file")
        sys.exit(1)

    if not config.UPWORK_PASSWORD:
        print("Error: Please set config.UPWORK_PASSWORD in .env file")
        sys.exit(1)

    print("Logging in to Upwork...\n")

    await page.goto(config.LOGIN_URL)
    if page.url != config.LOGIN_URL:
        await locator.profile(page).wait_for(timeout=20000)
        print("already login\n")
        return

    await locator.button_continue(page).wait_for(timeout=20000)

    is_gmail = config.UPWORK_EMAIL.lower().endswith("@gmail.com")
    if is_gmail is False:
        raise NotImplementedError("Login implemented for gmail only")

    print("Gmail detected. Continuing with Google...")
    print("Google sign-in flow opened.")

    async with page.expect_popup() as popup_info:
        await locator.button_login_google(page).click()
        new_page = await popup_info.value
        try:
            await locator.input_email(new_page).wait_for(timeout=10000)
            await locator.input_email(new_page).fill(config.UPWORK_EMAIL, timeout=5000)
            await new_page.get_by_text("Siguiente").click()
            await locator.input_password(new_page).wait_for(timeout=5000)
            await locator.input_password(new_page).fill(
                config.UPWORK_PASSWORD, timeout=5000
            )
            await new_page.get_by_text("Siguiente").click()
            await locator.select_device(new_page).click(timeout=5000)
        except TimeoutError:
            await locator.select_google_account(new_page).click(timeout=5000)

    await locator.profile(page).wait_for(timeout=20000)

    print("Login successful!\n")


async def title_text(page):
    return await (await locator.title(page)).inner_text(timeout=5000)


async def description_text(page):
    return await (await locator.description(page)).inner_text(timeout=5000)


def get_url(page):
    # page url changes on every click of the article
    parse = urlparse(page.url)
    return f"{parse.scheme}://{parse.netloc}{parse.path}"


def get_job_url(page):
    parse = urlparse(page.url)
    job_id = parse.path.split("/")[-1]
    assert job_id[0] == "~"
    assert job_id[1:].isdigit()
    return f"{config.JOBS_URL}/{job_id}"


async def optimization_skip_processed(card):
    job_id = await card.get_attribute("data-ev-job-uid")
    if not job_id:
        job_id = await card.get_attribute("data-test-key")
    # this job id is truncated add ~02 at the beginning
    job_id = f"~02{job_id}"
    if job := get_job_by_id(job_id):
        return job[0]


async def scrape_jobs(page):
    jobs = []
    job_cards = await locator.jobs(page).all()

    for card in job_cards:
        try:
            job = await optimization_skip_processed(card)
            if job:
                print(f"job alredy processed {job[1]}")
                continue
            await card.click()
            with suppress(TimeoutError, locator.Incomplete):
                await (await locator.title(page)).wait_for(timeout=5000)
            with suppress(TimeoutError):
                await (await locator.description(page)).wait_for(timeout=5000)
            with suppress(TimeoutError):
                await (await locator.client(page)).wait_for(timeout=5000)
            url = get_job_url(page)
            title = await title_text(page)
            description = await description_text(page)
            print(url)
            print(title)
            print()
            job_data = {
                "url": url,
                "title": title,
                "description": description,
            }
            jobs.append(job_data)
            await page.keyboard.press("Escape")
        except (TimeoutError, locator.Incomplete) as e:
            print(f"Error scraping job: {e}")
            await page.keyboard.press("Escape")
            continue

    return jobs


def get_page_number(page):
    parsed = urlparse(page.url)
    params = dict(parse_qs(parsed.query))
    page_num = params.get("page")
    with suppress(ValueError, TypeError):
        return int(page_num[0])


async def main():
    init_db()
    await search_and_scrap()


async def open_browser_and_search(keyword):
    async with async_playwright() as p:
        print(f"open browser in headless mode = '{config.BROWSER_HEADLESS}'")
        context = await p.chromium.launch_persistent_context(
            channel="chrome",
            headless=config.BROWSER_HEADLESS,
            user_data_dir=config.USER_DATA_DIR,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
            ],
        )
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()

        await login(page)

        # sleep 5 seconds before opening pages
        await asyncio.sleep(5)

        if config.PROCESS_IN_PARALLEL:
            await scrap_pages_multiple(context, keyword)
        else:
            await scrap_pages(page, keyword)


async def search_and_scrap():
    keywords = config.SEARCH_KEYWORDS

    for keyword in keywords:
        await open_browser_and_search(keyword)


async def goto_search_page(page, keyword, page_number=1):
    await page.goto(f"{config.SEARCH_URL}/?q={keyword}&page={page_number}")


async def click_next_page(page, keyword, new_page_num):
    await (await locator.button_next(page)).wait_for(timeout=5000)
    await (await locator.button_next(page)).click()


async def loop_over_pages(page, keyword, search_func, next_page_func):
    page_num = 1

    while True:
        try:
            # wait for jobs to show
            await locator.jobs(page).first.wait_for(timeout=20000)

            # extract page details
            await search_func(page, page_num)

            # check page number before going to next page
            if page_num and page_num >= config.MAX_PAGE_NUMBER:
                print("reached maximum page number\n")
                break

            # go to next page
            await next_page_func(page, keyword, page_num + 1)

            # wait before checking page parameter if page number
            # does not exist then it will change from number to infinity
            # instead of returning 404
            await asyncio.sleep(5)

            # check if page number increased
            new_page_num = get_page_number(page) or 1

            if new_page_num <= page_num:
                print(f"page number did not increase\n")
                break

            page_num = new_page_num

        except TimeoutError as e:
            print(f"Error during scraping: {e}\n")

    return page_num


async def search_func(page, page_num):
    saved_count = 0

    jobs = await scrape_jobs(page)

    for job in jobs:
        if save_job(job):
            saved_count += 1

    print(f"Page {page_num} Saved {saved_count} new jobs to database.\n")


async def scrap_pages(page, keyword):
    print(f"searching for jobs '{keyword}'\n")

    await goto_search_page(page, keyword, page_number=1)

    await loop_over_pages(page, keyword, search_func, goto_search_page)

    print(f"search for {keyword} finished\n")


async def pool_of_pages(context, count: int) -> asyncio.Queue:
    pages = list(context.pages)

    create = count - len(pages)
    if create > 0:
        for _ in range(create):
            page = await context.new_page()
            pages.append(page)

    queue = asyncio.Queue(maxsize=count)
    for page in pages[:count]:
        await queue.put(page)

    return queue


async def scrap_pages_multiple(context, keyword):
    page_queue = await pool_of_pages(context, config.PAGES_IN_PARALLEL)
    work_queue = asyncio.Queue()

    for page_number in range(1, config.MAX_PAGE_NUMBER + 1):
        await work_queue.put(page_number)

    async def worker(worker_id: int):
        while True:
            page_number = await work_queue.get()
            page = await page_queue.get()
            try:
                # sleep 5 seconds on each search page
                await asyncio.sleep(5)
                await goto_search_page(page, keyword, page_number)
                await search_func(page, page_number)
            finally:
                await page_queue.put(page)
                work_queue.task_done()

    workers = [asyncio.create_task(worker(i)) for i in range(page_queue.maxsize)]
    await work_queue.join()

    for task in workers:
        task.cancel()
    await asyncio.gather(*workers, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
