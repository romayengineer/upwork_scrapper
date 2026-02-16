import config


class Incomplete(Exception):
    pass


def profile(page):
    return page.locator("#fwh-sidebar-profile")


def button_continue(page):
    return page.locator("#login_password_continue")


def button_login_google(page):
    return page.locator("#login_google_submit")


def input_email(page):
    return page.locator('input[type="email"]')


def input_password(page):
    return page.locator('input[type="password"]')


def select_device(page):
    return page.locator('div > strong:has-text("Sí")')


def select_google_account(page):
    return page.locator(f'div[data-email="{config.UPWORK_EMAIL}"]')


async def client(page):
    return page.locator('h5:has-text("About the client")').first


async def title(page):
    titles = await page.locator("h4").all()
    for e in titles:
        text = await e.inner_text(timeout=5000)
        if "Featured" not in text:
            return e
    raise Incomplete("no title found")


async def description(page):
    return page.locator('div[data-test="Description Description"]').first


def jobs(page):
    return page.locator('article[data-test="JobTile"]')


def button_next(page):
    return page.locator("li.air3-pagination-item").nth(1)
