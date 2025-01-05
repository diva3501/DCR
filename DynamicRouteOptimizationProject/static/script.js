document.getElementById('routeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;
    const vehicleType = document.getElementById('vehicle_type').value;

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
