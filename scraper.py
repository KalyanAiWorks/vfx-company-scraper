import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

class VFXCompanyScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.sarvam.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def scrape_website(self, url):
        """Scrape website content"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def parse_html(self, html_content, base_url):
        """Parse HTML and extract text content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n')
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_contact_info_with_ai(self, text_content, company_name):
        """Use Sarvam AI to extract contact information"""
        prompt = f"""Extract contact information from the following text about {company_name}.
Find and list:
- Email addresses
- Phone numbers
- Physical addresses
- Contact page URLs
- Social media links

Text:
{text_content[:4000]}

Provide the extracted information in JSON format with keys: emails, phones, addresses, contact_urls, social_media."""
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "sarvam-2b-v0.5",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that extracts contact information from text."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Try to parse JSON from response
            try:
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_response, re.DOTALL)
                if json_match:
                    contact_info = json.loads(json_match.group())
                else:
                    contact_info = self._manual_extract(text_content)
            except:
                contact_info = self._manual_extract(text_content)
            
            return contact_info
            
        except Exception as e:
            print(f"AI extraction error: {str(e)}")
            return self._manual_extract(text_content)
    
    def _manual_extract(self, text):
        """Fallback manual extraction using regex"""
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = list(set(re.findall(email_pattern, text)))
        
        # Phone pattern (various formats)
        phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        phones = list(set(re.findall(phone_pattern, text)))
        phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 10]
        
        return {
            "emails": emails[:5],
            "phones": phones[:5],
            "addresses": [],
            "contact_urls": [],
            "social_media": []
        }
    
    def scrape_company(self, company_name, website_url):
        """Scrape a single VFX company"""
        print(f"\nScraping {company_name} - {website_url}")
        
        html_content = self.scrape_website(website_url)
        if not html_content:
            return None
        
        text_content = self.parse_html(html_content, website_url)
        contact_info = self.extract_contact_info_with_ai(text_content, company_name)
        
        return {
            "company_name": company_name,
            "website": website_url,
            "contact_info": contact_info,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def scrape_multiple_companies(self, companies):
        """Scrape multiple VFX companies"""
        results = []
        
        for company in companies:
            try:
                result = self.scrape_company(company['name'], company['url'])
                if result:
                    results.append(result)
                time.sleep(2)  # Be respectful with requests
            except Exception as e:
                print(f"Error processing {company['name']}: {str(e)}")
        
        return results
    
    def save_results(self, results, filename="vfx_contacts.json"):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {filename}")

def main():
    # Get API key from environment variable
    api_key = os.getenv('SARVAM_API_KEY')
    if not api_key:
        print("Error: SARVAM_API_KEY environment variable not set")
        return
    
    # Initialize scraper
    scraper = VFXCompanyScraper(api_key)
    
    # Sample VFX companies to scrape
    companies = [
        {"name": "Industrial Light & Magic", "url": "https://www.ilm.com"},
        {"name": "Weta Digital", "url": "https://www.wetafx.co.nz"},
        {"name": "Framestore", "url": "https://www.framestore.com"},
        {"name": "MPC", "url": "https://www.moving-picture.com"},
        {"name": "Digital Domain", "url": "https://www.digitaldomain.com"}
    ]
    
    print("Starting VFX Company Contact Scraper...")
    print(f"Scraping {len(companies)} companies...\n")
    
    # Scrape companies
    results = scraper.scrape_multiple_companies(companies)
    
    # Save results
    scraper.save_results(results)
    
    print(f"\nCompleted! Scraped {len(results)} companies successfully.")

if __name__ == "__main__":
    main()
