from django.urls import path
from . import views

urlpatterns = [
    path('flight-average/', views.calculate_flight_price_average),
    path('car-average/', views.calculate_car_rental_price_average)
]