import pandas as pd
import numpy as np
import requests
from sqlalchemy import create_engine, String, Float, DateTime, Integer
from datetime import timedelta
import time
import random

engine = create_engine('postgresql://postgres:postgres@10.17.117.5:5432/ufo')


def load_sigthings(filename):
    df = pd.read_csv(filename)

    df.columns = ['city', 'state', 'country', 'shape', 'duration', 'description', 'lat', 'lng', 'sighted_year', 'sighted_month', 'sighted_day', 'sigthed_hour', 'sighted_minute', 'reported_year', 'reported_month', 'reported_day']

    df.rename(columns={'sighted_year': 'year', 'sighted_month': 'month', 'sighted_day': 'day', 'sigthed_hour': 'hour', 'sighted_minute': 'minute'}, inplace=True)

    df["sigthed_date"] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']])

    df = df.drop(['year', 'month', 'day', 'hour', 'minute'], axis=1)

    df.rename(columns={'reported_year': 'year', 'reported_month': 'month', 'reported_day': 'day'}, inplace=True)

    df["reported_date"] = pd.to_datetime(df[['year', 'month', 'day']])

    df = df.drop(['year', 'month', 'day'], axis=1)

    df_schema = {
        'index': Integer(),
        'city': String(255),
        'state': String(255),
        'country': String(255),
        'shape': String(255),
        'duration': Integer(),
        'description': String(255),
        'lat': Float(),
        'lng': Float(),
        'sigthed_date': DateTime(),
        'reported_date': DateTime(),
    }

    df.to_sql('ufo_sightings', engine, if_exists='replace', index=True, dtype=df_schema)

    return df


def label_wmo(code):
    if code == 0:
        return "Clear sky"
    elif code in [1, 2, 3]:
        return "Cloudy"
    elif code in [45, 48]:
        return "Foggy"
    elif code in [51, 53, 55]:
        return "Drizzle"
    elif code in [56, 57]:
        return "Freezing Drizzle"
    elif code in [61, 63, 65]:
        return "Rain"
    elif code in [66, 67]:
        return "Freezing Rain"
    elif code in [71, 73, 75]:
        return "Snow"
    elif code == 77:
        return "Snow grains"
    elif code in [80, 81, 82]:
        return "Rain showers"
    elif code in [85, 86]:
        return "Snow showers"
    elif code == 95:
        return "Thunderstorm"
    elif code in [96, 99]:
        return "Thunderstorm with hail"


def fetch_weather(ufo_id, date, lat, lng):
    hour = date.hour
    weather_api = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        'latitude': lat,
        'longitude': lng,
        'start_date': date.strftime('%Y-%m-%d'),
        'end_date': date.strftime('%Y-%m-%d'),
        "hourly": ["weathercode"],
    }

    response = requests.get(weather_api, params=params)
    if response.status_code == 200:
        data = response.json()
        weathercode = int(data.get('hourly', {}).get('weathercode', [])[hour])
        label = label_wmo(data.get('hourly', {}).get('weathercode', [])[hour])
        elevation = data.get('elevation', 0)
        print(f"Fetching weather for {ufo_id} at {date}")
        print(f"weathercode: {weathercode}")
        print("=====================================")
        return date, weathercode, label, elevation, ufo_id
    else:
        return None


def load_weather():
    query = """
        SELECT ufo_sightings.index, ufo_sightings.sigthed_date, ufo_sightings.lat, ufo_sightings.lng
        FROM ufo_sightings
        LEFT OUTER JOIN weather ON ufo_sightings.sigthed_date = weather.date
                    AND ufo_sightings.lat = weather.latitude
                    AND ufo_sightings.lng = weather.longitude
        WHERE weather.date is null AND ufo_sightings.sigthed_date > '1940-01-01';
    """
    df = pd.read_sql_query(query, engine)

    errors = []
    chunks = np.array_split(df, int(len(df) / 50))

    for i in range(len(chunks)):
        # for i in arr:
        chunk = chunks[i]
        print(f"Processing chunk {i}")
        # print(len(chunk))
        # time.sleep(100)
        time.sleep(random.randint(3, 7))

        params = {
            'latitude': [],
            'longitude': [],
            'start_date': [],
            'end_date': [],
            'hourly': ["weathercode"],
            'hours': [],
            'date': []
        }

        for index, row in chunk.iterrows():
            params['latitude'].append(row['lat'])
            params['longitude'].append(row['lng'])
            params['start_date'].append(row['sigthed_date'].strftime('%Y-%m-%d'))
            params['end_date'].append(row['sigthed_date'].strftime('%Y-%m-%d'))

            params['hours'].append(row['sigthed_date'].hour)
            params['date'].append(row['sigthed_date'])

        response = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
            'latitude': params['latitude'],
            'longitude': params['longitude'],
            'start_date': params['start_date'],
            'end_date': params['end_date'],
            'hourly': params['hourly'],
        })

        if response.status_code == 200:
            weather_data = []
            data = response.json()
            for index, row in enumerate(data):
                date = params['date'][index]
                latitude = params['latitude'][index]
                longitude = params['longitude'][index]
                hour = params['hours'][index]
                weathercode = int(row.get('hourly', {}).get('weathercode', [])[hour])
                label = label_wmo(row.get('hourly', {}).get('weathercode', [])[hour])
                elevation = row.get('elevation', 0)
                weather_data.append((date, latitude, longitude, weathercode, label, elevation))
            weather_data = pd.DataFrame(weather_data, columns=['date', 'latitude', 'longitude', 'weathercode', 'label', 'elevation'])
            weather_data.to_sql('weather', engine, if_exists='append', index=False)
        else:
            print(f"Error fetching weather for chunk {i}")
            print(f'Error code: {response.status_code}')
            print(response.text)
            errors.append(i)
            print(errors)

    # weather_data = df.apply(lambda row: fetch_weather(row['index'], row['sigthed_date'], row['lat'], row['lng']), axis=1)
# [339, 356]
#


if __name__ == "__main__":
    # load_sigthings("ufo_sightings.csv")
    load_weather()
