from config import UPWORK_EMAIL


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
    return page.locator(f'div[data-email="{UPWORK_EMAIL}"]')

def client(page):
    return page.locator('h5:has-text("About the client")').first

def title(page):
    for e in page.locator('h4').all():
        text = e.inner_text(timeout=5000)
        if "Featured" not in text:
            return e
    raise Incomplete("no title found")

def description(page):
    return page.locator('div[data-test="Description Description"]').first

def jobs(page):
    return page.locator('article[data-test="JobTile"]')

def button_next(page):
    return page.locator('li.air3-pagination-item').nth(1)