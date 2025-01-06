const map = L.map('map').setView([51.505, -0.09], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

let startMarker, endMarker;
let startLatLng, endLatLng;

function setMapToUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                map.setView([latitude, longitude], 13);
                L.marker([latitude, longitude])
                    .addTo(map)
                    .bindPopup('You are here')
                    .openPopup();
            },
            (error) => {
                console.error("Geolocation error:", error);
                alert("Unable to fetch your location. Please allow location access in your browser.");
            }
        );
    } else {
        alert("Geolocation is not supported by your browser.");
    }
}

setMapToUserLocation();

map.on('click', (e) => {
    if (!startMarker) {
        startLatLng = e.latlng;
        startMarker = L.marker(e.latlng).addTo(map).bindPopup('Start Location').openPopup();
    } else if (!endMarker) {
        endLatLng = e.latlng;
        endMarker = L.marker(e.latlng).addTo(map).bindPopup('End Location').openPopup();
        document.getElementById('start').value = `${startLatLng.lat},${startLatLng.lng}`;
        document.getElementById('end').value = `${endLatLng.lat},${endLatLng.lng}`;
    }
});

const resetMarkers = () => {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    startMarker = null;
    endMarker = null;
    startLatLng = null;
    endLatLng = null;
};

document.getElementById('routeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;
    const vehicleType = document.getElementById('vehicle_type').value;
    const fuelType = document.getElementById('fuel_type').value;

    if (!start || !end) {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').innerText = 'Please select both start and end locations.';
        return;
    }

    try {
        const response = await fetch('/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start, end, vehicle_type: vehicleType, fuel_type: fuelType })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('routeDetails').style.display = 'block';
            document.getElementById('error').style.display = 'none';

            const { route_summary, emissions } = data;
            document.getElementById('routeDetails').innerHTML = `
                <p><strong>Distance:</strong> ${route_summary.distance_km.toFixed(2)} km</p>
                <p><strong>Duration:</strong> ${route_summary.duration_min.toFixed(2)} minutes</p>
                <p><strong>Weather (AQI):</strong> ${route_summary.weather}</p>
                <p><strong>Estimated Emissions:</strong> ${emissions.toFixed(2)} kg CO₂</p>
            `;
        } else {
            throw new Error(data.error || 'An unknown error occurred.');
        }
    } catch (err) {
        document.getElementById('error').style.display = 'block';
        document.getElementById('routeDetails').style.display = 'none';
        document.getElementById('error').innerText = err.message;
    }
});

const packageLoadForm = document.getElementById('packageLoadForm');
if (packageLoadForm) {
    packageLoadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const vehicleCapacity = parseFloat(document.getElementById('vehicle_capacity').value);
        const packageWeight = parseFloat(document.getElementById('package_weight').value);
        const numPackages = parseInt(document.getElementById('num_packages').value, 10);

        if (!vehicleCapacity || !packageWeight || !numPackages) {
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').innerText = 'Please fill in all fields correctly.';
            return;
        }

        document.getElementById('error').style.display = 'none';
        document.getElementById('loadDetails').style.display = 'none';

        try {
            const response = await fetch('/package_load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_capacity: vehicleCapacity, package_weight: packageWeight, num_packages: numPackages })
            });

            const data = await response.json();

            if (response.ok) {
                document.getElementById('loadDetails').style.display = 'block';
                document.getElementById('loadDetails').innerHTML = `
                    <p><strong>Suggested Loads:</strong> ${data.suggested_loads}</p>
                    <p><strong>Remaining Capacity:</strong> ${data.remaining_capacity}</p>
                `;
            } else {
                throw new Error(data.error || 'An unknown error occurred.');
            }
        } catch (err) {
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').innerText = err.message || 'Network error';
        }
    });
}

const smartScheduleForm = document.getElementById('smartScheduleForm');
const calculateButton = document.getElementById('calculateButton');

if (smartScheduleForm && calculateButton) {
    calculateButton.addEventListener('click', async (e) => {
        e.preventDefault();

        const numOrders = parseInt(document.getElementById('num_orders').value, 10);
        const priority = document.getElementById('priority').value.trim();

        if (!numOrders || !priority) {
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').innerText = 'Please fill in all fields correctly.';
            return;
        }

        document.getElementById('error').style.display = 'none';
        document.getElementById('scheduleDetails').style.display = 'none';

        try {
            const response = await fetch('/smart_schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ num_orders: numOrders, priority: priority })
            });

            const data = await response.json();

            if (response.ok) {
                document.getElementById('scheduleDetails').style.display = 'block';
                document.getElementById('scheduleDetails').innerHTML = `
                    <p><strong>Optimal Time to Dispatch:</strong> ${data.best_time}</p>
                    <p><strong>Suggested Priority Levels:</strong> ${data.priority_suggestion}</p>
                `;
            } else {
                throw new Error(data.error || 'An unknown error occurred.');
            }
        } catch (err) {
            document.getElementById('error').style.display = 'block';
            document.getElementById('error').innerText = err.message || 'Network error';
        }
    });
}

