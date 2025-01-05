from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# API Keys (replace with your actual keys)
TOMTOM_API_KEY = "MVKuv3pCsGAtSHNdjQ7JIj9yorWXSkiQ"
AQICN_API_KEY = "bfd17d0a7a3265bb140f9341cbd22581f0631a98"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/route', methods=['POST'])
def get_route():
    data = request.json
    start = data.get('start')  # Latitude,Longitude
    end = data.get('end')      # Latitude,Longitude
    vehicle_type = data.get('vehicle_type', 'car')

    try:
        # Fetch route from TomTom API
        tomtom_url = f"https://api.tomtom.com/routing/1/calculateRoute/{start}:{end}/json?key={TOMTOM_API_KEY}&traffic=true"
        tomtom_response = requests.get(tomtom_url)
        tomtom_data = tomtom_response.json()

        # Extract distance
        distance_km = tomtom_data['routes'][0]['summary']['lengthInMeters'] / 1000

        # Estimate emissions
        emissions_kg = estimate_emissions(distance_km, vehicle_type)

        return jsonify({
            "route_summary": tomtom_data['routes'][0]['summary'],
            "emissions": emissions_kg
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def estimate_emissions(distance_km, vehicle_type):
    emissions_per_km = {
        "car": 0.121,    # 121 grams per km
        "truck": 0.185,  # 185 grams per km
        "motorcycle": 0.055  # 55 grams per km
    }
    return emissions_per_km.get(vehicle_type, 0.121) * distance_km

if __name__ == '__main__':
    app.run(debug=True)
