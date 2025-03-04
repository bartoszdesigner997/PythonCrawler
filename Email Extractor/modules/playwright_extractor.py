# Playwright Extractor Module
# Provides advanced email extraction using browser automation

import asyncio
from typing import Set, Optional, Tuple
import logging
import re
from playwright.async_api import async_playwright, Page, Browser, TimeoutError

class PlaywrightExtractor:
    def __init__(self, timeout: int = 30):
        """
        Initialize the Playwright extractor
        
        Args:
            timeout (int): Timeout in seconds for page loading
        """
        self.timeout = timeout
        self.browser = None
        
    async def setup(self):
        """
        Set up the Playwright browser instance
        """
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            
    async def extract_from_url(self, url: str) -> Tuple[Set[str], Optional[str]]:
        """
        Extract emails from a URL using Playwright browser automation
        
        Args:
            url (str): The URL to extract emails from
            
        Returns:
            Tuple[Set[str], Optional[str]]: A tuple containing:
                - Set of extracted emails (empty if none found)
                - HTML content of the page (None if extraction failed)
        """
        # Normalize the URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        # Ensure browser is set up
        await self.setup()
        
        # Create a new page
        page = await self.browser.new_page()
        
        try:
            # Set timeout
            page.set_default_timeout(self.timeout * 1000)
            
            # Navigate to the URL
            await page.goto(url, wait_until='domcontentloaded')
            
            # Wait for the page to be fully loaded
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except TimeoutError:
                # Continue even if networkidle times out
                pass
                
            # Handle cookie consent dialogs (common in EU websites)
            await self._handle_cookie_dialogs(page)
            
            # Scroll to load lazy content
            await self._scroll_page(page)
            
            # Extract HTML content
            html_content = await page.content()
            
            # Extract emails from various sources
            emails = await self._extract_emails_from_page(page)
            
            return emails, html_content
            
        except Exception as e:
            logging.warning(f"Error extracting emails with Playwright from {url}: {str(e)}")
            return set(), None
            
        finally:
            await page.close()
            
    async def _handle_cookie_dialogs(self, page: Page):
        """
        Attempt to handle common cookie consent dialogs
        
        Args:
            page (Page): The Playwright page object
        """
        # Common cookie consent button selectors
        cookie_button_selectors = [
            'button:has-text("Accept")', 
            'button:has-text("Accept All")',
            'button:has-text("I Accept")',
            'button:has-text("OK")',
            'button:has-text("Agree")',
            'button:has-text("Got it")',
            'button:has-text("Akzeptieren")',  # German
            'button:has-text("Accepter")',     # French
            'button:has-text("Aceptar")',      # Spanish
            'button:has-text("Accetto")',      # Italian
            '.cookie-banner button',
            '.cookie-consent button',
            '#cookie-notice button',
            '#gdpr-consent button',
            '.consent-banner button'
        ]
        
        for selector in cookie_button_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.locator(selector).first.click(timeout=5000)
                    await page.wait_for_timeout(1000)  # Wait for dialog to disappear
                    break
            except Exception:
                continue
                
    async def _scroll_page(self, page: Page):
        """
        Scroll the page to load lazy-loaded content
        
        Args:
            page (Page): The Playwright page object
        """
        # Get the page height
        height = await page.evaluate('document.body.scrollHeight')
        
        # Scroll in increments
        viewport_height = await page.evaluate('window.innerHeight')
        for i in range(0, height, viewport_height):
            await page.evaluate(f'window.scrollTo(0, {i})')
            await page.wait_for_timeout(500)  # Wait for content to load
            
        # Scroll back to top
        await page.evaluate('window.scrollTo(0, 0)')
        
    async def _extract_emails_from_page(self, page: Page) -> Set[str]:
        """
        Extract emails from various sources in the page
        
        Args:
            page (Page): The Playwright page object
            
        Returns:
            Set[str]: A set of extracted email addresses
        """
        emails = set()
        
        # Extract emails from page content
        content = await page.content()
        emails.update(self._extract_emails_from_text(content))
        
        # Extract emails from JavaScript variables
        js_emails = await self._extract_emails_from_js(page)
        emails.update(js_emails)
        
        # Extract emails from data attributes
        data_emails = await self._extract_emails_from_data_attributes(page)
        emails.update(data_emails)
        
        # Extract emails from onclick handlers
        onclick_emails = await self._extract_emails_from_onclick(page)
        emails.update(onclick_emails)
        
        return emails
        
    def _extract_emails_from_text(self, text: str) -> Set[str]:
        """
        Extract emails from text using regex
        
        Args:
            text (str): The text to extract emails from
            
        Returns:
            Set[str]: A set of extracted email addresses
        """
        if not text:
            return set()
            
        # Email regex pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Find all email matches
        matches = re.findall(email_pattern, text)
        
        # Filter out common false positives
        filtered_emails = set()
        for email in matches:
            # Skip image file extensions
            if re.search(r'\.(?:png|jpg|jpeg|gif|bmp|svg|webp|css|js)@', email):
                continue
                
            # Skip placeholder emails
            if re.search(r'(?:example|sample|test|user)@(?:example|sample|test|domain)', email.lower()):
                continue
                
            filtered_emails.add(email.lower())
            
        return filtered_emails
        
    async def _extract_emails_from_js(self, page: Page) -> Set[str]:
        """
        Extract emails from JavaScript variables
        
        Args:
            page (Page): The Playwright page object
            
        Returns:
            Set[str]: A set of extracted email addresses
        """
        # Get all script content
        scripts = await page.evaluate('''
            Array.from(document.querySelectorAll('script'))
                .map(script => script.textContent)
                .join('\\n')
        ''')
        
        return self._extract_emails_from_text(scripts)
        
    async def _extract_emails_from_data_attributes(self, page: Page) -> Set[str]:
        """
        Extract emails from data attributes
        
        Args:
            page (Page): The Playwright page object
            
        Returns:
            Set[str]: A set of extracted email addresses
        """
        # Get all elements with data attributes
        data_attrs = await page.evaluate('''
            Array.from(document.querySelectorAll('*[data-*]'))
                .map(el => {
                    let attrs = '';
                    for (let i = 0; i < el.attributes.length; i++) {
                        if (el.attributes[i].name.startsWith('data-')) {
                            attrs += el.attributes[i].value + ' ';
                        }
                    }
                    return attrs;
                })
                .join('\\n')
        ''')
        
        return self._extract_emails_from_text(data_attrs)
        
    async def _extract_emails_from_onclick(self, page: Page) -> Set[str]:
        """
        Extract emails from onclick handlers
        
        Args:
            page (Page): The Playwright page object
            
        Returns:
            Set[str]: A set of extracted email addresses
        """
        # Get all elements with onclick attributes
        onclick_attrs = await page.evaluate('''
            Array.from(document.querySelectorAll('*[onclick]'))
                .map(el => el.getAttribute('onclick'))
                .join('\\n')
        ''')
        
        return self._extract_emails_from_text(onclick_attrs)
        
    async def close(self):
        """
        Close the browser instance
        """
        if self.browser:
            await self.browser.close()
            self.browser = None