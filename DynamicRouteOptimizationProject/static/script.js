// Initialize Leaflet Map
const map = L.map('map').setView([13.0827, 80.2707], 10); // Default location: Chennai

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
}).addTo(map);

let startMarker, endMarker;

// Click event to set start and end points
map.on('click', function (e) {
    if (!startMarker) {
        startMarker = L.marker(e.latlng).addTo(map);
        document.getElementById('start').value = `${e.latlng.lat},${e.latlng.lng}`;
        alert("Start point selected!");
    } else if (!endMarker) {
        endMarker = L.marker(e.latlng).addTo(map);
        document.getElementById('end').value = `${e.latlng.lat},${e.latlng.lng}`;
        alert("End point selected!");
    } else {
        alert("Both points are already selected. Reset the map to change.");
    }
});

// Form submission logic
document.getElementById('routeForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;
    const vehicleType = document.getElementById('vehicle_type').value;

    if (!start || !end) {
        alert("Please select both start and end points on the map.");
        return;
    }

    const response = await fetch('/route', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ start, end, vehicle_type: vehicleType }),
    });

    const data = await response.json();
    const results = document.getElementById('results');
    results.innerHTML = `
        <h4>Route Summary</h4>
        <p><strong>Distance:</strong> ${data.route_summary.lengthInMeters / 1000} km</p>
        <p><strong>Emissions:</strong> ${data.emissions.toFixed(2)} kg</p>
    `;
});
