import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re

class CBSLEconomicScraper:
    def __init__(self):
        self.base_url = "https://www.cbsl.gov.lk"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.data = {
            'exchange_rates': [],
            'inflation_data': [],
            'interest_rates': [],
            'economic_indicators': []
        }
    
    def get_exchange_rates(self):
        """Scrape current exchange rates for major currencies"""
        print("Scraping Exchange Rates...")
        
        try:
            # Get USD/LKR rate
            usd_url = f"{self.base_url}/rates-and-indicators/exchange-rates/daily-indicative-usd-spot-exchange-rates"
            response = self.session.get(usd_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find exchange rate data in tables or specific elements
            tables = soup.find_all('table')
            
            currencies = ['USD', 'GBP', 'EUR', 'INR', 'JPY', 'AUD', 'CAD', 'CHF']
            
            for currency in currencies:
                try:
                    # Try different URL patterns for each currency
                    if currency == 'USD':
                        rate_url = f"{self.base_url}/rates-and-indicators/exchange-rates/daily-indicative-usd-spot-exchange-rates"
                    else:
                        rate_url = f"{self.base_url}/rates-and-indicators/exchange-rates/daily-indicative-exchange-rates"
                    
                    response = self.session.get(rate_url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for rate information in various possible locations
                    rate_value = self.extract_rate_from_page(soup, currency)
                    
                    if rate_value:
                        self.data['exchange_rates'].append({
                            'Currency': currency,
                            'Rate_LKR': rate_value,
                            'Date': datetime.now().strftime('%Y-%m-%d'),
                            'Time': datetime.now().strftime('%H:%M:%S'),
                            'Source': 'CBSL'
                        })
                        print(f"Found {currency}: {rate_value} LKR")
                    else:
                        # Fallback - add placeholder data
                        self.data['exchange_rates'].append({
                            'Currency': currency,
                            'Rate_LKR': 'N/A',
                            'Date': datetime.now().strftime('%Y-%m-%d'),
                            'Time': datetime.now().strftime('%H:%M:%S'),
                            'Source': 'CBSL'
                        })
                        print(f"{currency} rate not found")
                    
                    time.sleep(1)  # Be respectful to the server
                    
                except Exception as e:
                    print(f"Error scraping {currency}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping exchange rates: {e}")
    
    def extract_rate_from_page(self, soup, currency):
        """Extract exchange rate from the page content"""
        try:
            # Look for tables containing rate data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if currency in text:
                            # Look for number in nearby cells
                            for sibling in cells:
                                sibling_text = sibling.get_text(strip=True)
                                # Look for decimal numbers
                                rate_match = re.search(r'\d+\.\d+', sibling_text)
                                if rate_match:
                                    return rate_match.group()
            
            # Alternative: Look for specific rate patterns in text
            text_content = soup.get_text()
            pattern = rf'{currency}[:\s]*(\d+\.\d+)'
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1)
                
            return None
            
        except Exception as e:
            print(f"Error extracting rate for {currency}: {e}")
            return None
    
    def get_inflation_data(self):
        """Scrape inflation rates and consumer price index data"""
        print("Scraping Inflation Data...")
        
        try:
            inflation_url = f"{self.base_url}/measures-of-consumer-price-inflation"
            response = self.session.get(inflation_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for inflation data in tables or specific elements
            tables = soup.find_all('table')
            
            # Try to extract CCPI and NCPI data
            inflation_types = ['CCPI', 'NCPI', 'Core CCPI']
            
            for inflation_type in inflation_types:
                try:
                    # Extract inflation rate from page content
                    inflation_rate = self.extract_inflation_rate(soup, inflation_type)
                    
                    self.data['inflation_data'].append({
                        'Inflation_Type': inflation_type,
                        'Rate_Percent': inflation_rate if inflation_rate else 'N/A',
                        'Date': datetime.now().strftime('%Y-%m-%d'),
                        'Period': 'Latest Available',
                        'Source': 'CBSL'
                    })
                    
                    print(f"Found {inflation_type}: {inflation_rate}%")
                    
                except Exception as e:
                    print(f"Error scraping {inflation_type}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping inflation data: {e}")
    
    def extract_inflation_rate(self, soup, inflation_type):
        """Extract inflation rate from page content"""
        try:
            text_content = soup.get_text()
            
            # Look for patterns like "CCPI: 1.5%" or "inflation 1.5%"
            patterns = [
                rf'{inflation_type}[:\s]*(\d+\.\d+)%',
                rf'{inflation_type}[:\s]*(\d+\.\d+)',
                rf'inflation[:\s]*(\d+\.\d+)%'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Look in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if inflation_type.lower() in cell.get_text().lower():
                            # Look for rate in next cells
                            if i + 1 < len(cells):
                                rate_text = cells[i + 1].get_text(strip=True)
                                rate_match = re.search(r'(\d+\.\d+)', rate_text)
                                if rate_match:
                                    return rate_match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error extracting inflation rate for {inflation_type}: {e}")
            return None
    
    def get_interest_rates(self):
        """Scrape policy interest rates and other monetary policy data"""
        print("Scraping Interest Rates...")
        
        try:
            interest_url = f"{self.base_url}/rates-and-indicators/policy-rates"
            response = self.session.get(interest_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            rate_types = [
                'Standing Deposit Facility Rate',
                'Standing Lending Facility Rate', 
                'Bank Rate',
                'Repo Rate',
                'Reverse Repo Rate'
            ]
            
            for rate_type in rate_types:
                try:
                    rate_value = self.extract_interest_rate(soup, rate_type)
                    
                    self.data['interest_rates'].append({
                        'Rate_Type': rate_type,
                        'Rate_Percent': rate_value if rate_value else 'N/A',
                        'Date': datetime.now().strftime('%Y-%m-%d'),
                        'Effective_Date': 'Latest Available',
                        'Source': 'CBSL'
                    })
                    
                    print(f"Found {rate_type}: {rate_value}%")
                    
                except Exception as e:
                    print(f"Error scraping {rate_type}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping interest rates: {e}")
    
    def extract_interest_rate(self, soup, rate_type):
        """Extract interest rate from page content"""
        try:
            # Look in tables first
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        if any(word in cell_text.lower() for word in rate_type.lower().split()):
                            # Look for rate in nearby cells
                            for j in range(max(0, i-1), min(len(cells), i+3)):
                                if j != i:
                                    rate_text = cells[j].get_text(strip=True)
                                    rate_match = re.search(r'(\d+\.\d+)', rate_text)
                                    if rate_match:
                                        return rate_match.group(1)
            
            # Look in general text
            text_content = soup.get_text()
            pattern = rf'{rate_type}[:\s]*(\d+\.\d+)%?'
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1)
                
            return None
            
        except Exception as e:
            print(f"Error extracting interest rate for {rate_type}: {e}")
            return None
    
    def get_economic_indicators(self):
        """Scrape general economic statistics and indicators"""
        print("Scraping Economic Indicators...")
        
        try:
            indicators_url = f"{self.base_url}/statistics/economic-indicators/daily-indicators"
            response = self.session.get(indicators_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for various economic indicators
            indicators = [
                'GDP Growth Rate',
                'Unemployment Rate',
                'Foreign Reserves',
                'Government Debt',
                'Current Account Balance',
                'Trade Deficit'
            ]
            
            for indicator in indicators:
                try:
                    value = self.extract_economic_indicator(soup, indicator)
                    
                    self.data['economic_indicators'].append({
                        'Indicator': indicator,
                        'Value': value if value else 'N/A',
                        'Unit': self.get_indicator_unit(indicator),
                        'Date': datetime.now().strftime('%Y-%m-%d'),
                        'Period': 'Latest Available',
                        'Source': 'CBSL'
                    })
                    
                    print(f"Found {indicator}: {value}")
                    
                except Exception as e:
                    print(f"Error scraping {indicator}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping economic indicators: {e}")
    
    def extract_economic_indicator(self, soup, indicator):
        """Extract economic indicator value from page content"""
        try:
            # This is a simplified extraction - in practice, you'd need
            # to analyze the specific page structure for each indicator
            text_content = soup.get_text()
            
            # Look for the indicator followed by a number
            pattern = rf'{indicator}[:\s]*(\d+\.\d+|\d+)'
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1)
                
            return None
            
        except Exception as e:
            print(f"Error extracting {indicator}: {e}")
            return None
    
    def get_indicator_unit(self, indicator):
        """Return appropriate unit for each indicator"""
        unit_map = {
            'GDP Growth Rate': '%',
            'Unemployment Rate': '%',
            'Foreign Reserves': 'USD Million',
            'Government Debt': 'LKR Billion',
            'Current Account Balance': 'USD Million',
            'Trade Deficit': 'USD Million'
        }
        return unit_map.get(indicator, '')
    
    def scrape_all_data(self):
        """Scrape all types of economic data"""
        print("Starting CBSL Economic Data Scraping...")
        print("=" * 50)
        
        # Scrape all data types
        self.get_exchange_rates()
        print("-" * 30)
        
        self.get_inflation_data()
        print("-" * 30)
        
        self.get_interest_rates()
        print("-" * 30)
        
        self.get_economic_indicators()
        print("-" * 30)
        
        print("Scraping completed!")
    
    def save_to_csv(self):
        """Save all scraped data to CSV files"""
        print("Saving data to CSV files...")
        
        try:
            # Save exchange rates
            if self.data['exchange_rates']:
                df_exchange = pd.DataFrame(self.data['exchange_rates'])
                df_exchange.to_csv('cbsl_exchange_rates.csv', index=False)
                print(f"Saved {len(self.data['exchange_rates'])} exchange rates to cbsl_exchange_rates.csv")
            
            # Save inflation data
            if self.data['inflation_data']:
                df_inflation = pd.DataFrame(self.data['inflation_data'])
                df_inflation.to_csv('cbsl_inflation_data.csv', index=False)
                print(f"Saved {len(self.data['inflation_data'])} inflation records to cbsl_inflation_data.csv")
            
            # Save interest rates
            if self.data['interest_rates']:
                df_interest = pd.DataFrame(self.data['interest_rates'])
                df_interest.to_csv('cbsl_interest_rates.csv', index=False)
                print(f"Saved {len(self.data['interest_rates'])} interest rates to cbsl_interest_rates.csv")
            
            # Save economic indicators
            if self.data['economic_indicators']:
                df_indicators = pd.DataFrame(self.data['economic_indicators'])
                df_indicators.to_csv('cbsl_economic_indicators.csv', index=False)
                print(f"Saved {len(self.data['economic_indicators'])} indicators to cbsl_economic_indicators.csv")
            
            # Create a combined summary file
            self.create_summary_report()
            
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def create_summary_report(self):
        """Create a comprehensive summary report"""
        try:
            summary_data = []
            
            # Add exchange rates summary
            for rate in self.data['exchange_rates']:
                summary_data.append({
                    'Category': 'Exchange Rate',
                    'Item': f"{rate['Currency']}/LKR",
                    'Value': rate['Rate_LKR'],
                    'Unit': 'LKR',
                    'Date': rate['Date'],
                    'Source': rate['Source']
                })
            
            # Add inflation data summary
            for inflation in self.data['inflation_data']:
                summary_data.append({
                    'Category': 'Inflation',
                    'Item': inflation['Inflation_Type'],
                    'Value': inflation['Rate_Percent'],
                    'Unit': '%',
                    'Date': inflation['Date'],
                    'Source': inflation['Source']
                })
            
            # Add interest rates summary
            for rate in self.data['interest_rates']:
                summary_data.append({
                    'Category': 'Interest Rate',
                    'Item': rate['Rate_Type'],
                    'Value': rate['Rate_Percent'],
                    'Unit': '%',
                    'Date': rate['Date'],
                    'Source': rate['Source']
                })
            
            # Add economic indicators summary
            for indicator in self.data['economic_indicators']:
                summary_data.append({
                    'Category': 'Economic Indicator',
                    'Item': indicator['Indicator'],
                    'Value': indicator['Value'],
                    'Unit': indicator['Unit'],
                    'Date': indicator['Date'],
                    'Source': indicator['Source']
                })
            
            if summary_data:
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_csv('cbsl_economic_summary.csv', index=False)
                print(f"Created comprehensive summary with {len(summary_data)} total records in cbsl_economic_summary.csv")
                
        except Exception as e:
            print(f"Error creating summary report: {e}")
    
    def display_summary(self):
        """Display a summary of scraped data"""
        print("\n" + "=" * 60)
        print("CBSL ECONOMIC DATA SCRAPING SUMMARY")
        print("=" * 60)
        
        print(f"Exchange Rates: {len(self.data['exchange_rates'])} currencies")
        print(f"Inflation Data: {len(self.data['inflation_data'])} indicators")
        print(f"Interest Rates: {len(self.data['interest_rates'])} rates")
        print(f"Economic Indicators: {len(self.data['economic_indicators'])} metrics")
        
        total_records = sum(len(v) for v in self.data.values())
        print(f"\nTotal Records Scraped: {total_records}")
        print(f"Scraping Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

def main():
    """Main function to run the scraper"""
    scraper = CBSLEconomicScraper()
    
    try:
        # Scrape all data
        scraper.scrape_all_data()
        
        # Save to CSV files
        scraper.save_to_csv()
        
        # Display summary
        scraper.display_summary()
        
    except Exception as e:
        print(f"Error in main execution: {e}")
    
    print("\nScraping process completed!")

if __name__ == "__main__":
    main()