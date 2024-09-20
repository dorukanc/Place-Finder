import requests
from config import API_KEY  # Import API_KEY from config.py

# List of companies to search
companies = [
    'Hilton headquarters',
    'Marriott headquarters',
    'Holiday Inn headquarters',
    'Holiday Inn Express headquarters',
    'Walt Disney Parks and Resorts headquarters',
    'Hampton Inn headquarters',
    'Courtyard by Marriott headquarters',
    'Ritz-Carlton headquarters',
    'Hyatt Regency headquarters',
    'Best Western headquarters',
    'Sheraton headquarters',
    'Hyatt headquarters',
    'Comfort Inn headquarters',
    'Embassy Suites headquarters',
    'Wyndham Hotels & Resorts headquarters',
    'Hyatt Place headquarters',
    'Doubletree headquarters',
    'Hilton Garden Inn headquarters',
    'Ramada headquarters',
    'Days Inn headquarters'
]

def search_place(query):
    """Searches for a place using the Google Places API."""
    url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
    params = {
        'input': query,
        'inputtype': 'textquery',
        'fields': 'place_id,name,formatted_address',
        'key': API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['candidates']:
            return result['candidates'][0]  # Return the first match
    return None

def get_place_details(place_id):
    """Fetches detailed information about a place using its place_id."""
    url = f'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,international_phone_number,website',
        'key': API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['result']
    return None

def main():
    for company in companies:
        print(f"Searching for: {company}")
        place = search_place(company)
        if place:
            print(f"Found: {place['name']} at {place['formatted_address']}")
            place_details = get_place_details(place['place_id'])
            if place_details:
                print(f"Details for {place_details['name']}:")
                print(f"Address: {place_details['formatted_address']}")
                print(f"Phone: {place_details.get('international_phone_number', 'N/A')}")
                print(f"Website: {place_details.get('website', 'N/A')}")
                print("\n")
        else:
            print(f"No results found for {company}")

if __name__ == '__main__':
    main()