# Stockholm Parking API Server
# This bypasses CORS issues and serves the app properly

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# Your Stockholm API key
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
        # Call Stockholm API from server side (no CORS issues)
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
            return jsonify(response.json())
        else:
            return jsonify({'error': f'API error: {response.status_code}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
