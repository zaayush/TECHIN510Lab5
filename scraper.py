import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from dp import get_db_conn

# Load environment variables from .env file
load_dotenv()

def extract(page):
    url = f'https://visitseattle.org/events/page/{page}'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup

def extract_event_urls(soup):
    selector = "div.search-result-preview > div > h3 > a"
    a_eles = soup.select(selector)
    return [x['href'] for x in a_eles]

def extract_event_details(event_url):
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extracting details
    name = soup.find('h1', class_='page-title').text.strip()
    date = soup.find("h4").find_all("span")[0].text.strip()
    location = soup.find("h4").find_all("span")[1].text.strip()
    event_type = soup.find_all("a", class_="button big medium black category")[0].text.strip()
    region = soup.find_all("a", class_="button big medium black category")[1].text.strip()
    
    return [name, date, location, event_type, region]

# Extract event URLs
event_data = []
for page in range(0, 2):
    print(f'Getting page {page}...')
    soup = extract(page)
    event_urls = extract_event_urls(soup)
    for event_url in event_urls:
        data = extract_event_details(event_url)
        event_data.append(data)

# Use OpenStreetMap API to get latitude and longitude for locations
for data in event_data:
    region_name = data[4].split('/')[0].strip()  # Extract the first name before the '/'
    region_name = f"{region_name}, Seattle"  # Append ", Seattle"
    base_url = "https://nominatim.openstreetmap.org/search.php"
    query_params = {
        "q": region_name,
        "format": "jsonv2"
    }
    res = requests.get(base_url, params=query_params)
    location_data = res.json()
    if location_data:
        latitude = location_data[0]['lat']
        longitude = location_data[0]['lon']
        data.extend([latitude, longitude])
    else:
        data.extend([None, None])

# Step 4: Look up the weather
weather_api_url = "https://api.weather.gov/points/{},{}"
for data in event_data:
    if data[-2] is not None and data[-1] is not None:
        weather_url = weather_api_url.format(data[-2], data[-1])
        response = requests.get(weather_url)
        if response.status_code == 200:
            point_dict = response.json()
            forcast_url = point_dict['properties']['forecast']
            res = requests.get(forcast_url)
            weather_data = res.json()
            if 'properties' in weather_data and 'periods' in weather_data['properties']:
                forecast = weather_data['properties']['periods'][0]
                detailed_forecast = forecast['detailedForecast']
                temperature_min = forecast['temperatureMin']
                temperature_max = forecast['temperatureMax']
                windchill = forecast['windChill']
                data.extend([detailed_forecast, temperature_min, temperature_max, windchill])
            else:
                data.extend(["Weather data not available"] * 4)
        else:
            data.extend(["Weather data not available"] * 4)
    else:
        data.extend(["Weather data not available"] * 4)

# Store data in the Azure PostgreSQL database
conn = get_db_conn()
cursor = conn.cursor()
for data in event_data:
    # Use INSERT INTO ... ON CONFLICT DO NOTHING to ensure only unique data is inserted
    cursor.execute("""
        INSERT INTO events (name, date, location, event_type, region, latitude, longitude, weather_forecast, temperature_min, temperature_max, windchill) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        ON CONFLICT (name, date, location) DO NOTHING
    """, data)

# Commit the transaction and close the cursor and connection
conn.commit()
cursor.close()
conn.close()

print("Data has been successfully written to the Azure PostgreSQL database.")
