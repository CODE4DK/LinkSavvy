import PyPDF2
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def chunk_text(text, chunk_size=4000):
    """Splits long text into manageable chunks so the AI doesn't lose focus."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def extract_text_from_pdf(file_bytes):
    """Reads a PDF file from bytes and extracts the text."""
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

def scrape_linkedin_url(url):
    """Uses a headless browser to scrape text from a LinkedIn public URL."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3) # Wait for JavaScript to load
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        # Strip out standard web junk and keep the core text
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        return text[:3000] # Return the first 3000 characters to save tokens
    except Exception as e:
        return f"Could not extract data from URL: {str(e)}"