# import the library
import googlemaps
import json
import pprint
import xlsxwriter
import time
import pandas as pd
import os
from datetime import datetime
import sqlite3
os.chdir('/Users/oanottage/Desktop/BTS/Data Science Foundations/DSFinal/')

# Define the API Key.
API_KEY = 'AIzaSyA-65Zhblpb0zTW61RaC1SLA9OwVUYU8bc'
# Define the Client
gmaps = googlemaps.Client(key=API_KEY)

categories = ['accounting', 'airport', 'amusement_park', 'aquarium', 'art_gallery', 'atm', 'bakery', 'bank', 'bar', 'beauty_salon', 'bicycle_store', 'book_store', 'bowling_alley', 'bus_station', 'cafe', 'campground', 'car_dealer', 'car_rental', 'car_repair', 'car_wash', 'casino', 'cemetery', 'church', 'city_hall', 'clothing_store', 'convenience_store', 'courthouse', 'dentist', 'department_store', 'doctor', 'drugstore', 'electrician', 'electronics_store', 'embassy', 'fire_station', 'florist', 'funeral_home', 'furniture_store', 'gas_station', 'gym', 'hair_care', 'hardware_store', 'hindu_temple', 'home_goods_store', 'hospital', 'insurance_agency', 'jewelry_store', 'laundry', 'lawyer',
              'library', 'light_rail_station', 'liquor_store', 'local_government_office', 'locksmith', 'lodging', 'meal_delivery', 'meal_takeaway', 'mosque', 'movie_rental', 'movie_theater', 'moving_company', 'museum', 'night_club', 'painter', 'park', 'parking', 'pet_store', 'pharmacy', 'physiotherapist', 'plumber', 'police', 'post_office', 'primary_school', 'real_estate_agency', 'restaurant', 'roofing_contractor', 'rv_park', 'school', 'secondary_school', 'shoe_store', 'shopping_mall', 'spa', 'stadium', 'storage', 'store', 'subway_station', 'supermarket', 'synagogue', 'taxi_stand', 'tourist_attraction', 'train_station', 'transit_station', 'travel_agency', 'university', 'veterinary_care', 'zoo']

stored_results = []

for category in categories:
    try:
        places_result = gmaps.places_nearby(
            location='41.397447, 2.164331', radius=50000, type=str(category))
        for _ in range(150):
            # loop through each of the places in the results, and get the place details.
            for place in places_result['results']:
                # define the place id, needed to get place details. Formatted as a string.
                my_place_id = place['place_id']
                # define the fields you would liked return. Formatted as a list.
                my_fields = ['place_id', 'url', 'name', 'formatted_phone_number', 'international_phone_number', 'type', 'rating', 'user_ratings_total',
                             'geometry/location/lng', 'geometry/location/lat', 'website', 'opening_hours', 'price_level', 'business_status', 'permanently_closed']
                # make a request for the details.
                places_details = gmaps.place(
                    place_id=my_place_id, fields=my_fields)
                # store the results in a list object.
                stored_results.append({'category': category})
                stored_results.append(places_details['result'])
            time.sleep(3)
            places_result = gmaps.places_nearby(
                page_token=places_result['next_page_token'])
    except:
        continue


# Convert the lead list into a Pandas DataFrame
raw = pd.DataFrame(stored_results)
raw['category'] = raw['category'].shift(1)

df = raw.copy()
df = df.dropna(how='all')
df = df.reset_index(drop=True)
df['coordinates'] = df['geometry'].apply(lambda x: x['location'])
df['latitude'] = df['coordinates'].apply(lambda x: x['lat'])
df['longitude'] = df['coordinates'].apply(lambda x: x['lng'])
df.drop(columns=['geometry', 'coordinates'], inplace=True)


today = datetime.today().date()

df.to_csv(
    'data/external/Google/lead_list_barcelona_{}.csv'.format(today), index=False)

df['TimeStamp'] = today

# Run the 'create if it doesn't exist' SQL statement


def create_db(folder, table_name, df):
    # Open a connection to the database and create a cursor
    cnx = sqlite3.connect('{}/DSFinal.db'.format(folder))
    c = cnx.cursor()

    # Get the column names and types from the dataframe
    cols = df.columns.tolist()
    types = df.dtypes.tolist()

    # Create the SQL CREATE TABLE statement
    create_statement = "CREATE TABLE IF NOT EXISTS {} ({})".format(
        table_name, ', '.join(['{} {}'.format(col, types) for col, types in zip(cols, types)]))

    # Execute the CREATE TABLE statement
    c.execute(create_statement)

    # Commit the changes and close the cursor and connection
    cnx.commit()


# Creating the table
def create_table(folder, table_name, df):
    cnx = sqlite3.connect('{}/DSFinal.db'.format(folder))
    c = cnx.cursor()
    # Get the list of column names and data types in the DataFrame
    cols = list(df.columns)
    types = df.dtypes.apply(lambda x: x.name).tolist()

    # Create the CREATE TABLE statement dynamically
    create_statement = "CREATE TABLE IF NOT EXISTS {} ({})".format(
        table_name, ', '.join(['{} {}'.format(col, types) for col, types in zip(cols, types)]))

    # Execute the CREATE TABLE statement
    c.execute(create_statement)
    # Commit the changes and close the cursor and connection
    cnx.commit()


# Dynamic Insertion
def dynamic_insertion(folder, table_name, df):
    cnx = sqlite3.connect('{}/DSFinal.db'.format(folder))
    c = cnx.cursor()
    # Get the list of column names in the DataFrame
    cols = list(df.columns)

    # Create the INSERT statement dynamically
    insert_statement = "INSERT INTO {}({}) VALUES ({})".format(
        table_name, ", ".join(cols), ", ".join(['?' for _ in range(len(cols))]))

    # Insert the data into the database
    for index, row in df.iterrows():
        c.execute(insert_statement, tuple(row))
        cnx.commit()

    # Close the database connection and cursor
    c.close()
    cnx.close()

# Putting it all together


def push(folder, table_name, df):
    create_db(folder, table_name, df)
    create_table(folder, table_name, df)
    dynamic_insertion(folder, table_name, df)


push('databases', 'gmaps_lead_list', df)
push('deliverables', 'gmaps_lead_list', df)
