
function getWebSocketServer() {
    return "ws://" + window.location.hostname + ":5001";
}

function receiveReadings(websocket) {
    websocket.addEventListener("message", ({ data }) => {
        const event = JSON.parse(data);
        document.getElementById("power").innerText = data.power;
    });
}

window.addEventListener("DOMContentLoaded", () => {
    // Open the WebSocket connection and register event handlers.
    const websocket = new WebSocket(getWebSocketServer());
    receiveReadings(websocket);
});