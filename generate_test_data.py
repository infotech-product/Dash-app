import csv
import random
from datetime import datetime, timedelta
import numpy as np

# Configuration
NUM_ROWS = 5000  # Number of log entries to generate
OUTPUT_FILE = "web_server_logs.csv"

# Data pools with continent mapping
COUNTRIES_WITH_CONTINENTS = {
    "United States": "North America",
    "China": "Asia", 
    "India": "Asia",
    "Brazil": "South America",
    "Germany": "Europe",
    "United Kingdom": "Europe",
    "France": "Europe",
    "Japan": "Asia",
    "Nigeria": "Africa",
    "South Africa": "Africa",
    "Kenya": "Africa",
    "Egypt": "Africa",
    "Australia": "Oceania",
    "Canada": "North America",
    "Mexico": "North America",
    "Argentina": "South America",
    "Russia": "Europe",
    "South Korea": "Asia",
    "Singapore": "Asia",
    "United Arab Emirates": "Asia"
}

COUNTRIES = list(COUNTRIES_WITH_CONTINENTS.keys())

URL_CATEGORIES = {
    "Generic": ["/index.html", "/about.html", "/contact.html", "/privacy.html"],
    "Job": ["/job/apply", "/job/view/{}", "/job/list", "/job/details/{}"],
    "Demo": ["/scheduledemo.php", "/demo/request", "/demo/signup"],
    "Event": ["/events.php", "/events/upcoming", "/events/past"],
    "AI": ["/virtualassistant.php", "/ai/help", "/ai/info"],
    "Prototype": ["/prototype.php", "/prototype/info", "/prototype/signup"],
    "Product": ["/product/{}", "/products/list", "/product/details/{}"],
    "Blog": ["/blog/{}", "/blog/latest", "/blog/category/tech"]
}

PRODUCT_NAMES = ["analytics", "dashboard", "api", "mobile", "enterprise", "cloud"]
BLOG_TITLES = ["getting-started", "new-features", "case-study", "tutorial"]

METHODS = ["GET", "POST", "PUT", "DELETE"]
METHOD_WEIGHTS = [0.85, 0.12, 0.02, 0.01]  # GET most common

STATUS_CODES = [200, 302, 304, 400, 404, 500]
STATUS_WEIGHTS = [0.75, 0.15, 0.05, 0.02, 0.02, 0.01]

# Helper functions
def random_time():
    """Generate random time in HH:MM:SS format"""
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def random_ip():
    """Generate random IPv4 address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def random_url():
    """Generate random URL with proper request type mapping"""
    category = random.choices(
        list(URL_CATEGORIES.keys()),
        weights=[0.2, 0.15, 0.1, 0.1, 0.1, 0.1, 0.15, 0.1]
    )[0]
    
    base_url = random.choice(URL_CATEGORIES[category])
    
    if "{}" in base_url:
        if category == "Job":
            base_url = base_url.format(random.randint(1000, 9999))
        elif category == "Product":
            base_url = base_url.format(random.choice(PRODUCT_NAMES))
        elif category == "Blog":
            base_url = base_url.format(random.choice(BLOG_TITLES))
    
    return category, base_url

def get_request_type(category, url):
    """Map URL category to request type"""
    mapping = {
        "Generic": None,
        "Job": "Job Application" if "apply" in url else "Job View",
        "Demo": "Demo Request",
        "Event": "Event Inquiry",
        "AI": "AI Assistant Inquiry",
        "Prototype": "Prototype Info",
        "Product": "Product View",
        "Blog": "Blog Post View"
    }
    return mapping[category]

def get_continent(country):
    """Get continent for a given country"""
    return COUNTRIES_WITH_CONTINENTS[country]

# Generate data
data = []
for _ in range(NUM_ROWS):
    # Generate timestamp within last 30 days
    time = random_time()
    
    # Generate IP
    ip = random_ip()
    
    # Generate method
    method = random.choices(METHODS, weights=METHOD_WEIGHTS)[0]
    
    # Generate URL and request type
    category, url = random_url()
    request_type = get_request_type(category, url)
    
    # Generate status code
    status_code = random.choices(STATUS_CODES, weights=STATUS_WEIGHTS)[0]
    
    # Generate country and get its continent
    country = random.choice(COUNTRIES)
    continent = get_continent(country)
    
    data.append([
        time, ip, method, url, status_code, request_type, country, continent
    ])

# Write to CSV with error handling
try:
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Time", "IP Address", "Method", "URL/Path", 
            "Status Code", "Request Type", "Country", "Continent"
        ])
        writer.writerows(data)
    
    print(f"Generated {NUM_ROWS} log entries in {OUTPUT_FILE}")
    print(f"Countries by continent:")
    for continent in sorted(set(COUNTRIES_WITH_CONTINENTS.values())):
        countries_in_continent = [country for country, cont in COUNTRIES_WITH_CONTINENTS.items() if cont == continent]
        print(f"  {continent}: {len(countries_in_continent)} countries")

except PermissionError:
    print(f"Permission denied: Cannot write to '{OUTPUT_FILE}'")
    print("Possible solutions:")
    print("1. Close the file if it's open in Excel or another program")
    print("2. Run the script as administrator")
    print("3. Try a different filename or location")
    
    # Try alternative filename
    import os
    base_name = os.path.splitext(OUTPUT_FILE)[0]
    extension = os.path.splitext(OUTPUT_FILE)[1]
    counter = 1
    
    while True:
        alt_filename = f"{base_name}_{counter}{extension}"
        try:
            with open(alt_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Time", "IP Address", "Method", "URL/Path", 
                    "Status Code", "Request Type", "Country", "Continent"
                ])
                writer.writerows(data)
            print(f"Successfully created alternative file: {alt_filename}")
            break
        except PermissionError:
            counter += 1
            if counter > 10:
                print("Unable to create file with alternative names. Please check permissions.")
                break