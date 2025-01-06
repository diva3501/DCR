from flask import Flask, render_template, request, jsonify, redirect, url_for
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
    fuel_type = data.get('fuel_type', 'petrol')

    try:
        # Fetch route from TomTom API
        tomtom_url = f"https://api.tomtom.com/routing/1/calculateRoute/{start}:{end}/json?key={TOMTOM_API_KEY}&traffic=true"
        tomtom_response = requests.get(tomtom_url)
        tomtom_data = tomtom_response.json()

        # Extract distance and duration
        distance_km = tomtom_data['routes'][0]['summary']['lengthInMeters'] / 1000
        duration_min = tomtom_data['routes'][0]['summary']['travelTimeInSeconds'] / 60

        # Estimate emissions
        emissions_kg = estimate_emissions(distance_km, vehicle_type, fuel_type)

        # Fetch weather data from AQICN
        lat, lon = start.split(',')
        weather_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_API_KEY}"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        weather = weather_data.get('data', {}).get('aqi', 'Unavailable')

        return jsonify({
            "route_summary": {
                "distance_km": distance_km,
                "duration_min": duration_min,
                "weather": weather,
            },
            "emissions": emissions_kg
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/smart_scheduling')
def smart_scheduling():
    return render_template('smart_scheduling.html')

def estimate_emissions(distance_km, vehicle_type, fuel_type):
    emissions_per_km = {
        "car": {"petrol": 0.121, "diesel": 0.145, "electric": 0.05},
        "truck": {"petrol": 0.185, "diesel": 0.22, "electric": 0.08},
        "motorcycle": {"petrol": 0.055, "diesel": 0.07, "electric": 0.02}
    }
    return emissions_per_km.get(vehicle_type, {}).get(fuel_type, 0.121) * distance_km

if __name__ == '__main__':
    app.run(debug=True)
