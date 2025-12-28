# CIS People Web Scraper

A web scraper to extract names, titles, categories, and profile URLs from the University of Melbourne's School of Computing and Information Systems people page.

## Features

- Extracts names, titles, categories, and profile URLs
- Separates honorifics (Prof, Dr, etc.) from names
- Handles Cloudflare protection using Selenium
- Saves data to both JSON and CSV formats
- Automatically manages ChromeDriver

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome browser installed (required for Selenium)

## Usage

Run the scraper:
```bash
python scraper.py
```

The scraper will:
- Fetch the page from https://cis.unimelb.edu.au/people
- Extract all people data
- Save results to `people_data.json` and `people_data.csv`
- Display a preview of the first 3 entries

## Output

The scraper generates two output files:

### JSON Format (`people_data.json`)
```json
[
  {
    "name": "Uwe Aickelin",
    "honorific": "Prof",
    "title": "Head of School",
    "category": "Leadership",
    "profile_url": "https://findanexpert.unimelb.edu.au/profile/815636"
  },
  ...
]
```

### CSV Format (`people_data.csv`)
The CSV file contains the same data with columns: `name`, `honorific`, `title`, `category`, `profile_url`

## Visualization

After scraping, you can visualize the data using the Streamlit app:

```bash
streamlit run app.py
```

The app provides:
- Interactive filters by category and honorific
- Search functionality
- Statistics and charts
- Clickable profile links
- Download filtered data as CSV

## Notes

- The scraper uses Selenium with headless Chrome to bypass Cloudflare protection
- Categories are determined from section headers on the page (e.g., "Leadership", "Program coordinators")
- Some entries may not have profile URLs if they're not linked on the page
- The scraper automatically scrapes all category subpages (Academic staff, Professional staff, etc.)

