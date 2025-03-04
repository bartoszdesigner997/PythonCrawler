# Spider Module
# Handles web crawling and link extraction

import asyncio
from typing import List, Set, Dict, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging

class Spider:
    def __init__(self, max_depth: int = 2, max_pages: int = 10):
        """
        Initialize the spider with crawling limits
        
        Args:
            max_depth (int): Maximum crawling depth
            max_pages (int): Maximum number of pages to crawl
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls = set()
        
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract links from HTML content
        
        Args:
            html_content (str): The HTML content to extract links from
            base_url (str): The base URL for resolving relative links
            
        Returns:
            List[str]: A list of extracted links
        """
        if not html_content:
            return []
            
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all links
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            
            # Skip empty links and non-HTTP links
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
                
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            # Skip fragments within the same page
            if full_url.split('#')[0] == base_url:
                continue
                
            # Ensure we're not leaving the original domain
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(full_url).netloc
            
            if url_domain != base_domain and not url_domain.endswith(f'.{base_domain}'):
                continue
                
            links.append(full_url)
            
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
                
        return unique_links
        
    async def crawl(self, start_url: str, http_extractor, email_parser) -> Set[str]:
        """
        Crawl a website starting from a URL and extract emails
        
        Args:
            start_url (str): The starting URL for crawling
            http_extractor: The HTTP extractor instance
            email_parser: The email parser instance
            
        Returns:
            Set[str]: A set of unique email addresses found
        """
        # Normalize the URL
        if not start_url.startswith(('http://', 'https://')):
            start_url = f'https://{start_url}'
            
        # Initialize crawling variables
        self.visited_urls = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        all_emails = set()
        pages_visited = 0
        
        # Start crawling
        while to_visit and pages_visited < self.max_pages:
            # Get the next URL to visit
            current_url, depth = to_visit.pop(0)
            
            # Skip if already visited or depth exceeded
            if current_url in self.visited_urls or depth > self.max_depth:
                continue
                
            # Mark as visited
            self.visited_urls.add(current_url)
            pages_visited += 1
            
            # Fetch the page
            _, html_content = await http_extractor.extract_from_url(current_url)
            
            if not html_content:
                continue
                
            # Extract emails from the page
            emails = email_parser.extract_emails(html_content)
            all_emails.update(emails)
            
            # Check if we found emails - if so, we can stop crawling
            if emails:
                logging.info(f"Found {len(emails)} emails on {current_url}")
                break
                
            # If we're at max depth, don't extract more links
            if depth >= self.max_depth:
                continue
                
            # Extract links for further crawling
            links = self.extract_links(html_content, current_url)
            
            # Add new links to the queue
            for link in links:
                if link not in self.visited_urls:
                    to_visit.append((link, depth + 1))
                    
        return all_emails