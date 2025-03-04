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
            
        # Clean the text by replacing HTML entities
        cleaned_text = self._clean_html_entities(text)
        
        # Find all potential email matches
        potential_emails = self.email_pattern.findall(cleaned_text)
        
        # Find obfuscated emails
        obfuscated_emails = self._extract_obfuscated_emails(cleaned_text)
        
        # Combine all potential emails
        all_potential_emails = potential_emails + obfuscated_emails
        
        # Filter and clean the results
        valid_emails = set()
        for email in all_potential_emails:
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
        
    def _clean_html_entities(self, text: str) -> str:
        """
        Clean HTML entities in text
        
        Args:
            text (str): The text to clean
            
        Returns:
            str: The cleaned text
        """
        # Replace common HTML entities
        for entity, replacement in self.obfuscation_replacements.items():
            text = text.replace(entity, replacement)
            
        # Replace numeric HTML entities (e.g., &#64; for @)
        def replace_entity(match):
            try:
                return chr(int(match.group(0)[2:-1]))
            except:
                return match.group(0)
                
        text = self.html_entity_pattern.sub(replace_entity, text)
        
        return text

    def _extract_obfuscated_emails(self, text: str) -> List[str]:
        """
        Extract emails that are obfuscated in various ways
        
        Args:
            text (str): The text to extract obfuscated emails from
            
        Returns:
            List[str]: A list of extracted email addresses
        """
        emails = []
        
        # Find obfuscated emails using the pattern
        matches = self.obfuscated_pattern.findall(text)
        
        for match in matches:
            if match and len(match) == 3:
                # Construct the email from the parts
                email = f"{match[0]}@{match[1]}.{match[2]}"
                emails.append(email)
                
        # Look for JavaScript obfuscation patterns
        # Example: var email = 'user' + '@' + 'domain.com';
        js_pattern = re.compile(r"['\"]([a-zA-Z0-9._%+\-]+)['\"][\s]*\+[\s]*['\"]@['\"][\s]*\+[\s]*['\"]([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})['\"]")
        js_matches = js_pattern.findall(text)
        
        for match in js_matches:
            if match and len(match) == 2:
                email = f"{match[0]}@{match[1]}"
                emails.append(email)
                
        # Look for CSS obfuscation
        # Example: <span class="user">user</span><span class="at">@</span><span class="domain">domain.com</span>
        # This is harder to detect with regex alone, but we can try some common patterns
        css_pattern = re.compile(r'<span[^>]*>([a-zA-Z0-9._%+\-]+)</span><span[^>]*>@</span><span[^>]*>([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})</span>')
        css_matches = css_pattern.findall(text)
        
        for match in css_matches:
            if match and len(match) == 2:
                email = f"{match[0]}@{match[1]}"
                emails.append(email)
                
        return emails
        
    def extract_emails_from_impressum(self, text: str) -> Set[str]:
        """
        Special extraction for Impressum pages (common in German-speaking regions)
        These pages often contain contact information in specific formats
        
        Args:
            text (str): The text content of the Impressum page
            
        Returns:
            Set[str]: A set of unique valid email addresses
        """
        # Get standard emails
        emails = self.extract_emails(text)
        
        # Look for specific patterns common in Impressum pages
        
        # Pattern for "E-Mail: " followed by an email or obfuscated email
        email_label_pattern = re.compile(r'(?:E-Mail|Email|E-mail|Mail|Mailto|Kontakt|Contact)[\s]*:[\s]*([^\n<]+)', re.IGNORECASE)
        
        matches = email_label_pattern.findall(text)
        for match in matches:
            # Clean the match
            cleaned_match = match.strip()
            
            # Check if it's already an email
            if '@' in cleaned_match and '.' in cleaned_match:
                potential_email = cleaned_match
                # Clean the email
                potential_email = self._clean_email(potential_email)
                if self._validate_email(potential_email):
                    emails.add(potential_email.lower())
            else:
                # It might be an obfuscated email
                obfuscated_emails = self._extract_obfuscated_emails(cleaned_match)
                for email in obfuscated_emails:
                    if self._validate_email(email):
                        emails.add(email.lower())
                        
        return emails