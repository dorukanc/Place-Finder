import json

# Load country and state bounds from a JSON file
with open('data/location_bounds.json', 'r') as f:
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