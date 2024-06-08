from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render

# flightapi/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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


@api_view(['POST'])
def calculate_flight_price_average(request):
    try:
        # Parse the JSON data from the request body
        flight_data = json.loads(request.body)
            
        # Call the function to scrape flight prices
        average_price = find_flight_prices(flight_data)
            
        # Return the result as JSON
        return JsonResponse({'average_price': average_price})
    except Exception as e:
        # Return error message if something went wrong
        return JsonResponse({'error': str(e)}, status=400)

def find_flight_prices(flight_info):
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Specify the path to chromedriver executable
    chromedriver_path = '/usr/bin/chromedriver'
    
    # Set the path to the chromedriver executable
    service = Service(chromedriver_path)
    
    driver = webdriver.Chrome(options=options)

    dep = flight_info['Departure']
    arr = flight_info['Arrival']
    date = flight_info['Date']
    airline_code = "DL" if flight_info['Airline'].lower() == "delta" else "AA"

    url = f"https://www.kayak.com/flights/{dep}-{arr}/{date}?sort=bestflight_a&fs=airlines={airline_code}"

    driver.get(url)

    try:
        # Wait for the price elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'price-text')]"))
        )

        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract all elements with class names containing 'price-text' or similar patterns
        price_elements = soup.find_all(lambda tag: tag.name == 'div' and re.search(r'price-text', ' '.join(tag.get('class', []))))
        prices = []

        # Extract numeric value from price text and calculate the average
        for element in price_elements:
            price_text = element.get_text(strip=True)
            price = float(re.sub(r'[^\d.]', '', price_text))
            prices.append(price)

        average_price = np.mean(prices)
        return average_price

    except TimeoutException as e:
        raise Exception("Loading took too much time!") from e

    finally:
        driver.quit()


