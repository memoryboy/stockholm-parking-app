
# Robust backend that enriches Stockholm LTF-Tolken data
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests, os
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)
API_KEY=os.environ.get('STHLM_API','c24534a8-7bc6-43af-b19e-b8ca86b0c5b0')
BASE='https://openparking.stockholm.se/LTF-Tolken/v1'

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/parking')
def parking():
    lat=request.args.get('lat'); lng=request.args.get('lng'); radius=request.args.get('radius','120')
    if not lat or not lng:
        return jsonify({'error':'Missing lat/lng'}),400
    try:
        url=f"{BASE}/ptillaten/within"
        params={'radius':radius,'lat':lat,'lng':lng,'outputFormat':'json','apiKey':API_KEY}
        r=requests.get(url,params=params,timeout=10)
        r.raise_for_status()
        data=r.json()
        now=datetime.now()
        for feat in data.get('features',[]):
            p=feat.get('properties',{})
            # normalize keys (some feeds vary in case)
            keys={k.lower():k for k in p.keys()}
            def g(name):
                return p.get(keys.get(name.lower()))
            tid_fran=g('TID_FRAN') or g('tid_fran')
            tid_till=g('TID_TILL') or g('tid_till')
            dagar=g('DAGAR') or g('dagar')
            taxa=g('TAXA') or g('taxa')
            max_tid=g('MAX_TID') or g('max_tid')
            allowed=True
            try:
                if tid_fran and tid_till:
                    cur=now.hour*100+now.minute
                    s=int(str(tid_fran).replace(':',''))
                    e=int(str(tid_till).replace(':',''))
                    allowed = (cur>=s and cur<e)
            except: pass
            feat['parsed']={
                'isCurrentlyAllowed': allowed,
                'timeUntil': tid_till,
                'formattedDays': dagar or 'Alla dagar',
                'formattedTime': (f"{tid_fran} - {tid_till}" if (tid_fran or tid_till) else 'Hela dygnet'),
                'taxa': (f"Taxa {taxa}" if taxa else 'Ingen avgift'),
                'maxTime': max_tid or 'Ingen begränsning'
            }
        return jsonify(data)
    except requests.HTTPError as e:
        return jsonify({'error':f'HTTP {e.response.status_code}'}),502
    except Exception as e:
        return jsonify({'error':str(e)}),500

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
