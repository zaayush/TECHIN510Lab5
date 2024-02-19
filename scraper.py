import os
import requests
from bs4 import BeautifulSoup
from db import get_db_conn
import csv
import os
import re

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
    
    date = re.sub(r'^Now through\s+', '', date)
    date = re.sub(r'^.*through\s+', '', date)
    return [name, date, location, event_type, region]

# Extract event URLs
event_data = []
for page in range(0, 10):
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
            # print (weather_data)
            if 'properties' in weather_data and 'periods' in weather_data['properties']:
                forecast = weather_data['properties']['periods'][0]
                detailed_forecast = forecast['detailedForecast']
                temperature = forecast['temperature']
                windSpeed = forecast['windSpeed']
                data.extend([detailed_forecast, temperature, windSpeed])
            else:
                data.extend(["Weather data not available"] * 4)
        else:
            data.extend(["Weather data not available"] * 4)
    else:
        data.extend(["Weather data not available"] * 4)

        

# Save data to a CSV file
csv_file = os.path.join(os.getcwd(), 'output.csv')
header = ['name', 'date', 'location', 'event_type', 'region', 'latitude', 'longitude', 'weather_forecast', 'temperature', 'windSpeed']

with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(event_data)

print("Data has been successfully written to the CSV file.")

# Store data in the Azure PostgreSQL database
conn = get_db_conn()
cursor = conn.cursor()

# Store data in the Azure PostgreSQL database
conn = get_db_conn()
cursor = conn.cursor()

# Create the 'events' table if it does not exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        name TEXT,
        date TEXT,
        location TEXT,
        event_type TEXT,
        region TEXT,
        latitude FLOAT,
        longitude FLOAT,
        weather_forecast TEXT,
        temperature FLOAT,
        windSpeed FLOAT
    )
""")

# Insert data into the 'events' table
for data in event_data:
    # Extract the numerical part of the windSpeed string
    wind_speed_str = data[-1]  # Assuming windSpeed is the last element in the data list
    wind_speed_numeric = None
    try:
        wind_speed_numeric = float(wind_speed_str.split()[0])  # Extracting the numeric part
    except (ValueError, IndexError):
        pass  # Handle cases where windSpeed is not properly formatted

    # Use INSERT INTO ... ON CONFLICT DO NOTHING to ensure only unique data is inserted
    cursor.execute("""
        INSERT INTO events (name, date, location, event_type, region, latitude, longitude, weather_forecast, temperature, windSpeed) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
    """, data[:-1] + [wind_speed_numeric])  # Exclude the last element (windSpeed) and append the numeric windSpeed

# Commit the transaction and close the cursor and connection
conn.commit()
cursor.close()
conn.close()

print("Data has been successfully written to the Azure PostgreSQL database.")
