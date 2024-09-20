# HQ Finder

## Overview

**HQ Finder** is a Python-based tool that uses the Google Places API to retrieve the headquarters address, contact information, and other details for well-known hotel chains. This script automates the process of finding business information and outputs the results in a structured format.

## Features

- **Retrieve Headquarters Information**: Fetch the headquarters' address, phone number, and website for a list of companies.
- **Google Places API**: Leverages the Google Places API for reliable business information.
- **Secure API Keys**: Keeps your API key secure by using environment variables or config files excluded from version control.
- **CSV Output**: Optionally export the retrieved results to a CSV file.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hq-finder.git
   cd hq-finder
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
   - Add your API key to an environment variable or create a `config.py` file.

## Usage

### Using Environment Variables

1. Add your Google Places API key to your shell's environment variables:

   **Linux/macOS:**
   ```bash
   export API_KEY="YOUR_API_KEY"
   ```

   **Windows (CMD):**
   ```cmd
   set API_KEY=YOUR_API_KEY
   ```

2. Run the script:
   ```bash
   python main.py
   ```

### Using a Config File

1. Create a `config.py` file:
   ```python
   # config.py
   API_KEY = "YOUR_API_KEY"
   ```

2. Make sure `config.py` is added to your `.gitignore` file.

3. Run the script:
   ```bash
   python main.py
   ```

## Example Output

```
Company: Hilton
Address: 7930 Jones Branch Dr, McLean, VA 22102, USA
Phone: +1 703-883-1000
Website: https://www.hilton.com
```

## Configuration

- **API Key Security**: Store your API key securely using environment variables or a config file.
- **Custom Queries**: Modify the list of companies to include other businesses.
- **CSV Export**: You can enable CSV export in the script to save results.

## Project Structure

```
hq-finder/
│
├── main.py               # Main Python script that retrieves headquarters info
├── config.py             # (Optional) File to store the API key (git-ignored)
├── requirements.txt      # Required Python packages
├── .gitignore            # To ignore sensitive files
└── README.md             # This file
```

## License

This project is licensed under the MIT License.
```

This version of the repository name is more concise while still capturing the core function of the tool. Let me know if you need further changes!