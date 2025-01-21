from flask import Flask, render_template, request, jsonify
import requests
import math
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
AQICN_API_KEY = os.getenv('AQICN_API_KEY')

EMISSION_FACTOR = 0.12  

def calculate_emissions(distance_km):
    return round(distance_km * EMISSION_FACTOR, 2)

@app.route('/')
def index():
    return render_template('index1.html', google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/get-routes', methods=['POST'])
def get_routes():
    data = request.json
    start_coords = data['start_coords']
    end_coords = data['end_coords']

    directions_url = f"https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': start_coords,
        'destination': end_coords,
        'alternatives': 'true',
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(directions_url, params=params)
    routes = response.json().get('routes', [])

    # Rank routes based on distance or emissions
    routes = sorted(routes, key=lambda x: (
        x['legs'][0]['distance']['value'],  # Sort by distance
        x['legs'][0]['duration']['value'],  # Then by time
        calculate_emissions(x['legs'][0]['distance']['value'] / 1000)  # Then by emissions
    ))

    route_details = []
    for index, route in enumerate(routes[:3]):
        distance = route['legs'][0]['distance']['value'] / 1000 
        duration = route['legs'][0]['duration']['text']
        emissions = calculate_emissions(distance)
        route_details.append({
            'summary': route['summary'],
            'distance': f"{distance:.2f} km",
            'duration': duration,
            'emissions': f"{emissions} kg CO₂",
            'polyline': route['overview_polyline']['points']
        })

    return jsonify({'routes': route_details})

if __name__ == '__main__':
    app.run(debug=True)