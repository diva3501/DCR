from flask import Flask, render_template, request, jsonify
import requests
import math
from dotenv import load_dotenv
import os
import datetime
from datetime import date
import mysql.connector
import googlemaps

app = Flask(__name__)
load_dotenv()

db_config = {
    'host': 'localhost',
    'user': 'fedex',
    'password': 'routeopt',
    'database': 'routeopt'
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
AQICN_API_KEY = os.getenv('AQICN_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

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
    mode = data.get('mode')  
    fuel_type = data.get('fuel_type') 
    enable_traffic = data.get('enableTraffic') 

    directions_url = f"https://maps.googleapis.com/maps/api/directions/json"

    driving_options = None
    if enable_traffic:
        driving_options = {
            'departureTime': 'now',
            'trafficModel': 'best_guess'
        }

    params = {
        'origin': start_coords,
        'destination': end_coords,
        'alternatives': 'true',
        'key': GOOGLE_MAPS_API_KEY,
        'mode': mode,
        'drivingOptions': driving_options,
    }
    
    response = requests.get(directions_url, params=params)
    routes = response.json().get('routes', [])

    routes = sorted(routes, key=lambda x: (
        x['legs'][0]['distance']['value'],  
        x['legs'][0]['duration']['value'],  
        calculateemissions(x['legs'][0]['distance']['value'] / 1000, mode, fuel_type)  
    ))

    route_details = []
    for index, route in enumerate(routes[:3]):
        distance = route['legs'][0]['distance']['value'] / 1000  
        duration = route['legs'][0]['duration']['text']
        emissions = calculateemissions(distance, mode, fuel_type)  
        route_details.append({
            'summary': route['summary'],
            'distance': f"{distance:.2f} km",
            'duration': duration,
            'emissions': f"{emissions} kg CO₂",
            'polyline': route['overview_polyline']['points'],
        })

    return jsonify({'routes': route_details})
def calculateemissions(distance_km, mode, fuel_type):
    emission_factors = {
        'DRIVING': {
            'PETROL': 180,  
            'DIESEL': 190,
            'ELECTRIC': 0,
            'CNG': 120,
        },
        'BICYCLING': 0,  
        'TRANSIT': {
            'PETROL': 100,  
            'ELECTRIC': 0,
        },
        'TRUCK': 300, 
    }

    if mode == 'BICYCLING':
        return 0

    if mode in ['DRIVING', 'TRANSIT']:
        emission_factor = emission_factors[mode].get(fuel_type, 0)
    else:
        emission_factor = emission_factors.get(mode, 0)

    emissions = emission_factor * distance_km / 1000  
    return round(emissions, 2)


@app.route('/smart_scheduling')
def smart_schedule_page():
    return render_template('smart_schedule.html', title="Smart Scheduling", google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/smart_scheduling', methods=['POST'])
    
def smart_schedule():
    """Handle smart scheduling requests."""
    try:
        data = request.get_json()
        num_orders = data.get('num_orders', 0)
        priority = data.get('priority', 'medium')
        order_coords = data.get('order_coords', [])

        if not num_orders or not order_coords:
            return jsonify({'error': 'Invalid inputs'}), 400

        all_routes = []
        for order in order_coords:
            start_coords = order['start']
            end_coords = order['end']
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

@app.route('/calculate-multi-routes')
def multirouteplanner():
    return render_template('multirouteplanner.html', title="Multi-Route Planner", google_maps_api_key=GOOGLE_MAPS_API_KEY)


@app.route('/calculate-multi-routes', methods=['POST'])
def calculate_multi_routes():
    """
    Calculate and optimize routes with traffic data for multiple destinations.
    """
    try:
        data = request.get_json()
        start_location = data['start_location']
        destinations = data['destinations']

        routes = []
        for index, destination in enumerate(destinations):
            response = get_route_from_google_maps(start_location, destination)
            for route in response.get('routes', []):
                distance_km = route['legs'][0]['distance']['value'] / 1000  
                duration_traffic = route['legs'][0].get('duration_in_traffic', {}).get('text', route['legs'][0]['duration']['text'])
                emissions = calculate_emissions(distance_km)
                arrival_time = estimate_arrival_time(route['legs'][0]['duration_in_traffic']['value'] if 'duration_in_traffic' in route['legs'][0] else route['legs'][0]['duration']['value'])

                routes.append({
                    'destination': destination,
                    'distance': f"{distance_km:.2f} km",
                    'duration': duration_traffic,
                    'arrival_time': arrival_time,
                    'emissions': f"{emissions:.2f} kg CO₂",
                    'polyline': route['overview_polyline']['points']
                })

        routes = sorted(routes, key=lambda x: (float(x['distance'].split()[0]), float(x['emissions'].split()[0])))

        return jsonify({'routes': routes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_route_from_google_maps(start_coords, end_coords):
    """
    Fetch route information from Google Maps API with real-time traffic data.
    """
    try:
        directions_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            'origin': start_coords,
            'destination': end_coords,
            'key': GOOGLE_MAPS_API_KEY,
            'departure_time': 'now', 
            'alternatives': 'true',
        }
        response = requests.get(directions_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Error in Google Maps API Response: {response.status_code}")
    except Exception as e:
        print(f"Error fetching routes from Google Maps: {e}")
        return {}

def calculate_emissions(distance_km):
    """
    Calculate emissions based on the distance.
    Assume 120g CO₂ per km for a car.
    """
    emission_rate = 0.12  
    return distance_km * emission_rate


def estimate_arrival_time(duration_seconds):
    """
    Estimate arrival time based on the current time and duration.
    """
    from datetime import datetime, timedelta
    current_time = datetime.now()
    arrival_time = current_time + timedelta(seconds=duration_seconds)
    return arrival_time.strftime('%I:%M %p')


@app.route('/deliveryPartner')
def dp():
    return render_template('DeliveryPartner.html', title="Real-Time Delivery Rescheduling System", google_maps_api_key=GOOGLE_MAPS_API_KEY)
    
@app.route('/client')
def client():
    return render_template('client.html', title="Real-Time Delivery Rescheduling System", google_maps_api_key=GOOGLE_MAPS_API_KEY)


@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    productId = data['productId']
    deliveryDate = data['deliveryDate']
    deliveryLocation = data['deliveryLocation']

    cursor.execute(
        "INSERT INTO ClientOrders (productId, deliveryDate, deliveryLocation) VALUES (%s, %s, %s)",
        (productId, deliveryDate, deliveryLocation)
    )
    conn.commit()
    return jsonify({"message": "Order placed successfully!"})

# Endpoint to reschedule an order
@app.route('/reschedule_order', methods=['POST'])
def reschedule_order():
    data = request.get_json()
    order_id = data.get('orderId')
    new_date = data.get('newDate')

    # Validate input
    if not order_id or not new_date:
        return jsonify({'message': 'Order ID and New Date are required'}), 400

    try:
        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Check if the order ID exists
        query_check = "SELECT * FROM clientOrders WHERE productId = %s"
        cursor.execute(query_check, (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({'message': f'Product ID {order_id} does not exist'}), 404

        # Update the delivery date
        query_update = "UPDATE clientOrders SET deliveryDate = %s WHERE productId = %s"
        cursor.execute(query_update, (new_date, order_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': f'Delivery date updated successfully for Product ID {order_id}'}), 200

    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {err}'}), 500

    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

# Endpoint to get delivery partner routes
@app.route('/delivery-partner', methods=['GET'])
def delivery_partner():
    today = date.today().isoformat()
    
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all orders for today's date
    query = "SELECT * FROM clientorders WHERE deliveryDate = %s"
    cursor.execute(query, (today,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        return jsonify({'message': 'No orders found for today'}), 404
    
    delivery_locations = [order['deliveryLocation'] for order in orders]
    
    # Fetch start point (current location) from the frontend
    current_location = request.args.get('currentLocation', '13.0827,80.2707')  # Default to Chennai if not provided
    current_lat, current_lng = map(float, current_location.split(','))
    
    # Calculate the best route using Google Maps API
    waypoints = delivery_locations
    directions_result = gmaps.directions(
        origin=current_location,
        destination=waypoints[-1],
        waypoints=waypoints[:-1],
        optimize_waypoints=True
    )
    
    # Parse the directions result
    route = directions_result[0]
    overview_polyline = route['overview_polyline']['points']
    legs = route['legs']
    
    route_details = {
        'overall_distance': sum(leg['distance']['value'] for leg in legs) / 1000,  # in kilometers
        'overall_time': sum(leg['duration']['value'] for leg in legs) / 60,  # in minutes
        'overall_carbon_emission': round(0.120 * (sum(leg['distance']['value'] for leg in legs) / 1000), 2),  # Approximation
        'polyline': overview_polyline,
        'markers': [{'lat': leg['start_location']['lat'], 'lng': leg['start_location']['lng']} for leg in legs]
    }
    
    detailed_points = []
    for i, order in enumerate(orders):
        leg = legs[i]
        detailed_points.append({
            'productId': order['productId'],
            'estimated_time_reach': leg['duration']['text'],
            'distance_from_origin': leg['distance']['text'],
            'location': order['deliveryLocation']
        })
    
    return jsonify({'route_details': route_details, 'detailed_points': detailed_points})


if __name__ == '__main__':
    app.run(debug=True)