# Stockholm Parking API Server v2.0 - FULL FEATURED

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
            if 'features' in data and len(data['features']) > 0:
                now = datetime.now()
                for i, feature in enumerate(data['features']):
                    props = feature.get('properties', {})
                    feature['parsed'] = {
                        'isCurrentlyAllowed': check_if_currently_allowed(props, now),
                        'timeUntil': extract_end_time(props),
                        'formattedDays': format_days(props),
                        'formattedTime': format_time_range(props),
                        'taxa': extract_taxa(props),
                        'maxTime': extract_max_time(props)
                    }
            return jsonify(data)
        else:
            return jsonify({'error': f'API error: {response.status_code}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_if_currently_allowed(props, now):
    time_from = props.get('TID_FRAN') or props.get('tid_fran')
    time_to = props.get('TID_TILL') or props.get('tid_till')
    if not time_from or not time_to:
        return True
    try:
        current_time = now.hour * 100 + now.minute
        start_time = int(time_from.replace(':', ''))
        end_time = int(time_to.replace(':', ''))
        return start_time <= current_time < end_time
    except:
        return True

def extract_end_time(props):
    return props.get('TID_TILL') or props.get('tid_till') or None

def format_days(props):
    days = props.get('DAGAR') or props.get('dagar')
    return days if days else 'Alla dagar'

def format_time_range(props):
    time_from = props.get('TID_FRAN') or props.get('tid_fran')
    time_to = props.get('TID_TILL') or props.get('tid_till')
    if time_from and time_to:
        return f'{time_from} - {time_to}'
    return 'Hela dygnet'

def extract_taxa(props):
    taxa = props.get('TAXA') or props.get('taxa')
    if taxa:
        return f'Taxa {taxa}'
    return 'Ingen avgift'

def extract_max_time(props):
    max_tid = props.get('MAX_TID') or props.get('max_tid')
    return max_tid if max_tid else 'Ingen begränsning'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
