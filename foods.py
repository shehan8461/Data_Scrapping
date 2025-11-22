import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

# Base URL for food composition database
base_url = "https://www.foodcompositiondb.lk/foods?name=food"

data = []
page = 1
max_pages = 17  # As mentioned, there are 17 pages

# Set up Selenium WebDriver with headless option
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get(base_url)
    print("Page loaded, waiting for content...")
    time.sleep(5)
    
    # Wait for initial table load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )
    print("Table element found")
    
    # Wait specifically for table rows with data to appear
    print("Waiting for data rows to load...")
    WebDriverWait(driver, 30).until(
        lambda d: len(d.find_elements(By.XPATH, "//table//tr[td]")) > 0
    )
    print("Data rows detected!")
    time.sleep(5)
    
    while page <= max_pages:
        print(f"\n{'='*60}")
        print(f"Scraping page {page} of {max_pages}")
        print(f"{'='*60}")
        
        # Wait for table rows to load after pagination
        if page > 1:
            print("Waiting for page data to load...")
            try:
                WebDriverWait(driver, 30).until(
                    lambda d: len(d.find_elements(By.XPATH, "//table//tr[td]")) > 0
                )
                print("Page data loaded!")
            except:
                print("Timeout waiting for data, trying anyway...")
        
        time.sleep(5)
        
        # Scroll to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Try to find the table with food data
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            if not tables:
                print("No tables found on page")
                break
            
            table = tables[0]
            
            # Get headers (only on first page)
            if page == 1:
                headers = []
                try:
                    header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
                    header_cells = header_row.find_elements(By.TAG_NAME, "th")
                    headers = [cell.text.strip() for cell in header_cells if cell.text.strip()]
                    print(f"Headers: {headers}")
                except:
                    all_rows = table.find_elements(By.TAG_NAME, "tr")
                    if all_rows:
                        header_cells = all_rows[0].find_elements(By.TAG_NAME, "th")
                        if not header_cells:
                            header_cells = all_rows[0].find_elements(By.TAG_NAME, "td")
                        headers = [cell.text.strip() for cell in header_cells if cell.text.strip()]
                        print(f"Headers: {headers}")
            
            # Get data rows
            data_rows = []
            try:
                tbody = table.find_element(By.TAG_NAME, "tbody")
                data_rows = tbody.find_elements(By.TAG_NAME, "tr")
                print(f"Found {len(data_rows)} rows in tbody")
            except:
                # Try getting all tr elements with td children (data rows)
                data_rows = table.find_elements(By.XPATH, ".//tr[td]")
                print(f"Found {len(data_rows)} rows with td elements")
                
                if not data_rows:
                    # Fallback to all rows except first
                    all_rows = table.find_elements(By.TAG_NAME, "tr")
                    data_rows = all_rows[1:] if len(all_rows) > 1 else []
                    print(f"Fallback: Found {len(data_rows)} rows (all rows - header)")
            
            print(f"Processing {len(data_rows)} data rows on this page")
            
            # Process each row
            row_count = 0
            for idx, row in enumerate(data_rows):
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if not cells:
                    cells = row.find_elements(By.TAG_NAME, "th")
                
                if cells and len(cells) > 0:
                    cell_values = [cell.text.strip() for cell in cells]
                    
                    # Skip if it's just the header row again
                    if cell_values == headers:
                        continue
                    
                    # Skip empty rows
                    if not any(cell_values):
                        continue
                    
                    item = {}
                    for i, cell_value in enumerate(cell_values):
                        if i < len(headers) and headers[i]:
                            item[headers[i]] = cell_value
                        else:
                            item[f'Column_{i}'] = cell_value
                    
                    if item and any(item.values()):
                        data.append(item)
                        row_count += 1
                        # Print first and last few items for verification
                        if row_count <= 2 or row_count == len(data_rows):
                            print(f"  Row {row_count}: {item}")
            
            print(f"Scraped {row_count} items from page {page}")
            print(f"Total items collected so far: {len(data)}")
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
        
        # Move to next page
        if page < max_pages:
            try:
                # Look for next button or page number
                # Try multiple pagination selectors
                next_clicked = False
                
                # Method 1: Try clicking "Next" button
                try:
                    next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Next') or contains(text(), 'next') or contains(text(), '›') or contains(text(), '»')]")
                    for btn in next_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            driver.execute_script("arguments[0].scrollIntoView();", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            print("Clicked 'Next' button")
                            next_clicked = True
                            break
                except Exception as e:
                    print(f"Next button not found: {e}")
                
                # Method 2: Try clicking specific page number
                if not next_clicked:
                    try:
                        page_links = driver.find_elements(By.XPATH, f"//a[contains(text(), '{page + 1}')]")
                        for link in page_links:
                            if link.is_displayed() and link.is_enabled():
                                driver.execute_script("arguments[0].scrollIntoView();", link)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", link)
                                print(f"Clicked page {page + 1} link")
                                next_clicked = True
                                break
                    except Exception as e:
                        print(f"Page number link not found: {e}")
                
                # Method 3: Try pagination buttons/li elements
                if not next_clicked:
                    try:
                        pagination_items = driver.find_elements(By.CSS_SELECTOR, ".pagination li a, .pager a, nav a")
                        for item in pagination_items:
                            if item.text.strip() == str(page + 1):
                                driver.execute_script("arguments[0].scrollIntoView();", item)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", item)
                                print(f"Clicked pagination item for page {page + 1}")
                                next_clicked = True
                                break
                    except Exception as e:
                        print(f"Pagination items not found: {e}")
                
                if not next_clicked:
                    print(f"Could not navigate to page {page + 1}, stopping.")
                    break
                
                time.sleep(5)  # Wait for new page to load
                page += 1
                
            except Exception as e:
                print(f"Error navigating to next page: {e}")
                break
        else:
            break

except Exception as e:
    print(f"Error during scraping: {e}")

finally:
    driver.quit()

# Save to CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv('foods.csv', index=False)
    print(f"\n{'='*60}")
    print(f"Successfully scraped {len(data)} items and saved to foods.csv")
    print(f"{'='*60}")
else:
    print("No data scraped.")
