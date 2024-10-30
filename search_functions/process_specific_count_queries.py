import os
import threading
import csv
import requests

# Import API KEY from .env

API_URL = 'https://places.googleapis.com/v1/places:searchText'
API_KEY = os.getenv('API_KEY')

# Import delete_file_after_delay, import get_location_bounds, import divide_bounding_box

from search_functions.delete_file_after_delay import delete_file_after_delay
from search_functions.get_location_bounds import get_location_bounds
from search_functions.divide_bounding_box import divide_bounding_box


def process_specific_location_count_queries(query_file_path, location_code, results_file_path, use_deep_search=False):
    try:
        with open(query_file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()

        results = []
        for query in queries:
            query = query.strip()
            count = count_locations_specific_location(query, location_code, use_deep_search)
            results.append({
                'place_name': query,
                'location': location_code,
                'count': count
            })

        save_specific_location_count_to_csv(results, results_file_path)
    except Exception as e:
        print(f"Error processing specific location count queries: {e}")
    finally:
        if os.path.exists(query_file_path):
            os.remove(query_file_path)
            print(f"Deleted query file: {query_file_path}")
        
        threading.Thread(target=delete_file_after_delay, args=(results_file_path,)).start()

# This function counts the locations and returns the total

def count_locations_specific_location(query, location_code, use_deep_search= False):
    if use_deep_search:
        count = deep_search_places(query, location_code)
    else:
        count = count_places(query, location_code)
    return count

# Deep Search Function divides the area into smaller parts then runs the search

def deep_search_places(query, location_code, divisions=3):
    """
    Perform a deep search by dividing the area into smaller parts, only counting results.
    """
    bounds = get_location_bounds(location_code)
    if not bounds:
        return 0

    sub_boxes = divide_bounding_box(bounds, divisions)
    total_count = 0

    for sub_box in sub_boxes:
        count = count_places(query, None, location_restriction={
                'rectangle': {
                'low': {
                    'latitude': sub_box['southwest']['lat'],
                    'longitude': sub_box['southwest']['lng']
                },
                'high': {
                    'latitude': sub_box['northeast']['lat'],
                    'longitude': sub_box['northeast']['lng']
                }
            }
        })
        total_count += count

    return total_count

# Count Places API req function, this function only requests places.id 

def count_places(query, location_code, location_restriction=None):
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id,nextPageToken'  # We only need the place ID to count and the next page token
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
    
    total_count = 0
    page_token = None
    
    while True:
        data = {
            'textQuery': query,
            'maxResultCount': 20,  # Maximum allowed by the API
            'locationRestriction': location_restriction
        }
        if page_token:
            data['pageToken'] = page_token
        
        try:
            response = requests.post(API_URL, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            total_count += len(result.get('places', []))
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            break
    
    return total_count


# Save to CSV function for specific location count
def save_specific_location_count_to_csv(data, file_path):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Location', 'Count'])
        for row in data:
            writer.writerow([row['place_name'], row['location'], row['count']])