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
        # Fetch route from TomTom API with traffic consideration
        tomtom_url = f"https://api.tomtom.com/routing/1/calculateRoute/{start}:{end}/json?key={TOMTOM_API_KEY}&traffic=true"
        tomtom_response = requests.get(tomtom_url)
        tomtom_data = tomtom_response.json()

        # Extract route summaries
        routes = tomtom_data.get("routes", [])
        route_details = []

        for route in routes:
            distance_km = route['summary']['lengthInMeters'] / 1000
            duration_min = route['summary']['travelTimeInSeconds'] / 60
            route_details.append({
                "distance_km": distance_km,
                "duration_min": duration_min,
                "traffic_level": route['summary'].get('trafficTimeInSeconds', 'N/A')
            })

        # Choose the best route based on the shortest duration (or traffic conditions)
        best_route = min(route_details, key=lambda x: x["duration_min"])

        # Estimate emissions for the best route
        emissions_kg = estimate_emissions(best_route["distance_km"], vehicle_type, fuel_type)

        # Fetch weather data from AQICN API
        lat, lon = start.split(',')
        weather_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_API_KEY}"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        weather = weather_data.get('data', {}).get('aqi', 'Unavailable')

        # Respond with multiple routes details and the best one selected
        return jsonify({
            "routes": route_details,
            "best_route": best_route,
            "emissions": emissions_kg,
            "weather": weather
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/smart_scheduling')
def smart_scheduling():
    return render_template('smart_schedule.html')

@app.route('/smart_schedule', methods=['POST'])
def smart_schedule():
    try:
        data = request.json
        num_orders = data.get('num_orders')
        priority = data.get('priority')

        # Implement your logic here
        # For example, use the inputs to calculate a result:
        if num_orders < 1:
            raise ValueError("Number of orders should be greater than zero.")

        best_time = "10:30 AM"  # Placeholder logic
        priority_suggestion = "High"  # Placeholder logic
        
        # Respond with JSON data
        return jsonify({
            'best_time': best_time,
            'priority_suggestion': priority_suggestion
        })
    except Exception as e:
        # In case of errors, send an error response with 500 status code
        return jsonify({'error': str(e)}), 500
    
@app.route('/package_load')
def package_loading():
    return render_template('package_load.html')

@app.route('/package_load', methods=['POST'])
def package_load():
    data = request.json
    vehicle_capacity = data.get('vehicle_capacity')
    package_weight = data.get('package_weight')
    num_packages = data.get('num_packages')

    if not vehicle_capacity or not package_weight or not num_packages:
        return jsonify({"error": "All fields are required"}), 400

    # Calculate the number of vehicles needed to carry all packages
    packages_per_vehicle = vehicle_capacity // package_weight
    required_vehicles = (num_packages + packages_per_vehicle - 1) // packages_per_vehicle

    if required_vehicles <= 0:
        return jsonify({"error": "Package weight exceeds vehicle capacity."}), 400

    return jsonify({
        "required_vehicles": required_vehicles,
        "packages_per_vehicle": packages_per_vehicle
    })


def estimate_emissions(distance_km, vehicle_type, fuel_type):
    emissions_per_km = {
        "car": {"petrol": 0.121, "diesel": 0.145, "electric": 0.05},
        "truck": {"petrol": 0.185, "diesel": 0.22, "electric": 0.08},
        "motorcycle": {"petrol": 0.055, "diesel": 0.07, "electric": 0.02}
    }
    return emissions_per_km.get(vehicle_type, {}).get(fuel_type, 0.121) * distance_km

if __name__ == '__main__':
    app.run(debug=True)
