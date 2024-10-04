# Place Finder

## Overview

**Place Finder** is a Python-based web application that utilizes the Google Places API to search for and retrieve information about various locations. It allows users to perform text-based searches across different countries and US states, making it an excellent tool for market research and data collection directly from Google Maps.

## Features

- **Flexible Text Search**: Search for any query across multiple locations.
- **Country and US State Support**: Perform searches in various countries and specific US states.
- **CSV Export**: Export search results to a CSV file for easy analysis.
- **US State Count**: Ability to count search results for each US state, useful for comparative analysis.
- **User-friendly Interface**: Simple web interface for easy interaction with the tool.
- **Google Places API Integration**: Leverages the Google Places API for accurate and up-to-date information.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/dorukanc/place-finder.git
   cd place-finder
   ```

2. Set up a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Windows, use `venv\Scripts\activate`
   ```

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your Google Places API key:
   - Create a `config.py` file in the root directory.
   - Add your API key to the `config.py` file:
     ```python
     API_KEY = "YOUR_GOOGLE_PLACES_API_KEY"
     ```

## Configuration

1. Obtain a Google Places API key:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Enable the Places API for your project.
   - Create credentials (API key) for the Places API.

2. Configure the application:
   - Open `config.py` and replace `"YOUR_GOOGLE_PLACES_API_KEY"` with your actual API key.

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`.

3. Using the web interface:
   - Upload a text file containing your search queries (one per line).
   - Select the location (country or US state) for your search from the dropdown menu.
   - Click "Run Search" to start the process.
   - Wait for the search to complete.
   - Once complete, click "Download Results" to get your CSV file.

### Example Use Cases

1. Find hotel locations:
   - Upload a file with hotel chain names.
   - Select different states to compare hotel presence across the US.

2. Market research for a retail chain:
   - Search for your company name across different countries to see international presence.

3. Competitor analysis:
   - Search for competitor names in specific regions to understand their market coverage.

## US State Count Feature

To use the US State Count feature:

1. Prepare a text file with your search queries.
2. Run the search for each US state you're interested in.
3. The resulting CSV will include a count of results for each state, allowing you to compare presence across states easily.

## Project Structure

```
place-finder/
│
├── app.py               # Main Flask application
├── config.py            # Configuration file for API key
├── location_bounds.json # JSON file containing location boundaries
├── requirements.txt     # Required Python packages
├── templates/
│   └── index.html       # HTML template for the web interface
└── README.md            # This file
```

## License

This project is licensed under the MIT License.

## Note

Ensure that you comply with Google's Terms of Service and usage limits when using this tool. The application is designed for educational and research purposes, and users should be aware of and adhere to Google's policies regarding data usage and collection.
