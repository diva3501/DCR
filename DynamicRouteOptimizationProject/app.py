from flask import Flask, request, jsonify, render_template
import requests

# Initialize Flask app
app = Flask(__name__)

# API Keys (replace with your valid keys)
TOMTOM_API_KEY = "MVKuv3pCsGAtSHNdjQ7JIj9yorWXSkiQ"
AQICN_API_KEY = "bfd17d0a7a3265bb140f9341cbd22581f0631a98"

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def get_route():
    try:
        data = request.json
        start = data['start']
        end = data['end']
        vehicle_type = data['vehicle_type']

        # Ensure start and end points are latitude,longitude
        if not (',' in start and ',' in end):
            return jsonify({"error": "Invalid start or end coordinates. Format: 'latitude,longitude'"}), 400

        # TomTom API URL
        tomtom_url = f"https://api.tomtom.com/routing/1/calculateRoute/{start}:{end}/json?key={TOMTOM_API_KEY}&traffic=true"
        tomtom_response = requests.get(tomtom_url)
        
        if tomtom_response.status_code != 200:
            return jsonify({"error": "Failed to fetch route from TomTom API."}), 500
        
        tomtom_data = tomtom_response.json()

        # Calculate emissions
        distance_km = tomtom_data['routes'][0]['summary']['lengthInMeters'] / 1000
        emissions_kg = estimate_emissions(distance_km, vehicle_type)

        return jsonify({
            "route_summary": tomtom_data['routes'][0]['summary'],
            "emissions_kg": emissions_kg
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def estimate_emissions(distance_km, vehicle_type):
    emissions_per_km = {"car": 0.121, "truck": 0.185, "motorcycle": 0.055}
    return emissions_per_km.get(vehicle_type, 0.121) * distance_km

if __name__ == '__main__':
    app.run(debug=True)
