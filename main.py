import requests
from bs4 import BeautifulSoup
import pandas as pd

current_page = 1
data = []
proceed = True

while proceed:
    print("Scraping Page " + str(current_page))
    url = "https://ikman.lk/en/ads/sri-lanka/property?sort=relevance&buy_now=0&urgent=0&query=boarding&page=" + str(current_page)
    
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        # Check if page exists by looking for ads
        all_ads = soup.find_all('li', class_="normal--2QYVk gtm-normal-ad")
        
        if not all_ads:  # No ads found, probably reached the end
            proceed = False
            print("No more ads found. Scraping complete.")
        else:
            for ads in all_ads:
                item = {}
                
                # Get title from img alt attribute
                img_tag = ads.find("img")
                if img_tag and 'alt' in img_tag.attrs:
                    item['Title'] = img_tag.attrs['alt']
                else:
                    # Fallback: try to get title from h2 heading
                    title_tag = ads.find("h2", class_="heading--2eONR")
                    if title_tag:
                        item['Title'] = title_tag.text.strip()
                    else:
                        item['Title'] = "N/A"
                
                # Get price from div with correct classes
                price_tag = ads.find("div", class_="price--3SnqI color--t0tGX")
                if price_tag:
                    # Get the span inside the price div
                    price_span = price_tag.find("span")
                    if price_span:
                        item['Price'] = price_span.text.strip()
                    else:
                        item['Price'] = price_tag.text.strip()
                else:
                    item['Price'] = "N/A"
                
                # Get description from div (not p tag)
                desc_tag = ads.find("div", class_="description--2-ez3")
                if desc_tag:
                    item['Description'] = desc_tag.text.strip()
                else:
                    item['Description'] = "N/A"
                
                # Get additional details if available
                details_tag = ads.find("div", class_="details--1GUIn")
                if details_tag:
                    item['Details'] = details_tag.text.strip()
                else:
                    item['Details'] = "N/A"
                
                data.append(item)
            
            # Increment page AFTER processing all ads on current page
            current_page += 1
            
            # Add a reasonable limit to prevent infinite scraping
            if current_page > 50:  # Adjust this limit as needed
                proceed = False
                print("Reached page limit. Stopping.")
                
    except Exception as e:
        print(f"Error scraping page {current_page}: {e}")
        proceed = False

# Save data to CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv('boarding_houses.csv', index=False)
    print(f"Scraped {len(data)} listings and saved to boarding_houses.csv")


