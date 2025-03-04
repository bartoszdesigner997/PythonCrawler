    def _normalize_url(self, url: str) -> str:
        """
        Normalize a URL by ensuring it has a scheme and removing trailing slashes
        
        Args:
            url (str): The URL to normalize
            
        Returns:
            str: The normalized URL
        """
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
            
        return url
# Email Extractor - Main Script
# Orchestrates the email extraction process

import asyncio
import json
import logging
import os
import sys
from typing import List, Set, Dict
from urllib.parse import urlparse

# Import modules
from modules.email_parser import EmailParser
from modules.http_extractor import HttpExtractor
from modules.contact_finder import ContactFinder
from modules.spider import Spider
from modules.playwright_extractor import PlaywrightExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('email_extractor.log')
    ]
)

class EmailExtractor:
    def __init__(self, concurrency: int = 20, timeout: int = 60, batch_size: int = 50):
        """
        Initialize the Email Extractor
        
        Args:
            concurrency (int): Maximum number of concurrent URL processing tasks
            timeout (int): Timeout in seconds for processing a single URL
            batch_size (int): Number of URLs to process in each batch
        """
        self.concurrency = concurrency
        self.timeout = timeout
        self.batch_size = batch_size
        self.email_parser = EmailParser()
        self.http_extractor = HttpExtractor()
        self.contact_finder = ContactFinder()
        self.spider = Spider(max_pages=30, timeout=timeout, max_time_per_domain=300)
        self.playwright_extractor = PlaywrightExtractor(timeout=timeout)
        self.cache_file = 'email_cache.json'
        self.email_cache = self._load_cache()
        self.processed_urls = set()  # Track processed URLs to avoid duplicates
        self.start_time = None
        
    def _load_cache(self) -> Dict[str, List[str]]:
        """
        Load the email cache from file
        
        Returns:
            Dict[str, List[str]]: The email cache (domain -> emails)
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Error loading cache: {str(e)}")
                
        return {}
        
    def _save_cache(self):
        """
        Save the email cache to file
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.email_cache, f, indent=2)
        except Exception as e:
            logging.warning(f"Error saving cache: {str(e)}")
            
    def _get_domain(self, url: str) -> str:
        """
        Extract the domain from a URL
        
        Args:
            url (str): The URL to extract the domain from
            
        Returns:
            str: The domain
        """
        # Normalize the URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Return the domain
        return parsed_url.netloc
        
    async def process_url(self, url: str) -> Set[str]:
        """
        Process a URL to extract emails
        
        Args:
            url (str): The URL to process
            
        Returns:
            Set[str]: A set of extracted email addresses
        """
        # Normalize the URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        domain = self._get_domain(url)
        logging.info(f"Processing {url}")
        
        # Check cache
        if domain in self.email_cache:
            logging.info(f"Using cached emails for {domain}")
            return set(self.email_cache[domain])
            
        # Strategy 1: Try HTTP extraction on the main page
        _, html_content = await self.http_extractor.extract_from_url(url)
        
        if html_content:
            emails = self.email_parser.extract_emails(html_content)
            
            if emails:
                logging.info(f"Found {len(emails)} emails on main page of {url}")
                self._update_cache(domain, emails)
                return emails
                
            # Strategy 2: Look for contact page links
            contact_urls = self.contact_finder.find_contact_links(html_content, url)
            
            if contact_urls:
                logging.info(f"Found {len(contact_urls)} potential contact pages on {url}")
                
                # Check each contact page
                for contact_url in contact_urls[:5]:  # Limit to first 5 contact pages
                    _, contact_html = await self.http_extractor.extract_from_url(contact_url)
                    
                    if contact_html:
                        # Check if it's an Impressum page (common in German websites)
                        if 'impressum' in contact_url.lower():
                            contact_emails = self.email_parser.extract_emails_from_impressum(contact_html)
                        else:
                            contact_emails = self.email_parser.extract_emails(contact_html)
                            
                        if contact_emails:
                            logging.info(f"Found {len(contact_emails)} emails on contact page {contact_url}")
                            self._update_cache(domain, contact_emails)
                            return contact_emails
                            
            # Strategy 3: Try common contact URL patterns
            common_contact_urls = self.contact_finder.generate_common_contact_urls(url)
            
            for common_url in common_contact_urls[:10]:  # Limit to first 10 common patterns
                _, common_html = await self.http_extractor.extract_from_url(common_url)
                
                if common_html:
                    common_emails = self.email_parser.extract_emails(common_html)
                    
                    if common_emails:
                        logging.info(f"Found {len(common_emails)} emails on common contact page {common_url}")
                        self._update_cache(domain, common_emails)
                        return common_emails
                        
            # Strategy 4: Try crawling
            spider_emails = await self.spider.crawl(url, self.http_extractor, self.email_parser)
            
            if spider_emails:
                logging.info(f"Found {len(spider_emails)} emails by crawling {url}")
                self._update_cache(domain, spider_emails)
                return spider_emails
                
        # Strategy 5: Last resort - use Playwright for advanced extraction
        logging.info(f"Using Playwright for advanced extraction on {url}")
        playwright_emails, _ = await self.playwright_extractor.extract_from_url(url)
        
        if playwright_emails:
            logging.info(f"Found {len(playwright_emails)} emails with Playwright on {url}")
            self._update_cache(domain, playwright_emails)
            return playwright_emails
            
        logging.warning(f"No emails found for {url}")
        return set()
        
    def _update_cache(self, domain: str, emails: Set[str]):
        """
        Update the email cache
        
        Args:
            domain (str): The domain
            emails (Set[str]): The emails to cache
        """
        self.email_cache[domain] = list(emails)
        self._save_cache()
        
    async def process_urls(self, urls: List[str]) -> Dict[str, Set[str]]:
        """
        Process multiple URLs with controlled concurrency and batch processing
        
        Args:
            urls (List[str]): The URLs to process
            
        Returns:
            Dict[str, Set[str]]: A dictionary mapping URLs to extracted emails
        """
        self.start_time = time.time()
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in urls:
            normalized_url = self._normalize_url(url)
            if normalized_url not in seen and normalized_url not in self.processed_urls:
                seen.add(normalized_url)
                unique_urls.append(normalized_url)
        
        total_urls = len(unique_urls)
        results = {}
        processed_count = 0
        
        # Process URLs in batches to control memory usage
        for i in range(0, total_urls, self.batch_size):
            batch = unique_urls[i:i + self.batch_size]
            
            # Create a semaphore to limit concurrency
            semaphore = asyncio.Semaphore(self.concurrency)
            
            async def process_with_semaphore(url):
                async with semaphore:
                    return url, await self.process_url(url)
            
            # Create tasks for all URLs in the batch
            tasks = [process_with_semaphore(url) for url in batch]
            
            # Process the batch
            for completed in asyncio.as_completed(tasks):
                url, emails = await completed
                results[url] = emails
                processed_count += 1
                
                # Report progress
                elapsed = time.time() - self.start_time
                emails_found = sum(len(e) for e in results.values())
                progress = (processed_count / total_urls) * 100
                
                logging.info(f"Progress: {processed_count}/{total_urls} URLs ({progress:.1f}%) - "
                             f"Found {emails_found} emails - "
                             f"Elapsed: {elapsed:.1f}s")
                
                # Save intermediate results periodically
                if processed_count % 10 == 0:
                    self._save_cache()
                    
        return results
        
    async def close(self):
        """
        Close resources
        """
        await self.playwright_extractor.close()
        
    def save_results(self, results: Dict[str, Set[str]], output_file: str = 'output.txt'):
        """
        Save the extraction results to a file
        
        Args:
            results (Dict[str, Set[str]]): The extraction results
            output_file (str): The output file path
        """
        # Collect all unique emails
        all_emails = set()
        for emails in results.values():
            all_emails.update(emails)
            
        # Sort emails alphabetically
        sorted_emails = sorted(all_emails)
        
        # Save to file
        with open(output_file, 'w') as f:
            for email in sorted_emails:
                f.write(f"{email}\n")
                
        logging.info(f"Saved {len(sorted_emails)} unique emails to {output_file}")
        
async def main():
    """
    Main function
    """
    import time
    
    print("=== Email Extractor ===")
    print("Enter URLs one per line. Submit an empty line or 'END' to start processing.")
    
    urls = []
    while True:
        try:
            line = input().strip()
            if not line or line.upper() == 'END':
                break
            urls.append(line)
        except EOFError:
            break
        
    if not urls:
        print("No URLs provided. Exiting.")
        return
        
    print(f"Processing {len(urls)} URLs...")
    
    # Create extractor with appropriate concurrency based on URL count
    concurrency = min(20, len(urls))  # Limit concurrency to avoid overwhelming the system
    extractor = EmailExtractor(concurrency=concurrency)
    
    start_time = time.time()
    
    try:
        results = await extractor.process_urls(urls)
        
        # Calculate statistics
        elapsed_time = time.time() - start_time
        total_urls = len(urls)
        successful_urls = len(results)
        total_emails = sum(len(emails) for emails in results.values())
        unique_emails = len(set().union(*results.values())) if results else 0
        
        # Print summary
        print("\n=== Results ===")
        print(f"Processed {successful_urls}/{total_urls} URLs in {elapsed_time:.1f} seconds")
        print(f"Average time per URL: {elapsed_time/total_urls:.2f} seconds")
        
        for url, emails in results.items():
            email_count = len(emails)
            if email_count > 0:
                print(f"{url}: {email_count} emails")
            
        print(f"\nTotal emails found: {total_emails}")
        print(f"Unique emails found: {unique_emails}")
        
        # Save results
        extractor.save_results(results)
        print("Emails saved to output.txt")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Saving partial results...")
        # Save partial results if available
        if 'results' in locals() and results:
            extractor.save_results(results)
            print("Partial results saved to output.txt")
    finally:
        await extractor.close()
        
if __name__ == "__main__":
    asyncio.run(main())