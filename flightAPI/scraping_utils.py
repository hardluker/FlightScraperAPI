# flightapi/scraping_utils.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from bs4 import BeautifulSoup
import numpy as np
import re
import json
from datetime import datetime
import time

# Function for defining the driver for scraping Chrome
def get_driver():
    # Adding options to the chrome driver for optimization
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument('--private')
    options.add_argument("--log-level=1")
    options.add_argument('--disable-software-rasterizer')
    options.add_argument("--incognito")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")

    #Disable several unnecessary preferences
    prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2, 'javascript': 2, 
                            'plugins': 2, 'popups': 2, 'geolocation': 2, 
                            'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 
                            'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 
                            'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2, 
                            'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
                            'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 
                            'durable_storage': 2}}
    options.add_experimental_option('prefs', prefs)
    

    #Defining the path of the chrome driver if needed pass the argument in the driver service=service
    chromedriver_path = '/usr/bin/chromedriver'
    service = Service(chromedriver_path)

    # Declaring the driver and returning it
    driver = webdriver.Chrome(options=options)
    return driver

# Function for defining Firefox driver
def get_driver2():
   ## get the Firefox profile object
    profile = webdriver.FirefoxOptions()
    profile.set_preference('permissions.default.stylesheet', 2)
    ## Disable images
    profile.set_preference('permissions.default.image', 2)
    ## Disable Flash
    profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                  'false')
    profile.set_preference("network.http.pipelining", True)
    profile.set_preference("network.http.proxy.pipelining", True)
    profile.set_preference("network.http.pipelining.maxrequests", 8)
    profile.set_preference("content.notify.interval", 500000)
    profile.set_preference("content.notify.ontimer", True)
    profile.set_preference("content.switch.threshold", 250000)
    profile.set_preference("browser.cache.memory.capacity", 65536) # Increase the cache capacity.
    profile.set_preference("browser.startup.homepage", "about:blank")
    profile.set_preference("reader.parse-on-load.enabled", False) # Disable reader, we won't need that.
    profile.set_preference("browser.pocket.enabled", False) # Duck pocket too!
    profile.set_preference("loop.enabled", False)
    profile.set_preference("browser.chrome.toolbar_style", 1) # Text on Toolbar instead of icons
    profile.set_preference("browser.display.show_image_placeholders", False) # Don't show thumbnails on not loaded images.
    profile.set_preference("browser.display.use_document_colors", False) # Don't show document colors.
    profile.set_preference("browser.display.use_document_fonts", 0) # Don't load document fonts.
    profile.set_preference("browser.display.use_system_colors", True) # Use system colors.
    profile.set_preference("browser.formfill.enable", False) # Autofill on forms disabled.
    profile.set_preference("browser.helperApps.deleteTempFileOnExit", True) # Delete temprorary files.
    profile.set_preference("browser.shell.checkDefaultBrowser", False)
    profile.set_preference("browser.startup.homepage", "about:blank")
    profile.set_preference("browser.startup.page", 0) # blank
    profile.set_preference("browser.tabs.forceHide", True) # Disable tabs, We won't need that.
    profile.set_preference("browser.urlbar.autoFill", False) # Disable autofill on URL bar.
    profile.set_preference("browser.urlbar.autocomplete.enabled", False) # Disable autocomplete on URL bar.
    profile.set_preference("browser.urlbar.showPopup", False) # Disable list of URLs when typing on URL bar.
    profile.set_preference("browser.urlbar.showSearch", False) # Disable search bar.
    profile.set_preference("extensions.checkCompatibility", False) # Addon update disabled
    profile.set_preference("extensions.checkUpdateSecurity", False)
    profile.set_preference("extensions.update.autoUpdateEnabled", False)
    profile.set_preference("extensions.update.enabled", False)
    profile.set_preference("general.startup.browser", False)
    profile.set_preference("plugin.default_plugin_disabled", False)
    profile.set_preference("permissions.default.image", 2) # Image load disabled again
    driver = webdriver.Firefox(profile)
    
    return driver

# Function for trying the scrapes multiple times in case there is an issue in the web page loading
def attempt_scrape(scrapeFunction, request_data, retries=3, delay=0.1):
    for attempt in range(retries):
        try:
            return scrapeFunction(request_data)
        except Exception as e:
            if attempt < retries - 1:
                print(f"Failed, trying again in {delay} seconds")
                time.sleep(delay)
            else:
                raise Exception(str(e))

# Function to scrape flight data
def find_flight_prices(flight_info):
    driver = get_driver()

    dep = flight_info['Departure']
    arr = flight_info['Arrival']
    date = flight_info['Date']
    airline_code = "DL" if flight_info['Airline'].lower() == "delta" else "AA"

    url = f"https://www.kayak.com/flights/{dep}-{arr}/{date}?sort=bestflight_a&fs=airlines={airline_code}"

    driver.get(url)

    try:
        # Wait for the price elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(text(), '$')]"))
        )

        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract all elements with class names containing 'price-text' or similar patterns
        price_elements = soup.find_all(lambda tag: tag.name == 'div' and re.match(r'\$\d+', tag.get_text()))
        prices = []

        # Extract numeric value from price text and calculate the average
        for element in price_elements:
            price_text = element.get_text(strip=True)
            # Match the first occurrence of a price pattern like $123
            match = re.search(r'\$\d+', price_text)
            if match:
                price = float(re.sub(r'[^\d.]', '', match.group()))
                prices.append(price)

        filtered_prices = remove_outliers(prices)
        average_price = np.mean(filtered_prices)
        return average_price

    except TimeoutException as e:
        raise Exception("Loading took too much time!") from e

    finally:
        driver.quit()

# Function for scraping car rental prices
def find_car_rental_prices(car_rental_info):
    driver = get_driver()

    start_airport = car_rental_info['StartAirport']
    end_airport = car_rental_info['EndAirport']
    start_date = car_rental_info['StartDate']
    end_date = car_rental_info['EndDate']

    url = f"https://www.kayak.com/cars/{start_airport}/{end_airport}/{start_date}/{end_date}?sort=rank_a"

    driver.get(url)

    try:
        # Wait for the price elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(text(), '$')]"))
        )

        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract all elements that contain a dollar sign
        price_elements = soup.find_all(lambda tag: tag.name == 'div' and re.match(r'\$\d+', tag.get_text()))
        prices = []

        # Extract numeric value from price text and calculate the average
        for element in price_elements:
            price_text = element.get_text(strip=True)
            # Match the first occurrence of a price pattern like $123
            match = re.search(r'\$\d+', price_text)
            if match:
                price = float(re.sub(r'[^\d.]', '', match.group()))
                prices.append(price)

        if not prices:
            raise Exception("No prices found on the page.")

        prices.sort()
        filtered_prices = remove_outliers(prices)
        average_price = np.mean(filtered_prices)
        return average_price

    except TimeoutException as e:
        raise Exception("Loading took too much time!") from e

    finally:
        driver.quit()

# Function to scrape hotel prices
def find_hotel_prices(hotel_info):
    
    driver = get_driver()

    city = hotel_info['City']
    state = hotel_info['State']
    start_date = hotel_info['StartDate']
    end_date = hotel_info['EndDate']
    nights = calculate_nights(start_date, end_date)

    url = f"https://www.kayak.com/hotels/{city},{state}/{start_date}/{end_date}/"

    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(text(), '$')]"))
        )
            
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        price_elements = soup.find_all(lambda tag: tag.name == 'div' and re.match(r'\$\d+', tag.get_text()))
        prices = []

        for element in price_elements:
            price_text = element.get_text(strip=True)
            match = re.search(r'\$\d+', price_text)
            if match:
                nightly_price = float(re.sub(r'[^\d.]', '', match.group()))
                total_price = nightly_price * nights
                prices.append(total_price)

        if not prices:
            raise Exception("No prices found on the page.")

        filtered_prices = remove_outliers(prices)
        average_price = np.mean(filtered_prices)
        return average_price

    except TimeoutException:
            raise Exception("Loading took too much time after multiple attempts!")
    finally:
        driver.quit()


# The interquartile method for removing extreme outliers in datasets.
def remove_outliers(data):
    data = np.array(data)
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
    return filtered_data.tolist()

# Calculate the number of nights between two dates
def calculate_nights(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    nights = (end - start).days
    return nights
