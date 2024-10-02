from flask import Flask, request, jsonify, send_file, render_template
import requests
import csv
import os
import tempfile
import uuid
from config import API_KEY
import threading
import time
import json

app = Flask(__name__)

API_URL = 'https://places.googleapis.com/v1/places:searchText'

# Create a temporary directory to store files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
QUERY_DIR = os.path.join(TEMP_DIR, 'queries')
RESULTS_DIR = os.path.join(TEMP_DIR, 'results')  

# Ensure directories exist
os.makedirs(QUERY_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# File expiration time in seconds (15 minutes)
FILE_EXPIRATION_TIME = 15 * 60

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
# Added another function to count locations for each state
def count_locations_per_state(query):
    state_counts = {state: 0 for state in LOCATION_BOUNDS.keys() if state.startswith('US-')}
    for state in state_counts.keys():
        places = search_places(query, state)
        state_counts[state] = len(places)
    return state_counts

def process_state_count_queries(query_file_path, results_file_path):
    try:
        with open(query_file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()
        
        results = []
        for query in queries:
            place_name = query.strip()
            state_counts = count_locations_per_state(place_name)
            results.append({
                'place_name' : place_name,
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


def search_places(query, location_code, page_size=20):
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,nextPageToken'
    }
    bounds = get_location_bounds(location_code)
    
    location_restriction = None
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
            'locationRestriction': location_restriction
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

@app.route('/run-search', methods=['POST'])
def run_search():
    if 'query' not in request.files or 'location' not in request.form or 'search-type' not in request.form:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    query_file = request.files['query']
    location_code = request.form['location']
    search_type = request.form['search-type']

    session_id = str(uuid.uuid4())
    query_file_path = os.path.join(QUERY_DIR, f"query_{session_id}.txt")
    results_file_path = os.path.join(RESULTS_DIR, f"results_{session_id}.csv")

    query_file.save(query_file_path)

    if search_type == 'specific-location':
        threading.Thread(target=process_specific_location_queries, args=(query_file_path, location_code, results_file_path)).start()
    elif search_type == 'state-count':
        threading.Thread(target=process_state_count_queries, args=(query_file_path, results_file_path)).start()
    else:
        return jsonify({'success': False, 'message': 'Invalid search type'}), 400

    return jsonify({'success': True, 'message': 'Search started', 'session_id': session_id})

def process_specific_location_queries(query_file_path, location_code, results_file_path):
    try:
        with open(query_file_path, 'r', encoding='utf-8') as file:
            queries = file.readlines()

        results = []
        for query in queries:
            places = search_places(query.strip(), location_code)
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