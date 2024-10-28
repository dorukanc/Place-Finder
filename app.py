from flask import Flask, request, jsonify, send_file, render_template
import requests
import csv
import os
import tempfile
import uuid
from dotenv import load_dotenv
import threading
import time
import json
import math


app = Flask(__name__)

API_URL = 'https://places.googleapis.com/v1/places:searchText'
API_KEY = os.getenv('API_KEY')

# Create a temporary directory to store files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
QUERY_DIR = os.path.join(TEMP_DIR, 'queries')
RESULTS_DIR = os.path.join(TEMP_DIR, 'results')  

# Ensure directories exist
os.makedirs(QUERY_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# File expiration time in seconds (300 minutes)
FILE_EXPIRATION_TIME = 300 * 60

# Load country and state bounds from a JSON file
with open('location_bounds.json', 'r') as f:
    LOCATION_BOUNDS = json.load(f)

def get_location_bounds(location_code):
    """Returns the bounding box for a given location code (country or US state)."""
    bounds = LOCATION_BOUNDS.get(location_code)
    if bounds:
        return {
            'southwest': {'lat': bounds['southwest']['lat'], 'lng': bounds['southwest']['lng']},
            'northeast': {'lat': bounds['northeast']['lat'], 'lng': bounds['northeast']['lng']}
        }
    return None

def divide_bounding_box(bounds, divisions):
    """
    Divide a bounding box into smaller boxes.
    """
    lat_step = (bounds['northeast']['lat'] - bounds['southwest']['lat']) / divisions
    lng_step = (bounds['northeast']['lng'] - bounds['southwest']['lng']) / divisions
    
    sub_boxes = []
    for i in range(divisions):
        for j in range(divisions):
            sub_box = {
                'southwest': {
                    'lat': bounds['southwest']['lat'] + i * lat_step,
                    'lng': bounds['southwest']['lng'] + j * lng_step
                },
                'northeast': {
                    'lat': bounds['southwest']['lat'] + (i + 1) * lat_step,
                    'lng': bounds['southwest']['lng'] + (j + 1) * lng_step
                }
            }
            sub_boxes.append(sub_box)
    
    return sub_boxes

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


# func for only counting locations on a spesific location
def count_locations_spesific_location(query, location_code, use_deep_search= False):
    if use_deep_search:
        count = deep_search_places(query, location_code)
    else:
        count = count_places(query, location_code)
    return count

# Function for processing queries specific to a location
def process_specific_location_count_queries(query_file_path, location_code, results_file_path, use_deep_search=False):
    try:
        with open(query_file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()

        results = []
        for query in queries:
            query = query.strip()
            count = count_locations_spesific_location(query, location_code, use_deep_search)
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

# Save to CSV function for specific location count
def save_specific_location_count_to_csv(data, file_path):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Location', 'Count'])
        for row in data:
            writer.writerow([row['place_name'], row['location'], row['count']])

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

# Save to CSV function for state count

def save_state_count_to_csv(data, file_path):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        header = ['Place Name'] + [state for state in LOCATION_BOUNDS.keys() if state.startswith('US-')]
        writer.writerow(header)
        for row in data:
            writer.writerow([row['place_name']] + [row['state_counts'].get(state, 0) for state in header[1:]])


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

# Added another api req methdo to reduce cost only getting places.id -> for deep search state_count func

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

def save_to_csv(data, file_path):
    """Saves the data to a CSV file."""
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Address', 'Phone', 'Website'])
        for row in data:
            writer.writerow([row['name'], row['address'], row.get('phone', 'N/A'), row.get('website', 'N/A')])

def delete_file_after_delay(file_path):
    """Deletes the file after a specified delay."""
    time.sleep(FILE_EXPIRATION_TIME)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

@app.route('/')
def index():
    """Serve the main HTML page with location options."""
    return render_template('index.html', locations=LOCATION_BOUNDS.keys())

# Added deep search option run-search route
@app.route('/run-search', methods=['POST'])
def run_search():
    if 'query' not in request.files or 'location' not in request.form or 'search-type' not in request.form:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    query_file = request.files['query']
    location_code = request.form['location']
    category = request.form['category']
    search_type = request.form['search-type']
    use_deep_search = request.form.get('use-deep-search') == 'true'

    session_id = str(uuid.uuid4())
    query_file_path = os.path.join(QUERY_DIR, f"query_{session_id}.txt")
    results_file_path = os.path.join(RESULTS_DIR, f"results_{session_id}.csv")

    query_file.save(query_file_path)

    if search_type == 'specific-location':
        threading.Thread(target=process_specific_location_queries, args=(query_file_path, location_code, category, results_file_path, use_deep_search)).start()
    elif search_type == 'state-count':
        threading.Thread(target=process_state_count_queries, args=(query_file_path, results_file_path, use_deep_search)).start()
    elif search_type == 'specific-count':
        threading.Thread(target=process_specific_location_count_queries, args=(query_file_path, location_code, results_file_path, use_deep_search)).start()
    else:
        return jsonify({'success': False, 'message': 'Invalid search type'}), 400

    return jsonify({'success': True, 'message': 'Search started', 'session_id': session_id})

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

@app.route('/check-status/<session_id>', methods=['GET'])
def check_status(session_id):
    results_file_path = os.path.join(RESULTS_DIR, f"results_{session_id}.csv")
    return jsonify({'status': 'complete' if os.path.exists(results_file_path) else 'processing'})

@app.route('/download-csv/<session_id>', methods=['GET'])
def download_csv(session_id):
    results_file_path = os.path.join(RESULTS_DIR, f"results_{session_id}.csv")
    if os.path.exists(results_file_path):
        return send_file(results_file_path, as_attachment=True, download_name='results.csv')
    return jsonify({'success': False, 'message': 'No results found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
