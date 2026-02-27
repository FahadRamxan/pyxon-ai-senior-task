import os
import sys
import psutil
import asyncio
import requests
from xml.etree import ElementTree
from datetime import datetime

__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")

# Append parent directory to system path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    print("\n=== Parallel Crawling with Browser Reuse + Memory Check ===")

    # We'll keep track of peak memory usage across all tasks
    peak_memory = 0
    process = psutil.Process(os.getpid())
    scraped_data = []  # Store all scraped data

    def log_memory(prefix: str = ""):
        nonlocal peak_memory
        current_mem = process.memory_info().rss  # in bytes
        if current_mem > peak_memory:
            peak_memory = current_mem
        print(f"{prefix} Current Memory: {current_mem // (1024 * 1024)} MB, Peak: {peak_memory // (1024 * 1024)} MB")

    # Minimal browser config
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,   # corrected from 'verbos=False'
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # We'll chunk the URLs in batches of 'max_concurrent'
        success_count = 0
        fail_count = 0
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                # Unique session_id per concurrent sub-task
                session_id = f"parallel_session_{i + j}"
                task = crawler.arun(url=url, config=crawl_config, session_id=session_id)
                tasks.append(task)

            # Check memory usage prior to launching tasks
            log_memory(prefix=f"Before batch {i//max_concurrent + 1}: ")

            # Gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check memory usage after tasks complete
            log_memory(prefix=f"After batch {i//max_concurrent + 1}: ")

            # Evaluate results and collect data
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                    fail_count += 1
                elif result.success:
                    success_count += 1
                    # Store the scraped data
                    scraped_data.append({
                        'url': url,
                        'title': result.metadata.get('title', 'No title'),
                        'content': result.cleaned_html or result.html or 'No content',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    fail_count += 1

        print("\nSummary:")
        print(f"  - Successfully crawled: {success_count}")
        print(f"  - Failed: {fail_count}")

        # Save data to markdown
        if scraped_data:
            save_to_markdown(scraped_data, max_content_length=None)  # Set to None for no truncation

    finally:
        print("\nClosing crawler...")
        await crawler.close()
        # Final memory log
        log_memory(prefix="Final: ")
        print(f"\nPeak memory usage (MB): {peak_memory // (1024 * 1024)}")

def save_to_markdown(scraped_data, max_content_length=100000000):
    """
    Save scraped data to a markdown file with proper formatting.
    
    Args:
        scraped_data: List of dictionaries containing scraped data
        max_content_length: Maximum length of content to save (set to None for no limit)
    """
    # Create output directory if it doesn't exist
    os.makedirs(__output__, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scraped_data_{timestamp}.txt"
    filepath = os.path.join(__output__, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("# Fahrschule Lagarde - Scraped Data\n\n")
            f.write(f"**Scraping Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Pages:** {len(scraped_data)}\n\n")
            f.write("---\n\n")
            
            # Write data for each page
            for i, data in enumerate(scraped_data, 1):
                f.write(f"## Page {i}: {data['title']}\n\n")
                f.write(f"**URL:** {data['url']}\n\n")
                f.write(f"**Scraped At:** {data['timestamp']}\n\n")
                
                # Clean and format content
                content = data['content']
                if content and content != 'No content':
                    # Remove excessive whitespace and newlines, but preserve structure
                    content = ' '.join(content.split())
                    # Truncate content if max_content_length is set and content exceeds it
                    if max_content_length and len(content) > max_content_length:
                        content = content[:max_content_length] + f"\n\n... [Content truncated - showing first {max_content_length:,} characters]"
                    f.write(f"**Content:**\n\n{content}\n\n")
                else:
                    f.write("**Content:** No content available\n\n")
                
                f.write("---\n\n")
        
        print(f"\n✅ Data saved to: {filepath}")
        print(f"📄 Total pages saved: {len(scraped_data)}")
        
    except (IOError, OSError) as e:
        print(f"❌ Error saving to markdown: {e}")

def get_pydantic_ai_docs_urls():
    """
    Fetches all URLs from the Pydantic AI documentation.
    Uses the sitemap (https://ai.pydantic.dev/sitemap.xml) to get these URLs.
    
    Returns:
        List[str]: List of URLs
    """            
    sitemap_url = "https://pyxon.com/sitemap.xml"
    try:
        response = requests.get(sitemap_url, timeout=30)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        # The namespace is usually defined in the root element
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except (requests.RequestException, ElementTree.ParseError) as e:
        print(f"Error fetching sitemap: {e}")
        return []        

async def main():
    urls = get_pydantic_ai_docs_urls()
    if urls:
        print(f"Found {len(urls)} URLs to crawl")
        await crawl_parallel(urls, max_concurrent=10)
    else:
        print("No URLs found to crawl")    

if __name__ == "__main__":
    asyncio.run(main())