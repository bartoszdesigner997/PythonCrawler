# Email Parser Module
# Responsible for email extraction and validation

import re
from typing import List, Set

class EmailParser:
    def __init__(self):
        # Regular expression for matching email addresses
        # This pattern is designed to match valid email addresses while reducing false positives
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
        # Pattern to exclude common false positives
        self.exclusion_pattern = re.compile(r'\.(?:png|jpg|jpeg|gif|bmp|svg|webp|css|js)@')
        
        # Pattern to identify placeholder/example emails
        self.placeholder_pattern = re.compile(r'(?:example|sample|test|user|info|admin|mail)@(?:example|sample|test|domain|yoursite|yourcompany|yourdomain)\.')
        
    def extract_emails(self, text: str) -> Set[str]:
        """
        Extract and validate email addresses from text content
        
        Args:
            text (str): The text content to search for emails
            
        Returns:
            Set[str]: A set of unique valid email addresses
        """
        if not text:
            return set()
            
        # Find all potential email matches
        potential_emails = self.email_pattern.findall(text)
        
        # Filter and clean the results
        valid_emails = set()
        for email in potential_emails:
            # Skip if it matches exclusion patterns
            if self.exclusion_pattern.search(email):
                continue
                
            # Skip placeholder/example emails
            if self.placeholder_pattern.search(email.lower()):
                continue
                
            # Clean the email (remove trailing punctuation, etc.)
            clean_email = self._clean_email(email)
            
            # Validate the email structure
            if self._validate_email(clean_email):
                valid_emails.add(clean_email.lower())  # Store as lowercase for consistency
                
        return valid_emails
        
    def _clean_email(self, email: str) -> str:
        """
        Clean an email address by removing trailing punctuation and other artifacts
        
        Args:
            email (str): The email address to clean
            
        Returns:
            str: The cleaned email address
        """
        # Remove trailing punctuation and common artifacts
        email = re.sub(r'[.,;:\'\"!?<>()[\]{}]$', '', email)
        
        # Remove HTML entities and tags
        email = re.sub(r'&[a-zA-Z]+;', '', email)
        email = re.sub(r'<[^>]+>', '', email)
        
        return email.strip()
        
    def _validate_email(self, email: str) -> bool:
        """
        Validate the structure of an email address
        
        Args:
            email (str): The email address to validate
            
        Returns:
            bool: True if the email is valid, False otherwise
        """
        # Basic structural validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False
            
        # Check for consecutive special characters (likely invalid)
        if re.search(r'[._%+-]{2,}', email):
            return False
            
        # Check domain part
        domain_parts = email.split('@')[1].split('.')
        
        # Domain must have at least one period and valid parts
        if len(domain_parts) < 2:
            return False
            
        # TLD should be 2-7 characters and alphabetic
        tld = domain_parts[-1]
        if not (2 <= len(tld) <= 7 and tld.isalpha()):
            return False
            
        return True
        
    def extract_emails_from_impressum(self, text: str) -> Set[str]:
        """
        Special extraction for Impressum pages (common in German-speaking regions)
        These pages often contain contact information in specific formats
        
        Args:
            text (str): The text content of the Impressum page
            
        Returns:
            Set[str]: A set of unique valid email addresses
        """
        emails = self.extract_emails(text)
        
        # Look for email addresses written in text form (e.g., "name (at) domain (dot) com")
        text_form_pattern = re.compile(r'([a-zA-Z0-9._%+-]+)[\s]*(?:\[at\]|\(at\)|@|&#64;|&#9090;|at)[\s]*([a-zA-Z0-9.-]+)[\s]*(?:\[dot\]|\(dot\)|\.|\.|dot)[\s]*([a-zA-Z]{2,})')
        
        matches = text_form_pattern.findall(text)
        for match in matches:
            if match and len(match) == 3:
                constructed_email = f"{match[0]}@{match[1]}.{match[2]}"
                if self._validate_email(constructed_email):
                    emails.add(constructed_email.lower())
                    
        return emails