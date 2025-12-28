"""
Web scraper for extracting people information from CIS website.
Extracts: names, titles, categories, and profile URLs.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
from typing import List, Dict
import time

# Try to import selenium, fallback to requests if not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False


def fetch_page_requests(url: str) -> BeautifulSoup:
    """Fetch and parse HTML page using requests."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'lxml')


def fetch_page_selenium(url: str) -> BeautifulSoup:
    """Fetch and parse HTML page using Selenium (handles JavaScript)."""
    if not SELENIUM_AVAILABLE:
        raise ImportError("Selenium not installed. Install with: pip install selenium")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use webdriver-manager if available, otherwise try default ChromeDriver
    if WEBDRIVER_MANAGER_AVAILABLE:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        # Wait for page to load and Cloudflare challenge to complete
        time.sleep(5)
        html = driver.page_source
        return BeautifulSoup(html, 'lxml')
    finally:
        driver.quit()


def fetch_page(url: str, use_selenium: bool = False) -> BeautifulSoup:
    """Fetch and parse HTML page. Tries requests first, falls back to Selenium if needed."""
    if use_selenium:
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not installed. Install with: pip install selenium")
        return fetch_page_selenium(url)
    else:
        try:
            return fetch_page_requests(url)
        except Exception as e:
            if SELENIUM_AVAILABLE:
                print(f"Requests failed ({e}), trying Selenium...")
                return fetch_page_selenium(url)
            raise


def parse_name_and_honorific(full_name: str) -> tuple[str, str]:
    """Separate honorific from name. Returns (name, honorific)."""
    # Common honorifics
    honorifics = ['Prof', 'A/Prof', 'Assoc Prof', 'Dr', 'Mr', 'Mrs', 'Ms', 'Miss']
    
    full_name = full_name.strip()
    for honorific in honorifics:
        if full_name.startswith(honorific + ' '):
            name = full_name[len(honorific):].strip()
            return name, honorific
    
    # No honorific found
    return full_name, ''


def extract_people_data(soup: BeautifulSoup, default_category: str = None) -> List[Dict]:
    """Extract people data from parsed HTML."""
    people = []
    
    # Find all person cards
    cards = soup.find_all('div', class_='card')
    
    # Track current category from section headers
    current_category = default_category or 'General'
    
    for card in cards:
        # Check if there's a section header before this card
        prev_section = card.find_previous('h2', id=True)
        if prev_section:
            section_id = prev_section.get('id', '')
            section_text = prev_section.get_text(strip=True)
            if section_text and section_text not in ['Featured content', 'Site footer']:
                current_category = section_text
        
        person_data = {}
        
        # Extract name from h3.card__header > a
        header = card.find('h3', class_='card__header')
        if header:
            name_link = header.find('a')
            if name_link:
                # Clean up name (remove extra whitespace and newlines)
                full_name = ' '.join(name_link.get_text().split())
                name, honorific = parse_name_and_honorific(full_name)
                person_data['name'] = name
                person_data['honorific'] = honorific
                
                # Extract profile URL
                href = name_link.get('href', '')
                if href.startswith('http'):
                    person_data['profile_url'] = href
                elif href.startswith('/'):
                    person_data['profile_url'] = 'https://cis.unimelb.edu.au' + href
                else:
                    person_data['profile_url'] = 'https://cis.unimelb.edu.au/' + href
            else:
                full_name = header.get_text(strip=True)
                name, honorific = parse_name_and_honorific(full_name)
                person_data['name'] = name
                person_data['honorific'] = honorific
                person_data['profile_url'] = 'N/A'
        else:
            continue  # Skip if no header found
        
        # Extract title from div.card__sub-heading
        sub_heading = card.find('div', class_='card__sub-heading')
        if sub_heading:
            person_data['title'] = sub_heading.get_text(strip=True)
        else:
            person_data['title'] = 'N/A'
        
        # Use current category (or default if provided)
        person_data['category'] = current_category
        
        people.append(person_data)
    
    return people


def find_category_links(soup: BeautifulSoup, base_url: str) -> List[tuple[str, str]]:
    """Find category links from pathfinder sections. Returns list of (category_name, url)."""
    category_links = []
    
    # Find pathfinder sections (the category boxes)
    pathfinders = soup.find_all('ul', class_='pathfinder-3')
    
    for pathfinder in pathfinders:
        links = pathfinder.find_all('a', href=True)
        for link in links:
            # Get the category name from the h3 inside the link
            h3 = link.find('h3')
            if h3:
                category_name = h3.get_text(strip=True)
                href = link.get('href', '')
                
                # Make absolute URL if relative
                if href.startswith('/'):
                    full_url = base_url.rstrip('/') + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = base_url.rstrip('/') + '/' + href
                
                category_links.append((category_name, full_url))
    
    return category_links


def save_to_json(data: List[Dict], filename: str = 'people_data.json'):
    """Save extracted data to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")


def save_to_csv(data: List[Dict], filename: str = 'people_data.csv'):
    """Save extracted data to CSV file."""
    if not data:
        return
    
    # Define column order
    fieldnames = ['name', 'honorific', 'title', 'category', 'profile_url']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")


def main(use_selenium: bool = True, save_html: bool = False, scrape_subpages: bool = True):
    """Main function to run the scraper."""
    base_url = 'https://cis.unimelb.edu.au/people'
    all_people = []
    
    print(f"Fetching main page: {base_url}...")
    try:
        if use_selenium and not SELENIUM_AVAILABLE:
            print("Selenium not available, falling back to requests...")
            use_selenium = False
        soup = fetch_page(base_url, use_selenium=use_selenium)
        
        # Optionally save HTML for inspection
        if save_html:
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print("HTML saved to page_source.html for inspection")
            
    except Exception as e:
        print(f"Error fetching page: {e}")
        if not use_selenium and SELENIUM_AVAILABLE:
            print("Retrying with Selenium...")
            soup = fetch_page(base_url, use_selenium=True)
        else:
            raise
    
    # Extract people from main page
    print("Extracting people from main page...")
    main_people = extract_people_data(soup)
    all_people.extend(main_people)
    print(f"Found {len(main_people)} people on main page")
    
    # Find and scrape category subpages
    if scrape_subpages:
        print("\nFinding category links...")
        category_links = find_category_links(soup, 'https://cis.unimelb.edu.au')
        print(f"Found {len(category_links)} category pages to scrape")
        
        for category_name, category_url in category_links:
            print(f"\nScraping: {category_name} ({category_url})...")
            try:
                category_soup = fetch_page(category_url, use_selenium=use_selenium)
                category_people = extract_people_data(category_soup, default_category=category_name)
                all_people.extend(category_people)
                print(f"  Found {len(category_people)} people")
                time.sleep(1)  # Be polite, add small delay between requests
            except Exception as e:
                print(f"  Error scraping {category_name}: {e}")
                continue
    
    print(f"\nTotal people found: {len(all_people)}")
    
    if all_people:
        # Display first few entries
        print("\nSample entries:")
        for i, person in enumerate(all_people[:3], 1):
            honorific_str = f"{person.get('honorific', '')} " if person.get('honorific') else ''
            print(f"\n{i}. {honorific_str}{person['name']}")
            print(f"   Title: {person['title']}")
            print(f"   Category: {person['category']}")
            print(f"   URL: {person['profile_url']}")
        
        # Save to JSON and CSV
        save_to_json(all_people)
        save_to_csv(all_people)
    else:
        print("No people found. The HTML structure might be different.")
        print("Consider running with save_html=True to inspect the page structure.")
    
    return all_people


if __name__ == '__main__':
    main()

