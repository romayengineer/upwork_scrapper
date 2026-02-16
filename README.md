# Upwork Job Scraper

A Python project that uses Playwright to scrape job posts from Upwork, stores them in an SQLite database, and provides tools for word frequency analysis and job clustering.

## Features

- **Async Playwright**: Fully async implementation for better performance
- **Parallel Processing**: Run multiple pages concurrently using worker pools
- **Page Pool Queue**: Reusable pool of pages for concurrent scraping
- **Session Persistence**: Saves login state to reuse on subsequent runs
- **Automated Job Scraping**: Scrapes job posts from Upwork with title, URL, and description
- **Google SSO Login**: Automated login via Gmail (upwork.com/@gmail.com accounts)
- **Multiple Keywords**: Search multiple keywords in a single run
- **Pagination Support**: Automatically navigates through multiple pages (configurable limit)
- **Optimization**: Skips already processed jobs to avoid duplicates
- **Stealth Browser**: Uses Chrome with stealth arguments to avoid bot detection
- **Headless Mode**: Configurable browser mode (headless or visible)
- **Word Frequency Analysis**: Count and analyze common words across all jobs
- **Job Clustering**: Auto-categorize jobs using sentence embeddings and machine learning

## Requirements

- Python 3.10+
- Google Chrome browser installed

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

4. **Download NLTK data:**
   ```bash
   python -c "import nltk; nltk.download('stopwords')"
   ```

5. **Configure credentials:**
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
| `CLUSTER_COUNT` | Number of clusters for job categorization | Yes |
| `MAX_PAGE_NUMBER` | Maximum number of pages to scrape per keyword | Yes |
| `SEARCH_KEYWORDS` | Comma-separated keywords to search (e.g., "python,javascript") | Yes |
| `BROWSER_HEADLESS` | Run browser in headless mode (true/false, default: true) | No |
| `PROCESS_IN_PARALLEL` | Enable parallel page processing (true/false, default: false) | No |
| `PAGES_IN_PARALLEL` | Number of pages to use in parallel (default: 2) | No |
| `STORAGE_STATE_PATH` | Path to store login session (default: storage_state.json) | No |

## Usage

### Scrape Jobs (Sequential - Single Page)
```bash
python main.py
```
- Opens Chrome (headless or visible based on config)
- Logs in via Google SSO if not already logged in
- Saves login session to `storage_state.json` for reuse
- Iterates through all keywords in `SEARCH_KEYWORDS`
- For each keyword, navigates through pages until `MAX_PAGE_NUMBER` is reached
- Skips already processed jobs (optimization feature)
- Stores jobs in `jobs.db`

### Scrape Jobs (Parallel - Multiple Pages)
Set `PROCESS_IN_PARALLEL=true` in your `.env` file to enable parallel processing:
```bash
python main.py
```
- Uses a pool of pages (configurable via `PAGES_IN_PARALLEL`, default 2)
- Each worker processes different page numbers concurrently
- Work queue manages page numbers, page queue manages available pages

### Word Frequency Analysis
```bash
python count.py
```
- Analyzes all job titles and descriptions
- Removes English stop words
- Case-insensitive counting
- Displays top 100 most common words

### Job Clustering
```bash
python cluster.py              # Uses CLUSTER_COUNT from config
python cluster.py 12           # Override with custom cluster count
```
- Uses sentence-transformers (all-MiniLM-L6-v2) for semantic embeddings
- Clusters jobs using K-Means algorithm
- Generates category labels using TF-IDF keywords
- Updates `category` column in database
- Shows cluster summary with examples

## Database Schema

The `jobs` table contains:

| Column | Type | Description |
|--------|------|-------------|
| `url` | TEXT PRIMARY KEY | Unique job URL |
| `title` | TEXT | Job title |
| `description` | TEXT | Full job description |
| `budget` | TEXT | Job budget (not currently scraped) |
| `skills` | TEXT | Required skills (not currently scraped) |
| `category` | TEXT | Job category (populated by cluster.py) |
| `posted_at` | TEXT | When job was posted (not currently scraped) |
| `client_info` | TEXT | Client information (not currently scraped) |
| `scraped_at` | TEXT | Timestamp when job was scraped (ISO format) |

## Project Structure

```
.
├── main.py           # Job scraping script (async)
├── config.py         # Centralized configuration
├── locator.py        # Page element locators
├── database.py       # SQLite database operations
├── count.py          # Word frequency analysis
├── cluster.py        # Job clustering with ML
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (credentials)
├── .env.example      # Example environment file
├── jobs.db           # SQLite database (created on first run)
├── storage_state.json # Saved login session (generated on first run)
└── README.md         # This file
```

## Parallel Processing Architecture

The scraper uses two async queues:

1. **Work Queue**: Contains page numbers to process (1, 2, 3, ..., MAX_PAGE_NUMBER)
2. **Page Queue**: Contains available browser pages from the pool

**Worker Pattern:**
```
[Worker 1] -> get page_number from work_queue -> get page from page_queue -> do work -> return page to page_queue
[Worker 2] -> get page_number from work_queue -> get page from page_queue -> do work -> return page to page_queue
```

This allows true concurrent processing - both workers can process different pages simultaneously.

## Stealth Features

The browser launches with these arguments to avoid detection:
- `--disable-blink-features=AutomationControlled` - Hides automation flags
- `--disable-infobars` - Removes automation warning banner
- `--disable-dev-shm-usage` - Better stability

## Session Persistence

- On first run, after successful login, the session is saved to `storage_state.json`
- Subsequent runs load this file to skip login
- To force re-login, delete the `storage_state.json` file

## Optimization Features

- **Duplicate Prevention**: Uses `get_job_by_id()` to check if job already exists before scraping
- **Skip Processed Jobs**: The `optimization_skip_processed()` function extracts job ID from the card element and skips if found in database
- **Delay Between Pages**: 5-second delay to prevent rate limiting

## Notes

- Currently only supports Gmail/Google SSO login
- Browser runs in headless mode by default (configurable via `BROWSER_HEADLESS`)
- Default search keywords must be configured in `.env`
- The scraper clicks each job tile to get the full URL (Upwork loads details dynamically)
- Press `Escape` to close job details popup after each scrape
- Scraping stops after reaching `MAX_PAGE_NUMBER` pages per keyword
- Multiple keywords are processed sequentially in one run
- Use `PROCESS_IN_PARALLEL=true` to enable concurrent page processing