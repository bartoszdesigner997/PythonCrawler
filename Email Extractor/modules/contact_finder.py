# Contact Finder Module
# Specializes in locating contact pages on websites

import re
from typing import List, Set, Dict, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

class ContactFinder:
    def __init__(self):
        """
        Initialize the contact finder with multilingual contact page keywords
        """
        # Multilingual keywords for contact pages in all EU languages
        self.contact_keywords = {
            # English
            'en': ['contact', 'contact-us', 'contact_us', 'contactus', 'get-in-touch', 'reach-us', 'email-us'],
            # German
            'de': ['kontakt', 'impressum', 'uber-uns', 'ueber-uns', 'about-us', 'ansprechpartner'],
            # French
            'fr': ['contact', 'contactez-nous', 'nous-contacter', 'a-propos'],
            # Italian
            'it': ['contatti', 'contattaci', 'chi-siamo', 'about'],
            # Spanish
            'es': ['contacto', 'contactenos', 'sobre-nosotros', 'acerca-de'],
            # Portuguese
            'pt': ['contacto', 'contato', 'fale-conosco', 'sobre-nos'],
            # Dutch
            'nl': ['contact', 'neem-contact-op', 'over-ons'],
            # Polish
            'pl': ['kontakt', 'o-nas', 'o-firmie'],
            # Swedish
            'se': ['kontakt', 'kontakta-oss', 'om-oss'],
            # Danish
            'dk': ['kontakt', 'om-os'],
            # Finnish
            'fi': ['yhteystiedot', 'ota-yhteytta', 'meista'],
            # Czech
            'cz': ['kontakt', 'o-nas', 'o-spolecnosti'],
            # Hungarian
            'hu': ['kapcsolat', 'rolunk', 'cegunkrol'],
            # Romanian
            'ro': ['contact', 'despre-noi', 'despre-companie'],
            # Greek
            'gr': ['epikoinonia', 'contact', 'sxetika-me'],
            # Bulgarian
            'bg': ['kontakti', 'za-nas'],
            # Croatian
            'hr': ['kontakt', 'o-nama'],
            # Slovak
            'sk': ['kontakt', 'o-nas'],
            # Slovenian
            'si': ['kontakt', 'o-nas'],
            # Estonian
            'ee': ['kontakt', 'meist'],
            # Latvian
            'lv': ['kontakti', 'par-mums'],
            # Lithuanian
            'lt': ['kontaktai', 'apie-mus'],
            # Irish
            'ie': ['contact', 'about-us', 'about'],
            # Maltese
            'mt': ['kuntatt', 'dwarna'],
            # Generic (used as fallback)
            'generic': ['contact', 'about', 'info', 'impressum', 'kontakt', 'contatti', 'contacto']
        }
        
        # Common contact URL patterns
        self.common_contact_paths = [
            '/contact', '/contact-us', '/contactus', '/kontakt', '/impressum',
            '/about/contact', '/about-us/contact', '/get-in-touch',
            '/about', '/about-us', '/about_us', '/aboutus',
            '/company/contact', '/support', '/help', '/reach-us',
            '/info/contact', '/contact/index.html', '/en/contact', '/en/about'
        ]
        
    def find_contact_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Find contact page links in HTML content
        
        Args:
            html_content (str): The HTML content to search
            base_url (str): The base URL for resolving relative links
            
        Returns:
            List[str]: A list of contact page URLs
        """
        if not html_content:
            return []
            
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Determine the likely language based on the TLD
        language = self._detect_language(base_url)
        
        # Get keywords for the detected language and add generic keywords
        keywords = self.contact_keywords.get(language, []) + self.contact_keywords['generic']
        
        # Find all links
        contact_urls = []
        
        # Look for links with contact keywords in href, text, or title
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
                
            # Get link text and title
            link_text = link.get_text().strip().lower()
            link_title = link.get('title', '').strip().lower()
            
            # Check if any keyword is in the href, text, or title
            if any(keyword in href.lower() for keyword in keywords) or \
               any(keyword in link_text for keyword in keywords) or \
               any(keyword in link_title for keyword in keywords):
                # Resolve relative URLs
                full_url = urljoin(base_url, href)
                contact_urls.append(full_url)
                
        # Look for links in navigation menus or footers (common locations for contact links)
        for nav_element in soup.find_all(['nav', 'footer', 'header']):
            for link in nav_element.find_all('a', href=True):
                href = link.get('href', '').strip()
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                    continue
                    
                link_text = link.get_text().strip().lower()
                if any(keyword in link_text for keyword in keywords) or \
                   any(keyword in href.lower() for keyword in keywords):
                    full_url = urljoin(base_url, href)
                    contact_urls.append(full_url)
                    
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in contact_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
                
        return unique_urls
        
    def generate_common_contact_urls(self, base_url: str) -> List[str]:
        """
        Generate common contact page URLs based on the base URL and detected language
        
        Args:
            base_url (str): The base URL of the website
            
        Returns:
            List[str]: A list of potential contact page URLs
        """
        # Ensure base_url has a scheme
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'https://{base_url}'
            
        # Remove trailing slash if present
        if base_url.endswith('/'):
            base_url = base_url[:-1]
            
        # Determine the likely language based on the URL
        language = self._detect_language(base_url)
        
        # Get language-specific paths
        language_paths = []
        if language in self.contact_keywords:
            language_paths = [f'/{keyword}' for keyword in self.contact_keywords[language]]
            
        # Add paths with language prefix for international sites
        # For example: /en/contact, /de/kontakt, etc.
        international_paths = []
        for lang, keywords in self.contact_keywords.items():
            if lang != 'generic':
                for keyword in keywords[:3]:  # Limit to first 3 keywords per language
                    international_paths.append(f'/{lang}/{keyword}')
                    
        # Combine with common paths
        all_paths = self.common_contact_paths + language_paths + international_paths
        
        # Add variations with common prefixes and suffixes
        variations = []
        prefixes = ['', '/about/', '/company/', '/info/']
        suffixes = ['', '.html', '.php', '.aspx', '/index.html']
        
        for path in language_paths[:5]:  # Limit to first 5 language-specific paths
            for prefix in prefixes:
                for suffix in suffixes:
                    if not path.startswith('/'):
                        path = '/' + path
                    variations.append(f"{prefix}{path}{suffix}")
                    
        # Generate full URLs, removing duplicates
        all_paths = list(set(all_paths + variations))
        contact_urls = [f"{base_url}{path}" for path in all_paths]
        
        # Limit the number of URLs to avoid excessive requests
        return contact_urls[:30]  # Return up to 30 potential contact URLs
        
    def _detect_language(self, url: str) -> str:
        """
        Detect the likely language of a website based on its TLD
        
        Args:
            url (str): The URL to analyze
            
        Returns:
            str: The detected language code or 'generic' if unknown
        """
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Get the domain
            domain = parsed_url.netloc.lower()
            
            # Extract the TLD
            tld = domain.split('.')[-1]
            
            # Check if the TLD is a country code that maps to a language
            if tld in self.contact_keywords:
                return tld
                
            # Special cases
            if tld == 'com' or tld == 'org' or tld == 'net':
                # Check for language in subdomain (e.g., de.example.com)
                subdomain = domain.split('.')[0]
                if subdomain in self.contact_keywords:
                    return subdomain
                    
            # Default to generic
            return 'generic'
            
        except Exception:
            return 'generic'