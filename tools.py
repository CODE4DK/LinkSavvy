# tools.py
import PyPDF2
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def scrape_linkedin_url(url):
    """
    Visits a URL using a headless browser and extracts the visible text.
    """
    print(f"🕵️‍♂️ Initializing scraper for: {url}")
    
    # Configure Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without opening a visible window
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add a user-agent to look less like a bot
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        # Launch the browser
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to the page
        driver.get(url)
        
        # Pause to let JavaScript load (LinkedIn is heavy on dynamic content)
        time.sleep(5)
        
        # Grab the fully rendered HTML
        page_source = driver.page_source
        driver.quit()
        
        # Parse the HTML to extract clean text
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        clean_text = soup.get_text(separator=' ', strip=True)
        return clean_text
        
    except Exception as e:
        return f"🚨 Error scraping the page: {str(e)}"
    
def extract_text_from_pdf(file_bytes):
    """
    Reads a PDF file from bytes and extracts the text.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"🚨 Error reading PDF: {str(e)}"    
    
def chunk_text(text, chunk_size=4000):
    """
    Splits long text into manageable chunks so the AI 
    doesn't lose focus on specific details.
    """
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]    

# --- Local Testing Block ---
# This only runs if you execute tools.py directly, not when imported.
if __name__ == "__main__":
    test_url = "https://www.linkedin.com/in/dinesh-kumar-j/" # Replace with any public URL to test
    print("Testing scraper...")
    result = scrape_linkedin_url(test_url)
    print("\n--- Extracted Text Preview ---")
    print(result[:500]) # Print the first 500 characters
    print("------------------------------")