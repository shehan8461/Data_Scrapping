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
    "https://cargillsonline.com/Product/Food-Cupboard?IC=Nw==&NC=Rm9vZCBDdXBib2FyZA=="
]

data = []

# Set up Selenium WebDriver with headless option
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

for base_url in urls:
    driver.get(base_url)
    time.sleep(5)
    category = base_url.split('Product/')[1].split('?')[0]
    page = 1
    total_pages = 1  # Will be updated after first page
    
    while page <= total_pages:
        print(f"Scraping page {page} of {category}")
        
        # Try to find items
        collections = []
        product_divs = driver.find_elements(By.XPATH, "//div[@ng-repeat='product in Products']")
        if product_divs:
            collections = product_divs
        else:
            # Try collection
            col_divs = driver.find_elements(By.XPATH, "//div[@ng-repeat='collection in DS.Data']")
            if col_divs:
                collections = col_divs
            else:
                # Try ban
                ban_divs = driver.find_elements(By.XPATH, "//div[@ng-repeat='ban in DS.Data']")
                collections = ban_divs
        
        if not collections:
            print(f"No products found on page {page}, stopping.")
            break
        
        for col in collections:
            name = "N/A"
            price = "N/A"
            image_url = "N/A"
            try:
                # Extract name
                name_elem = col.find_element(By.XPATH, ".//p")
                name = name_elem.text.strip()
                
                # Extract price
                price_elem = col.find_element(By.XPATH, ".//h4[contains(@class, 'txtSmall')]")
                price = price_elem.text.strip()
                
                # Extract image URL
                img_elem = col.find_element(By.XPATH, ".//img")
                image_url = img_elem.get_attribute('ng-src') or img_elem.get_attribute('src')
            except Exception as e:
                print(f"Error extracting data: {e}")
                continue
            
            data.append({
                'Category': category,
                'Name': name,
                'Price': price,
                'Image_URL': image_url
            })
        
        # On first page, find total pages
        if page == 1:
            total_pages = 1
            try:
                # Look for numbered links
                number_links = driver.find_elements(By.XPATH, "//a[string(number(text())) = text()]")
                for link in number_links:
                    try:
                        num = int(link.text.strip())
                        if num > total_pages:
                            total_pages = num
                    except:
                        continue
                print(f"Total pages detected: {total_pages}")
            except Exception as e:
                print(f"Error finding total pages: {e}")
        
        # If not the last page, try to go to next page
        if page < total_pages:
            try:
                # Wait for next button to be clickable
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[string(number(text())) = text() and text()='" + str(page + 1) + "']")))
                next_button = driver.find_element(By.XPATH, "//a[string(number(text())) = text() and text()='" + str(page + 1) + "']")
                
                # Scroll to the element
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(1)
                
                # Try JavaScript click
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)
                page += 1
            except Exception as e:
                print(f"Error clicking next page {page + 1}: {e}")
                break
        else:
            break

driver.quit()

# Save to CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv('food.csv', index=False)
    print(f"Scraped {len(data)} items and saved to food.csv")
else:
    print("No data scraped.")
