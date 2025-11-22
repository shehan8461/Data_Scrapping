import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# List of URLs to scrape
urls = [
    "https://ikman.lk/en/ads/sri-lanka/room-annex-rentals"
]

data = []

# Set up Selenium WebDriver with headless option
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

for base_url in urls:
    driver.get(base_url)
    time.sleep(5)
    category = base_url.split('/')[-1]
    page = 1
    total_pages = 100  # Set high limit to ensure we get all pages
    
    while page <= total_pages:
        print(f"Scraping page {page} of {category}")
        
        # Navigate to the current page
        if page > 1:
            current_url = f"{base_url}?page={page}"
            driver.get(current_url)
            time.sleep(3)
        
        # Try to find items
        collections = []
        product_divs = driver.find_elements(By.CSS_SELECTOR, "li[class*='normal']")
        if product_divs:
            collections = product_divs
        else:
            # Try alternative selector
            col_divs = driver.find_elements(By.CSS_SELECTOR, "a[href*='/ad/']")
            if col_divs:
                collections = col_divs
            else:
                # Try another alternative
                ban_divs = driver.find_elements(By.XPATH, "//ul[@class='list--3NxGO']/li")
                collections = ban_divs
        
        if not collections:
            print(f"No products found on page {page}, stopping.")
            break
        
        for col in collections:
            name = "N/A"
            price = "N/A"
            image_url = "N/A"
            try:
                # Extract name - try multiple selectors
                try:
                    name_elem = col.find_element(By.TAG_NAME, "h2")
                    name = name_elem.text.strip()
                except:
                    try:
                        name_elem = col.find_element(By.CSS_SELECTOR, "[class*='title']")
                        name = name_elem.text.strip()
                    except:
                        pass
                
                # Extract price - try multiple selectors
                try:
                    price_elem = col.find_element(By.XPATH, ".//div[contains(@class, 'price')]")
                    price = price_elem.text.strip()
                except:
                    try:
                        price_elem = col.find_element(By.CSS_SELECTOR, "[class*='price']")
                        price = price_elem.text.strip()
                    except:
                        pass
                
                # Extract image URL
                try:
                    img_elem = col.find_element(By.TAG_NAME, "img")
                    image_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                except:
                    pass
            except Exception as e:
                continue
            
            # Only add if we got at least a name
            if name != "N/A":
                data.append({
                    'Category': category,
                    'Name': name,
                    'Price': price,
                    'Image_URL': image_url
                })
        
        print(f"Collected {len(data)} items so far...")
        
        # Move to next page
        page += 1

driver.quit()

# Save to CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv('room_annex_rentals.csv', index=False)
    print(f"Scraped {len(data)} items and saved to room_annex_rentals.csv")
else:
    print("No data scraped.")
