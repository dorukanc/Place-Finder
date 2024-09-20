import requests
import csv
from config import API_KEY  # Import API_KEY from config.py

API_URL = 'https://places.googleapis.com/v1/places:searchText'

def load_queries(file_path):
    """Reads queries from a text file."""
    with open(file_path, 'r') as file:
        queries = [line.strip() for line in file.readlines()]
    return queries

def search_place(query):
    """Searches for a place using the Google Places API."""
    url = API_URL
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri'
    }
    data = {
        'textQuery': query
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('places'):
            return result['places'][0]  # Return the first match
    return None

def save_to_csv(data, file_name='results.csv'):
    """Saves the data to a CSV file."""
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Place Name', 'Address', 'Phone', 'Website'])  # CSV header
        for row in data:
            writer.writerow([row['name'], row['address'], row.get('phone', 'N/A'), row.get('website', 'N/A')])

def main():
    queries = load_queries('queries.txt')
    results = []

    for query in queries:
        print(f"Searching for: {query}")
        place = search_place(query)
        if place:
            place_info = {
                'name': place['displayName']['text'],
                'address': place['formattedAddress'],
                'phone': place.get('internationalPhoneNumber', 'N/A'),
                'website': place.get('websiteUri', 'N/A')
            }
            results.append(place_info)
            print(f"Found: {place_info['name']} at {place_info['address']}")
            print(f"Phone: {place_info['phone']}")
            print(f"Website: {place_info['website']}")
        else:
            print(f"No results found for {query}")

    # Save results to CSV
    if results:
        save_to_csv(results)
        print(f"Results saved to results.csv")

if __name__ == '__main__':
    main()