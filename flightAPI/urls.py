from django.urls import path
from . import views

urlpatterns = [
    path('flight-average/', views.calculate_flight_price_average),
]