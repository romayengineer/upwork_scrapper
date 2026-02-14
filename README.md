# Upwork Job Scraper

A Python project that uses Playwright to scrape job posts from Upwork and store them in an SQLite database.

## Features

- Automated login to Upwork (supports email/password and Google SSO)
- Scrapes job details including title, description, budget, skills, category, and client info
- Stores data in SQLite database (`jobs.db`)
- Prevents duplicate entries using unique URL constraint

## Requirements

- Python 3.10+
- Virtual environment (venv)

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
   # Edit .env and add your Upwork credentials
   ```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `UPWORK_EMAIL` | Your Upwork email address |
| `UPWORK_PASSWORD` | Your Upwork password |

**Note:** If your email ends with `@gmail.com`, the scraper will redirect you to Google SSO login.

## Usage

```bash
python main.py
```

The scraper will:
1. Initialize the SQLite database
2. Log you into Upwork (opens browser window)
3. Navigate to jobs search page
4. Scrape job details and store them in `jobs.db`

## Database Schema

The `jobs` table contains:

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `url` | Unique job URL |
| `title` | Job title |
| `description` | Job description |
| `budget` | Job budget |
| `skills` | Required skills (comma-separated) |
| `category` | Job category |
| `posted_at` | When the job was posted |
| `client_info` | Client information |
| `scraped_at` | Timestamp when job was scraped |

## Project Structure

```
.
├── main.py           # Main scraping script
├── database.py       # SQLite database operations
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (credentials)
├── .env.example      # Example environment file
└── jobs.db           # SQLite database (created on first run)
```

## Notes

- The browser runs in non-headless mode so you can complete 2FA if needed
- Upwork may change their DOM structure; you may need to update selectors in `main.py`
- The scraper defaults to scraping 10 jobs. Modify `max_jobs` parameter in `scrape_jobs()` to change this