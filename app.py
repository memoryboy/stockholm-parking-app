# Stockholm Parking API Server - FIXED VERSION
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)

API_KEY = 'c24534a8-7bc6-43af-b19e-b8ca86b0c5b0'
API_BASE = 'https://openparking.stockholm.se/LTF-Tolken/v1'

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/parking')
def get_parking():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = request.args.get('radius', 100)

    if not lat or not lng:
        return jsonify({'error': 'Missing lat/lng parameters'}), 400

    try:
        # Call Stockholm API
        url = f'{API_BASE}/ptillaten/within'
        params = {
            'radius': radius,
            'lat': lat,
            'lng': lng,
            'outputFormat': 'json',
            'apiKey': API_KEY
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Parse and enrich the data
            if 'features' in data and len(data['features']) > 0:
                now = datetime.now()

                for feature in data['features']:
                    props = feature.get('properties', {})

                    # Add parsed information for easier frontend consumption
                    feature['parsed'] = {
                        'isCurrentlyAllowed': check_if_currently_allowed(props, now),
                        'timeUntil': extract_end_time(props),
                        'formattedDays': format_days(props),
                        'formattedTime': format_time_range(props),
                        'taxa': props.get('TAXA', props.get('taxa', 'Ingen avgift')),
                        'maxTime': props.get('MAX_TID', props.get('max_tid', 'Ingen begränsning'))
                    }

            return jsonify(data)
        else:
            return jsonify({'error': f'API error: {response.status_code}'}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def check_if_currently_allowed(props, now):
    """Check if parking is currently allowed based on time restrictions"""
    # Get time fields (API might use different field names)
    time_from = props.get('TID_FRAN') or props.get('tid_fran') or props.get('TidFran')
    time_to = props.get('TID_TILL') or props.get('tid_till') or props.get('TidTill')

    if not time_from or not time_to:
        return True  # No time restriction means always allowed

    try:
        # Parse time
        current_time = now.hour * 100 + now.minute
        start_time = int(time_from.replace(':', ''))
        end_time = int(time_to.replace(':', ''))

        return start_time <= current_time < end_time
    except:
        return True

def extract_end_time(props):
    """Extract end time from properties"""
    return props.get('TID_TILL') or props.get('tid_till') or props.get('TidTill')

def format_days(props):
    """Format days string"""
    days = props.get('DAGAR') or props.get('dagar') or props.get('Dagar')
    if not days:
        return 'Alla dagar'
    return days

def format_time_range(props):
    """Format time range"""
    time_from = props.get('TID_FRAN') or props.get('tid_fran') or props.get('TidFran')
    time_to = props.get('TID_TILL') or props.get('tid_till') or props.get('TidTill')

    if time_from and time_to:
        return f'{time_from} - {time_to}'
    elif time_from:
        return f'Från {time_from}'
    elif time_to:
        return f'Till {time_to}'
    else:
        return 'Hela dygnet'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
