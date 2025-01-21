from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
EMISSION_FACTOR = 0.12  # kg CO₂ per km

def calculate_emissions(distance_km):
    """Calculate emissions based on distance."""
    return round(distance_km * EMISSION_FACTOR, 2)

@app.route('/')
def dashboard():
    return render_template('dashboard.html', title="Dashboard")

@app.route('/routes')
def routes():
    return render_template('index1.html', title="Route Planner", google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/get-routes', methods=['POST'])
def get_routes():
    """Fetch routes from Google Maps API."""
    data = request.json
    start_coords = data['start_coords']
    end_coords = data['end_coords']

    url = f"https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': start_coords,
        'destination': end_coords,
        'alternatives': 'true',
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    routes = response.json().get('routes', [])

    route_details = []
    for route in routes[:3]:
        distance = route['legs'][0]['distance']['value'] / 1000
        duration = route['legs'][0]['duration']['text']
        emissions = calculate_emissions(distance)
        route_details.append({
            'summary': route['summary'],
            'distance': f"{distance:.2f} km",
            'duration': duration,
            'emissions': f"{emissions} kg CO₂"
        })

    return jsonify({'routes': route_details})

if __name__ == '__main__':
    app.run(debug=True)
