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
    
from fpdf import FPDF
import io

def create_pdf_carousel(text_content):
    """Parses text for [SLIDE] tags and generates a multi-page PDF."""
    pdf = FPDF(orientation='P', unit='mm', format=(108, 135)) # Standard 4:5 aspect ratio for LinkedIn
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Split the AI's text by the [SLIDE] marker
    slides = text_content.split("[SLIDE]")
    
    for slide in slides:
        clean_slide = slide.strip()
        if not clean_slide:
            continue
            
        pdf.add_page()
        pdf.set_font("Arial", size=16) # Using standard Arial
        
        # Add a simple background color (light gray)
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(0, 0, 108, 135, 'F')
        
        # Add the text
        # Encoding handles special characters that might break FPDF
        encoded_text = clean_slide.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, encoded_text, align='C')

    # Output to a byte stream so Streamlit can download it
    return pdf.output(dest='S').encode('latin-1')    