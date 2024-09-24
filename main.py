import os
from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import requests
from config import API_KEY

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTS_CSV = 'results.csv'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Google Places API endpoint
API_URL = 'https://places.googleapis.com/v1/places:searchText'

def search_places(query, page_size=5):
    """Searches for a list of places using the Google Places API with a location restriction to the US."""
    url = API_URL
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri'
    }
    location_restriction = {
        "locationRestriction": {
            "rectangle": {
                "low": {"latitude": 24.396308, "longitude": -125.0},
                "high": {"latitude": 49.384358, "longitude": -66.93457}
            }
        }
    }

    data = {
        'textQuery': query,
        'pageSize': page_size,
        **location_restriction
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result.get('places', [])
    return []

def process_queries(file_path):
    """Processes the uploaded queries and saves results to a CSV file."""
    results = []
    with open(file_path, 'r') as file:
        queries = [line.strip() for line in file.readlines()]

    for query in queries:
        places = search_places(query)
        if places:
            for place in places:
                place_info = {
                    'name': place['displayName']['text'],
                    'address': place['formattedAddress'],
                    'phone': place.get('internationalPhoneNumber', 'N/A'),
                    'website': place.get('websiteUri', 'N/A')
                }
                results.append(place_info)

    # Save results to CSV
    save_to_csv(results)

def save_to_csv(data, file_name=RESULTS_CSV):
    """Saves the data to a CSV file."""
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Address', 'Phone', 'Website'])
        for row in data:
            writer.writerow([row['name'], row['address'], row.get('phone', 'N/A'), row.get('website', 'N/A')])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles the file upload and triggers the search process."""
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Process the uploaded queries
            process_queries(file_path)

            return redirect(url_for('download_csv'))

@app.route('/download')
def download_csv():
    """Provides the CSV file for download."""
    return send_file(RESULTS_CSV, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)