document.getElementById("routeForm").onsubmit = async (event) => {
    event.preventDefault();
    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;
    const vehicle = document.getElementById("vehicle").value;
    const response = await fetch("/route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start, end, vehicle_type: vehicle }),
    });
    const data = await response.json();
    document.getElementById("results").innerText = JSON.stringify(data, null, 2);
};
