from rest_framework.response import Response
from rest_framework.decorators import api_view

# flightapi/views.py
from django.http import JsonResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import numpy as np
import re
import json
from datetime import datetime
import time

# Post request for getting flight prices
@api_view(['POST'])
def calculate_flight_price_average(request):
    try:
        # Parse the JSON data from the request body
        flight_data = json.loads(request.body)
            
        # Call the function to scrape flight prices
        average_price = attempt_scrape(find_flight_prices, flight_data)
            
        # Return the result as JSON
        return JsonResponse({'average_price': average_price})
    except Exception as e:
        # Return error message if something went wrong
        return JsonResponse({'error': str(e)}, status=400)


# Post request for getting the average rental car price
@api_view(['POST'])
def calculate_car_rental_price_average(request):
    try:
        # Parse the JSON data from the request body
        car_rental_data = json.loads(request.body)
            
        # Call the function to scrape car rental prices
        average_price = attempt_scrape(find_car_rental_prices, car_rental_data,)
            
        # Return the result as JSON
        return JsonResponse({'average_price': average_price})
    except Exception as e:
        # Return error message if something went wrong
        return JsonResponse({'error': str(e)}, status=400)


# Post request for getting hotel prices
@api_view(['POST'])
def calculate_hotel_price_average(request):
    try:
        hotel_data = json.loads(request.body)
        average_price = attempt_scrape(find_hotel_prices, hotel_data)
        return JsonResponse({'average_price': average_price})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




####### Everything Here needs to be Abstracted into a new file #########

# Function for trying the scrapes multiple times in case there is an issue in the web page loading
def attempt_scrape(scrapeFunction, request_data, retries=3, delay=1):
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

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=1")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    chromedriver_path = '/usr/bin/chromedriver'
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(options=options)
    return driver


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

