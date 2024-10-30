from flask import Flask, request, jsonify, send_file, render_template
import os
import uuid
import threading
import json
import csv

# Import Search Functions

from search_functions.process_specific_location_queries import process_specific_location_queries
from search_functions.process_state_count_queries import process_state_count_queries
from search_functions.process_specific_count_queries import process_specific_location_count_queries

app = Flask(__name__)

# Create a temporary directory to store files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
QUERY_DIR = os.path.join(TEMP_DIR, 'queries')
RESULTS_DIR = os.path.join(TEMP_DIR, 'results')  

# Ensure directories exist
os.makedirs(QUERY_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Load country and state bounds from a JSON file
with open('location_bounds.json', 'r') as f:
    LOCATION_BOUNDS = json.load(f)


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

    return jsonify({'success': True, 'message': 'Search started', 'session_id': session_id, 'plot' : search_type == 'specific-count'})

# To plot data in the front-end passing the csv result as json
@app.route('/get-results/<session_id>', methods = ['GET'])
def get_results(session_id):
    results_file_path = os.path.join(RESULTS_DIR, f"results_{session_id}.csv")
    
    # Check if the file exists
    if not os.path.exists(results_file_path):
        return jsonify({'success': False, 'message': 'Results not found'}), 404

    # Read the CSV and convert to JSON format
    data = []
    with open(results_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Ensure proper integer conversion for the 'Count' column
            row['Count'] = int(row['Count'])
            data.append(row)

    return jsonify({'success': True, 'data': data})

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
