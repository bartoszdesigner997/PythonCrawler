# HTTP Extractor Module
# Handles email extraction using standard HTTP requests

import aiohttp
import asyncio
from typing import Tuple, Set, Optional
import logging
from urllib.parse import urlparse, urljoin

class HttpExtractor:
    def __init__(self, timeout: int = 10):
        """
        Initialize the HTTP extractor
        
        Args:
            timeout (int): Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
    async def extract_from_url(self, url: str) -> Tuple[Set[str], Optional[str]]:
        """
        Extract emails from a URL using HTTP requests
        
        Args:
            url (str): The URL to extract emails from
            
        Returns:
            Tuple[Set[str], Optional[str]]: A tuple containing:
                - Set of extracted emails (empty if none found)
                - HTML content of the page (None if request failed)
        """
        # Normalize the URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        try:
            # Create a timeout context
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers, allow_redirects=True) as response:
                    if response.status != 200:
                        logging.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        return set(), None
                        
                    # Get the content type
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # Skip non-HTML content
                    if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                        logging.info(f"Skipping non-HTML content at {url}: {content_type}")
                        return set(), None
                        
                    # Read the HTML content
                    html_content = await response.text(errors='replace')
                    
                    # We don't extract emails here - we return the HTML for processing by the email parser
                    return set(), html_content
                    
        except asyncio.TimeoutError:
            logging.warning(f"Timeout while fetching {url}")
            return set(), None
        except Exception as e:
            logging.warning(f"Error fetching {url}: {str(e)}")
            return set(), None
            
    def normalize_url(self, base_url: str, url: str) -> str:
        """
        Normalize a URL by ensuring it has a scheme and is absolute
        
        Args:
            base_url (str): The base URL for relative URLs
            url (str): The URL to normalize
            
        Returns:
            str: The normalized URL
        """
        # Add scheme if missing
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'https://{base_url}'
            
        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
            
        # Remove fragments
        url = url.split('#')[0]
        
        # Ensure we're not leaving the original domain
        base_domain = urlparse(base_url).netloc
        url_domain = urlparse(url).netloc
        
        # If the domains don't match and the URL domain is not a subdomain of the base domain
        if url_domain != base_domain and not url_domain.endswith(f'.{base_domain}'):
            return None
            
        return url