from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
import json
from .scraping_utils import attempt_scrape, find_flight_prices, find_car_rental_prices, find_hotel_prices

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
        average_price = attempt_scrape(find_car_rental_prices, car_rental_data)
            
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
