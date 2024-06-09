# Backend Webscraper

## How does it work?

This webscraper utilizes Selenium, BeautifulSoup, Kayak.com, and Probability and statistics principles.
It is capable of gathering the average cost of flights, car rentals, and hotel prices.

The webscraping is robust and dynamic in that is simply searches for elements that contain "$" followed by numbers.
Next, it will filter out useless data. Finally, it will use the interquartile range method to elimnate obscure outliers.
Finally, it calculates the average of all the prices it scrapes.

## Http Requests

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
