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
def dashboard():
    return render_template('dashboard.html', title="Dashboard")

@app.route('/routes')
def routes():
    return render_template('index1.html', title="Route Planner", google_maps_api_key=GOOGLE_MAPS_API_KEY)
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

    routes = sorted(routes, key=lambda x: (
        x['legs'][0]['distance']['value'],  
        x['legs'][0]['duration']['value'],  
        calculate_emissions(x['legs'][0]['distance']['value'] / 1000)  
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

@app.route('/smart_scheduling')
def smart_schedule_page():
    return render_template('smart_schedule.html', title="Smart Scheduling")

@app.route('/smart_scheduling', methods=['POST'])
def smart_schedule():
    """Handle smart scheduling requests."""
    try:
        data = request.get_json()
        
        num_orders = data.get('num_orders', 0)
        priority = data.get('priority', 'medium')
        order_coords = data.get('order_coords', [])
        
        if not num_orders or num_orders <= 0 or not order_coords:
            return jsonify({'error': 'Invalid number of orders or coordinates'}), 400
        
        all_routes = []
        
        for order in order_coords:
            start_coords = order.get('start_coords', '')
            end_coords = order.get('end_coords', '')
            
            google_routes = get_google_routes(start_coords, end_coords)
            tomtom_routes = get_tomtom_routes(start_coords, end_coords)
            
            all_routes.append({
                'start_coords': start_coords,
                'end_coords': end_coords,
                'google_routes': google_routes,
                'tomtom_routes': tomtom_routes
            })
        
        best_routes = optimize_routes(all_routes, num_orders, priority)
        return jsonify({'best_routes': best_routes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_google_routes(start_coords, end_coords):
    """Fetch routes from Google Maps API."""
    try:
        directions_url = f"https://maps.googleapis.com/maps/api/directions/json"
        params = {
            'origin': start_coords,
            'destination': end_coords,
            'alternatives': 'true',
            'key': GOOGLE_MAPS_API_KEY
        }
        response = requests.get(directions_url, params=params)
        if response.status_code == 200:
            return response.json().get('routes', [])
        return []
    except Exception as e:
        print(f"Google Maps API Error: {e}")
        return []

def get_tomtom_routes(start_coords, end_coords):
    """Fetch routes from TomTom API."""
    try:
        tomtom_url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_coords}:{end_coords}/json"
        params = {
            'key': TOMTOM_API_KEY,
            'routeType': 'fastest',
            'traffic': 'true'
        }
        response = requests.get(tomtom_url, params=params)
        if response.status_code == 200:
            return response.json().get('routes', [])
        return []
    except Exception as e:
        print(f"TomTom API Error: {e}")
        return []

def optimize_routes(all_routes, num_orders, priority):
    """Optimize routes based on criteria."""
    best_routes = []
    for route in all_routes:
        route_data = []
        for g_route in route['google_routes'] + route['tomtom_routes']:
            distance = g_route.get('legs', [{}])[0].get('distance', {}).get('value', 0) / 1000
            duration = g_route.get('legs', [{}])[0].get('duration', {}).get('text', 'Unknown')
            emissions = calculate_emissions(distance)
            route_data.append({
                'source': 'Google' if g_route in route['google_routes'] else 'TomTom',
                'summary': g_route.get('summary', 'N/A'),
                'distance': f"{distance:.2f} km",
                'duration': duration,
                'emissions': f"{emissions} kg CO₂",
                'polyline': g_route.get('overview_polyline', {}).get('points', '')
            })

        route_data = sorted(route_data, key=lambda x: (x['distance'], x['emissions']))
        best_routes.append(route_data[:1])  
    return best_routes

if __name__ == '__main__':
    app.run(debug=True)