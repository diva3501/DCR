document.getElementById("routeForm").onsubmit = async (event) => {
    event.preventDefault();

    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;
    const vehicle = document.getElementById("vehicle").value;

    try {
        const response = await fetch("/route", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ start, end, vehicle_type: vehicle }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            document.getElementById("results").innerText = `Error: ${errorData.error}`;
        } else {
            const data = await response.json();
            document.getElementById("results").innerText = JSON.stringify(data, null, 2);
        }
    } catch (error) {
        document.getElementById("results").innerText = `Error: ${error.message}`;
    }
};
