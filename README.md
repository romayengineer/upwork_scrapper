# Upwork Job Scraper

A Python project that uses Playwright to scrape job posts from Upwork and store them in an SQLite database.

## Features

- Automated login to Upwork via Google SSO
- Stealth browser launch to avoid bot detection
- Uses existing Chrome profile for realistic browsing
- Scrapes job details from job tiles (title, URL, description)
- Stores data in SQLite database (`jobs.db`)
- Prevents duplicate entries using unique URL constraint

## Requirements

- Python 3.10+
- Google Chrome browser installed
- Chrome profile for login (to avoid bot detection)

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chrome
   ```

4. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Environment Variables

Create a `.env` file with:

| Variable | Description | Required |
|----------|-------------|----------|
| `UPWORK_EMAIL` | Your Upwork email (@gmail.com only) | Yes |
| `UPWORK_PASSWORD` | Your Upwork password | Yes |
| `USER_DATA_DIR` | Path to Chrome profile | Yes |

**To get Chrome profile path on macOS:**
```bash
ls ~/Library/Application\ Support/Google/Chrome/
```
Use a path like:
```
/Users/yourname/Library/Application Support/Google/Chrome/Default
```

## Usage

```bash
python main.py
```

The scraper will:
1. Initialize the SQLite database
2. Open Chrome with your existing profile
3. Navigate to Upwork login page
4. If already logged in, skip login; otherwise, complete Google SSO
5. Navigate to jobs search page
6. Click each job tile to get full details (URL changes on click)
7. Extract title, description, and URL
8. Store scraped jobs in `jobs.db`

## Database Schema

The `jobs` table contains:

| Column | Type | Description |
|--------|------|-------------|
| `url` | TEXT PRIMARY KEY | Unique job URL |
| `title` | TEXT | Job title |
| `description` | TEXT | Full job description |
| `budget` | TEXT | Job budget (not currently scraped) |
| `skills` | TEXT | Required skills (not currently scraped) |
| `category` | TEXT | Job category (not currently scraped) |
| `posted_at` | TEXT | When job was posted (not currently scraped) |
| `client_info` | TEXT | Client information (not currently scraped) |
| `scraped_at` | TEXT | Timestamp when job was scraped (ISO format) |

## Stealth Features

The browser launches with these arguments to avoid detection:
- `--disable-blink-features=AutomationControlled` - Hides automation flags
- `--disable-infobars` - Removes automation warning banner
- `--disable-dev-shm-usage` - Better stability
- Uses persistent Chrome context with existing user profile

## Project Structure

```
.
├── main.py           # Main scraping script
├── database.py       # SQLite database operations
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (credentials)
├── .env.example      # Example environment file
├── jobs.db           # SQLite database (created on first run)
└── README.md         # This file
```

## Notes

- Currently only supports Gmail/Google SSO login
- Browser runs in non-headless mode using your Chrome profile
- The scraper clicks each job tile to get the full URL (Upwork loads details dynamically)
- Press `Escape` to close job details popup after each scrape
- Default scrapes 10 jobs. Modify `max_jobs` parameter in `scrape_jobs()` to change this