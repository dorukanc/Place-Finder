from flask import Flask, request, jsonify, send_file
import requests
import csv
import os
from config import API_KEY

app = Flask(__name__)

API_URL = 'https://places.googleapis.com/v1/places:searchText'

def search_places(query, region, page_size=5):
    """Searches for a list of places using the Google Places API and region-specific search."""
    url = API_URL
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri'
    }
    data = {
        'textQuery': query,
        'pageSize': page_size,
        'regionCode': region  # Pass the selected region as a parameter to the API
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result.get('places', [])  # Return the list of places
    return []

def save_to_csv(data, file_name='results.csv'):
    """Saves the data to a CSV file."""
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Address', 'Phone', 'Website'])  # CSV header
        for row in data:
            writer.writerow([row['name'], row['address'], row.get('phone', 'N/A'), row.get('website', 'N/A')])

@app.route('/run-search', methods=['POST'])
def run_search():
    # Handle the uploaded file and region
    if 'query' not in request.files or 'region' not in request.form:
        return jsonify({'success': False, 'message': 'Missing query file or region'}), 400
    
    query_file = request.files['query']
    region = request.form['region']

    # Process the uploaded file and load queries
    queries = [line.decode('utf-8').strip() for line in query_file.readlines()]

    results = []
    for query in queries:
        places = search_places(query, region, page_size=5)  # Get first 5 results
        if places:
            for place in places:
                place_info = {
                    'name': place['displayName']['text'],
                    'address': place['formattedAddress'],
                    'phone': place.get('internationalPhoneNumber', 'N/A'),
                    'website': place.get('websiteUri', 'N/A')
                }
                results.append(place_info)

    # Save the results to CSV
    save_to_csv(results)

    return jsonify({'success': True, 'results': results})

@app.route('/download-csv', methods=['GET'])
def download_csv():
    file_path = 'results.csv'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'success': False, 'message': 'No results found'}), 404

if __name__ == '__main__':
    app.run(debug=True)