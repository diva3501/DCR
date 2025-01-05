from flask import Flask, request, jsonify, render_template
import requests

# Initialize Flask app
app = Flask(__name__)

# API Keys (replace with your actual keys)
TOMTOM_API_KEY = "MVKuv3pCsGAtSHNdjQ7JIj9yorWXSkiQ"
AQICN_API_KEY = "bfd17d0a7a3265bb140f9341cbd22581f0631a98"

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def get_route():
    data = request.json
    start = data['start']
    end = data['end']
    vehicle_type = data['vehicle_type']

    # Real-time Traffic using TomTom API
    tomtom_url = f"https://api.tomtom.com/routing/1/calculateRoute/{start}:{end}/json?key={TOMTOM_API_KEY}&traffic=true"
    response = requests.get(tomtom_url).json()

    # Calculate emissions
    distance_km = response['routes'][0]['summary']['lengthInMeters'] / 1000
    emissions_kg = estimate_emissions(distance_km, vehicle_type)

    return jsonify({
        "route": response['routes'][0],
        "emissions_kg": emissions_kg
    })

def estimate_emissions(distance_km, vehicle_type):
    emissions_per_km = {"car": 0.121, "truck": 0.185, "motorcycle": 0.055}
    return emissions_per_km.get(vehicle_type, 0.121) * distance_km

if __name__ == '__main__':
    app.run(debug=True)
