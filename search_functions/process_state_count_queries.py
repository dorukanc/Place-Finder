import os
import threading
import csv
import requests
import json

# Import API KEY from .env

API_URL = 'https://places.googleapis.com/v1/places:searchText'
API_KEY = os.getenv('API_KEY')

# Import delete_file_after_delay, import get_location_bounds, import divide_bounding_box

from search_functions.delete_file_after_delay import delete_file_after_delay
from search_functions.get_location_bounds import get_location_bounds
from search_functions.divide_bounding_box import divide_bounding_box


# Load country and state bounds from a JSON file
with open('location_bounds.json', 'r') as f:
    LOCATION_BOUNDS = json.load(f)

def process_state_count_queries(query_file_path, results_file_path, use_deep_search=False):
    try:
        with open(query_file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()
        
        results = []
        for query in queries:
            place_name = query.strip()
            state_counts = count_locations_per_state(place_name, use_deep_search)
            results.append({
                'place_name': place_name,
                'state_counts': state_counts
            })
        save_state_count_to_csv(results, results_file_path)
    except Exception as e:
        print(f"Error processing state count queries: {e}")
    finally:
        if os.path.exists(query_file_path):
            os.remove(query_file_path) 
            print(f"Deleted query file: {query_file_path}")

        threading.Thread(target=delete_file_after_delay, args=(results_file_path,)).start()

# Added deep search function, counting locations per state (count in 50 states)
def count_locations_per_state(query, use_deep_search=False):
    state_counts = {state: 0 for state in LOCATION_BOUNDS.keys() if state.startswith('US-')}
    for state in state_counts.keys():
        if use_deep_search:
            count = deep_search_places(query, state)
        else:
            count = count_places(query, state)
        state_counts[state] = count
    return state_counts

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

# Save to CSV function for state count

def save_state_count_to_csv(data, file_path):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        header = ['Place Name'] + [state for state in LOCATION_BOUNDS.keys() if state.startswith('US-')]
        writer.writerow(header)
        for row in data:
            writer.writerow([row['place_name']] + [row['state_counts'].get(state, 0) for state in header[1:]])