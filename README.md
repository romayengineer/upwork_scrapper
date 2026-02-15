# Upwork Job Scraper

A Python project that uses Playwright to scrape job posts from Upwork, stores them in an SQLite database, and provides tools for word frequency analysis and job clustering.

## Features

- **Automated Job Scraping**: Scrapes job posts from Upwork with title, URL, and description
- **Google SSO Login**: Automated login via Gmail (upwork.com/@gmail.com accounts)
- **Pagination Support**: Automatically navigates through multiple pages
- **Stealth Browser**: Uses existing Chrome profile to avoid bot detection
- **Word Frequency Analysis**: Count and analyze common words across all jobs
- **Job Clustering**: Auto-categorize jobs using sentence embeddings and machine learning

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
| `USER_DATA_DIR` | Path to Chrome profile | Yes |
| `CLUSTER_COUNT` | Number of clusters for job categorization (default: 8) | No |

**To get Chrome profile path on macOS:**
```bash
ls ~/Library/Application\ Support/Google/Chrome/
```
Use a path like:
```
/Users/yourname/Library/Application Support/Google/Chrome/Default
```

## Usage

### Scrape Jobs
```bash
python main.py
```
- Opens Chrome with your existing profile
- Logs in via Google SSO if not already logged in
- Searches for "python" jobs
- Navigates through pages automatically
- Stores jobs in `jobs.db`

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
python cluster.py              # Default 8 clusters
python cluster.py 12           # Custom cluster count
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
├── main.py           # Job scraping script
├── database.py       # SQLite database operations
├── count.py          # Word frequency analysis
├── cluster.py        # Job clustering with ML
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (credentials)
├── .env.example      # Example environment file
├── jobs.db           # SQLite database (created on first run)
└── README.md         # This file
```

## Stealth Features

The browser launches with these arguments to avoid detection:
- `--disable-blink-features=AutomationControlled` - Hides automation flags
- `--disable-infobars` - Removes automation warning banner
- `--disable-dev-shm-usage` - Better stability
- Uses persistent Chrome context with existing user profile

## Notes

- Currently only supports Gmail/Google SSO login
- Browser runs in non-headless mode using your Chrome profile
- Default search query is "python" (hardcoded in main.py)
- The scraper clicks each job tile to get the full URL (Upwork loads details dynamically)
- Press `Escape` to close job details popup after each scrape
- Default scrapes 10 jobs per page. Modify `max_jobs` in `scrape_jobs()` to change this

## Performance

for 10 pages it takes ~6 minutes

python main.py  128,95s user 51,27s system 50% cpu 5:53,85 total