# Email Extractor - Project Overview

## Introduction

The Email Extractor is a Python-based tool designed to efficiently extract email addresses from websites. It processes URLs entered via the console and employs multiple strategies to locate email addresses on main pages and contact pages. The tool supports all EU country languages and employs various techniques to maximize email discovery success rate.

## Project Purpose

The primary purpose of this project is to provide an efficient and effective way to extract email addresses from websites. The application supports:

- Processing multiple URLs (entered one per line)
- Extracting emails from both main pages and contact pages
- Multilingual support for all EU country languages
- Advanced extraction techniques when simpler methods fail
- Optimized performance for speed and effectiveness
- Saving extracted emails to an output file

## Project Structure

The project follows a modular structure with a main script and several specialized modules:

```
/
├── email_extractor.py        # Main script and entry point
├── email_cache.json          # Cache for previously extracted emails
├── modules/                  # Folder containing specialized modules
│   ├── __init__.py           # Module initialization
│   ├── spider.py             # Web crawling and link extraction
│   ├── playwright_extractor.py # Advanced extraction using browser automation
│   ├── http_extractor.py     # Basic extraction using HTTP requests
│   ├── email_parser.py       # Email pattern matching and validation
│   └── contact_finder.py     # Finding contact pages on websites
```

## Module Descriptions

### Main Script (email_extractor.py)

This is the entry point of the application. It orchestrates the email extraction process by:
- Reading URLs from user input
- Coordinating the extraction process across modules
- Managing concurrency to process multiple URLs efficiently
- Displaying results and saving them to a file

### Spider Module (spider.py)

Handles web crawling and basic email extraction:
- Extracts links from HTML content
- Parses web pages for email addresses
- Crawls websites with depth and page limits

### Email Parser Module (email_parser.py)

Responsible for email extraction and validation:
- Uses sophisticated regex patterns to extract emails
- Filters out false positives (e.g., image filenames)
- Includes special handling for "impressum" pages common in German-speaking regions
- Cleans and validates extracted email addresses

### HTTP Extractor Module (http_extractor.py)

Handles email extraction using standard HTTP requests:
- Makes optimized HTTP requests to target URLs
- Extracts emails from the page content
- Returns both extracted emails and the page HTML for further processing

### Playwright Extractor Module (playwright_extractor.py)

Provides advanced email extraction using browser automation:
- Uses Playwright to render JavaScript-heavy pages
- Extracts emails from dynamically loaded content
- Handles common obstacles like cookie banners and popups
- Extracts emails from JavaScript, onclick handlers, and data attributes
- Scrolls pages to load lazy-loaded content

### Contact Finder Module (contact_finder.py)

Specializes in locating contact pages on websites:
- Contains multilingual keywords for contact pages in all EU languages
- Finds contact links in website navigation
- Tries common contact URL patterns when direct links aren't found
- Adapts strategies based on the domain language (determined by TLD)

## Application Workflow

1. **Input Phase**:
   - User enters URLs one per line in the console
   - Empty line or "END" terminates input

2. **Processing Phase**:
   - URLs are processed asynchronously with controlled concurrency (10 at a time)
   - For each URL:
     a. Try HTTP extraction on the main page
     b. If no emails found, look for contact page links in the main page
     c. Check each contact page for emails
     d. If still no emails, try common contact URL patterns
     e. As a last resort, use Playwright for advanced extraction

3. **Output Phase**:
   - Display summary of results
   - Save unique emails to output.txt

## Extraction Strategy

The application employs a multi-layered approach to maximize email discovery:

1. **Standard HTTP Request** (fastest, lowest resource usage)
   - Extracts emails from the main page HTML

2. **Contact Page Discovery** (if main page extraction fails)
   - Intelligently finds contact page links in the main page
   - Checks impressum pages for German websites
   - Tries common contact URL patterns based on domain language

3. **Advanced Extraction** (last resort, highest resource usage)
   - Uses Playwright browser automation
   - Handles JavaScript-rendered content
   - Extracts emails from dynamic page elements
   - Processes onclick handlers and data attributes

## Usage Instructions

1. Run the application:
   ```
   python email_extractor.py
   ```

2. Enter URLs one per line:
   ```
   example.com
   another-website.com
   third-site.net
   ```

3. Submit an empty line or type "END" to start processing

4. The application will process the URLs and display results
   
5. Extracted emails will be saved to `output.txt`

## Email Validation

The application employs sophisticated email validation to:
- Match standard email patterns
- Exclude common false positives (like image filenames)
- Filter out example/placeholder emails
- Ensure proper domain structure

## Optimization Features

- Asynchronous processing with controlled concurrency
- Progressive extraction techniques (from simple to complex)
- Early termination when emails are found to minimize resource usage
- Language-specific optimizations based on domain TLD
- Timeout controls to avoid hanging on problematic sites 