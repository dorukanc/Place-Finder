import os
import threading
import csv
import requests

# Import API KEY from .env

API_URL = 'https://places.googleapis.com/v1/places:searchText'
API_KEY = os.getenv('API_KEY')

# Import delete_file_after_delay, import get_location_bounds

from search_functions.delete_file_after_delay import delete_file_after_delay
from search_functions.get_location_bounds import get_location_bounds

def process_specific_location_queries(query_file_path, location_code, categories, results_file_path, use_deep_search=False):
    try:
        with open(query_file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()

        results = []
        for query in queries:
            places = search_places(query.strip(), location_code, categories)
            for place in places:
                place_info = {
                    'name': place['displayName']['text'],
                    'address': place['formattedAddress'],
                    'phone': place.get('internationalPhoneNumber', 'N/A'),
                    'website': place.get('websiteUri', 'N/A')
                }
                results.append(place_info)

        save_to_csv(results, results_file_path)
    except Exception as e:
        print(f"Error processing specific location queries: {e}")
    finally:
        if os.path.exists(query_file_path):
            os.remove(query_file_path)
            print(f"Deleted query file: {query_file_path}")
        
        threading.Thread(target=delete_file_after_delay, args=(results_file_path,)).start()

def search_places(query, location_code, categories, page_size=20, location_restriction=None):
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,nextPageToken'
    }
    
    if location_code and not location_restriction:
        bounds = get_location_bounds(location_code)
        if bounds:
            location_restriction = {
                'rectangle': {
                    'low': {
                        'latitude': bounds['southwest']['lat'],
                        'longitude': bounds['southwest']['lng']
                    },
                    'high': {
                        'latitude': bounds['northeast']['lat'],
                        'longitude': bounds['northeast']['lng']
                    }
                }
        }
    
    all_places = []
    page_token = None
    
    while True:
        data = {
            'textQuery': query,
            'maxResultCount': page_size,
            'locationRestriction': location_restriction,
            'includedType' : categories
        }
        if page_token:
            data['pageToken'] = page_token
        
        try:
            response = requests.post(API_URL, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            all_places.extend(result.get('places', []))
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            break
    
    return all_places

def save_to_csv(data, file_path):
    """Saves the data to a CSV file."""
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Address', 'Phone', 'Website'])
        for row in data:
            writer.writerow([row['name'], row['address'], row.get('phone', 'N/A'), row.get('website', 'N/A')])
