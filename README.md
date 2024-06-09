# Backend Webscraper API

## How does it work?

This webscraper utilizes Selenium, BeautifulSoup, and Probability and statistics principles.
It is capable of gathering the average cost of flights, car rentals, and hotel prices.

The webscraping is robust and dynamic in that is simply searches for elements that contain "$" followed by numbers.
Next, it will filter out useless data. Finally, it will use the interquartile range method to eliminate obscure outliers.
Finally, it calculates the average of all the prices it scrapes.

The purpose of this tool is the calculate the average cost of travel. This can be used in a business application where travel is a significant part of the business.

## Http Requests

All HTTP requests return the average total price.

### POST http://<SERVER_ADDRESS>/api/flight-average/

This will return the average flights cost for a one-way trip. Currently it only supports Delta and American Airlines flights.
If the Airline attribute is not "Delta" it will otherwise calculate the average for American Airlines flights.

Example JSON Body:

```
{
    "Departure": "CAE",
    "Arrival": "BNA",
    "Date": "2024-08-09",
    "Airline": "Delta"
}
```

Example JSON Response:

```
{
    "average_price": 296.6808510638298
}
```

### POST http://<SERVER_ADDRESS>/api/car-average/

This will return the average car rental prices. It has the ability to support cars that are taken to a different airport.

Example JSON Body:

```
{
    "StartAirport": "BNA",
    "EndAirport": "BNA",
    "StartDate": "2024-08-09",
    "EndDate": "2024-08-10"
}
```

Example JSON Response:

```
{
    "average_price": 122.45283018867924
}
```

### POST http://<SERVER_ADDRESS>/api/hotel-average/

This will return the average cost of hotels. If the name of the state or city has spaces, you need to separate it with a "-".

Example JSON Body:

```
{
    "City": "batesburg-leesville",
    "State": "South-Carolina",
    "StartDate": "2024-08-09",
    "EndDate": "2024-08-10"
}
```

Example JSON Response:

```
{
    "average_price": 65.0
}
```
