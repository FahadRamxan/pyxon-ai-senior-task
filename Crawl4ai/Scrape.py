from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from bs4 import BeautifulSoup
import re

def is_cookie_content(text):
    """Check if text is cookie/consent related"""
    cookie_phrases = [
        'diese webseite verwendet cookies',
        'cookie-erklärung',
        'cookiebot',
        'consent selection',
        'maximale speicherdauer',
        'pixel-tracker',
        'http-cookie',
        'domainübergreifende zustimmung',
        'meine persönlichen daten nicht verkaufen'
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in cookie_phrases)

def extract_text_from_html(html_content):
    """Extract meaningful text from HTML content with better filtering"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements completely
    for element in soup(['script', 'style', 'noscript']):
        element.decompose()
    
    extracted = []
    seen_texts = set()  # Avoid duplicates
    
    # First pass: Extract all headings
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True)
        if len(text) > 3 and not is_cookie_content(text) and text not in seen_texts:
            level = tag.name[1]
            extracted.append((f'h{level}', text))
            seen_texts.add(text)
    
    # Second pass: Extract paragraphs
    for tag in soup.find_all('p'):
        text = tag.get_text(strip=True)
        # More lenient filtering for paragraphs
        if len(text) > 15 and not is_cookie_content(text) and text not in seen_texts:
            extracted.append(('p', text))
            seen_texts.add(text)
    
    # Third pass: Extract contact links (phone/email)
    for tag in soup.find_all('a'):
        href = tag.get('href', '')
        if href.startswith(('tel:', 'mailto:')):
            text = tag.get_text(strip=True)
            if text and text not in seen_texts:
                extracted.append(('contact', text))
                seen_texts.add(text)
    
    # Fourth pass: Extract list items that aren't navigation
    for tag in soup.find_all('li'):
        # Skip if it's part of navigation
        if tag.find_parent('nav'):
            continue
        text = tag.get_text(strip=True)
        if len(text) > 10 and not is_cookie_content(text) and text not in seen_texts:
            extracted.append(('li', text))
            seen_texts.add(text)
    
    return extracted

def parse_scraped_file(text):
    """Parse the scraped data file with HTML content"""
    elements = []
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for document title
        if i == 0 and line and not line.startswith('#'):
            elements.append(('title', line))
            i += 1
            continue
        
        # Check for page headers (## Page X:)
        if line.startswith('## Page'):
            if len(elements) > 0:  # Add page break before new page (except first)
                elements.append(('page_break', ''))
            elements.append(('h1', line[3:]))  # Remove "## "
            i += 1
            continue
        
        # Check for metadata
        if line.startswith('**URL:**'):
            elements.append(('url', line))
            i += 1
            continue
        
        if line.startswith('**Scraped At:**'):
            elements.append(('meta', line))
            i += 1
            continue
        
        if line.startswith('**Scraping Date:**'):
            elements.append(('meta', line))
            i += 1
            continue
        
        if line.startswith('**Total Pages:**'):
            elements.append(('meta', line))
            i += 1
            continue
        
        # Check for Content: marker followed by HTML
        if line.startswith('**Content:**'):
            i += 1
            # Collect HTML content until separator or next page
            html_content = []
            while i < len(lines):
                current_line = lines[i].strip()
                if current_line.startswith('---') or current_line.startswith('## Page'):
                    break
                html_content.append(lines[i])
                i += 1
            
            # Parse HTML content
            html_text = '\n'.join(html_content)
            if html_text.strip():
                extracted = extract_text_from_html(html_text)
                if extracted:
                    elements.extend(extracted)
                else:
                    # If no content extracted, note it
                    elements.append(('p', '[No content extracted from this page]'))
            continue
        
        # Check for separator
        if line == '---':
            elements.append(('separator', ''))
            i += 1
            continue
        
        # Handle markdown headers at file level
        if line.startswith('###'):
            elements.append(('h3', line[3:].strip()))
        elif line.startswith('##'):
            elements.append(('h2', line[2:].strip()))
        elif line.startswith('#'):
            elements.append(('h1', line[1:].strip()))
        elif line.startswith('**') and line.endswith('**'):
            elements.append(('bold', line[2:-2].strip()))
        elif line and not line.startswith('<'):
            elements.append(('p', line))
        
        i += 1
    
    return elements

def create_pdf(input_file, output_file):
    """Convert scraped text file with HTML to formatted PDF"""
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Title style for main heading
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor='#1a1a1a',
        spaceAfter=20,
        spaceBefore=10,
        leading=34,
        alignment=TA_LEFT
    )
    
    # Page heading style
    page_style = ParagraphStyle(
        'PageHeading',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#0066cc',
        spaceAfter=10,
        spaceBefore=10,
        leading=22
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#2c2c2c',
        spaceAfter=8,
        spaceBefore=10,
        leading=20
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#404040',
        spaceAfter=6,
        spaceBefore=8,
        leading=18
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor='#505050',
        spaceAfter=6,
        spaceBefore=6,
        leading=16
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=11,
        textColor='#1a1a1a',
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#333333',
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    )
    
    list_style = ParagraphStyle(
        'CustomList',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#333333',
        spaceAfter=4,
        leading=14,
        leftIndent=20
    )
    
    url_style = ParagraphStyle(
        'CustomURL',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#0066cc',
        spaceAfter=4,
        fontName='Helvetica-Oblique'
    )
    
    meta_style = ParagraphStyle(
        'CustomMeta',
        parent=styles['Normal'],
        fontSize=8,
        textColor='#666666',
        spaceAfter=2
    )
    
    contact_style = ParagraphStyle(
        'CustomContact',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#0066cc',
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    # Parse content
    elements = parse_scraped_file(content)
    
    print(f"[INFO] Found {len(elements)} content elements to process")
    
    # Build PDF story
    for element_type, text in elements:
        if element_type == 'title':
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.3*inch))
        elif element_type == 'page_break':
            story.append(PageBreak())
        elif element_type == 'h1':
            if 'Page' in text and ':' in text:
                story.append(Paragraph(text, page_style))
            else:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(text, h1_style))
        elif element_type == 'h2':
            story.append(Paragraph(text, h2_style))
        elif element_type == 'h3' or element_type == 'h4' or element_type == 'h5' or element_type == 'h6':
            story.append(Paragraph(text, h3_style))
        elif element_type == 'bold':
            story.append(Paragraph(text, bold_style))
        elif element_type == 'url':
            story.append(Paragraph(text, url_style))
        elif element_type == 'meta':
            story.append(Paragraph(text, meta_style))
        elif element_type == 'contact':
            story.append(Paragraph(f"📞 {text}", contact_style))
        elif element_type == 'li':
            cleaned_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• {cleaned_text}", list_style))
        elif element_type == 'separator':
            story.append(Spacer(1, 0.1*inch))
            story.append(HRFlowable(width="100%", thickness=1, color='#cccccc'))
            story.append(Spacer(1, 0.1*inch))
        elif element_type == 'p':
            # Clean up text and handle special characters
            cleaned_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(cleaned_text, normal_style))
    
    # Build PDF
    doc.build(story)
    print(f"[OK] PDF created successfully: {output_file}")
    print(f"[OK] Total pages and sections processed")

# Example usage
if __name__ == "__main__":
    input_file = "output/scraped_data_20260226_164933.txt"
    output_file = "Pyxon_formatted.pdf"
    
    try:
        create_pdf(input_file, output_file)
    except FileNotFoundError:
        print(f"[ERROR] Input file '{input_file}' not found!")
        print(f"[INFO] Make sure the file exists at: {input_file}")
    except Exception as e:
        print(f"[ERROR] Error creating PDF: {str(e)}")
        import traceback
        traceback.print_exc()