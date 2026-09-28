let currentUserId = null;
const path = window.location.pathname;
const parts = path.split("/");

const roomId = Number(parts[2]);
 

const protocol =
    window.location.protocol === "https:" ? "wss:" : "ws:";


const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "/login-page";
}

const ws = new WebSocket(
    `${protocol}//${window.location.host}/ws/${roomId}?token=${encodeURIComponent(token)}`
);

ws.onopen = function () {
    console.log("CHAT WS CONNECTED:", ws.url);
};



ws.onerror = function (error) {
    console.error("CHAT WS ERROR:", error);
};

ws.onclose = function (event) {
    console.log("CHAT WS CLOSED:", event.code, event.reason);
};

ws.onmessage = function (event) {

    const data = JSON.parse(event.data);

    console.log("CHAT SERVER DATA:", data);

    // =========================
    // Chat history
    // =========================

    if (data.type === "chat_history") {

        currentUserId = Number(data.user_id);

        console.log("HISTORY USER ID:", currentUserId);
        console.log("HISTORY DATA:", data);

        data.messages.forEach(function (msg) {

            const message = document.createElement("li");

            message.textContent = `${msg.username}: ${msg.message}`;

            message.classList.add("message");

            if (Number(msg.user_id) === currentUserId) {
                message.classList.add("my-message");
            } else {
                message.classList.add("other-message");
            }

            document
                .getElementById("messages")
                .appendChild(message);
        });
    }

    // =========================
    // New message
    // =========================

    else if (data.type === "message") {

        const message = document.createElement("li");

        message.textContent = `${data.username}: ${data.message}`;

        message.classList.add("message");

        console.log("Message user:", data.user_id);
        console.log("Current user:", currentUserId);

        if (Number(data.user_id) === currentUserId) {
            message.classList.add("my-message");
        } else {
            message.classList.add("other-message");
        }

        document
            .getElementById("messages")
            .appendChild(message);
    }

    // =========================
    // User joined
    // =========================

    else if (data.type === "user_joined") {

        const message = document.createElement("li");

        message.textContent = `${data.username} joined the chat`;

        message.classList.add("system-message");

        document
            .getElementById("messages")
            .appendChild(message);
    }

    // =========================
    // User left
    // =========================

    else if (data.type === "user_left") {

        const message = document.createElement("li");

        message.textContent = `${data.username} left the chat`;

        message.classList.add("system-message");

        document
            .getElementById("messages")
            .appendChild(message);
    }
};
    

const sendButton = document.querySelector("#sendButton");
const input = document.querySelector("#messageText");


input.addEventListener("keydown", function (event) {
if (event.key === "Enter") {
    event.preventDefault();
    sendMessage(); }
});
sendButton.addEventListener("click", sendMessage);

function sendMessage() {
    console.log("sendMessage called");
    const input = document.getElementById("messageText");

    if (!input.value.trim()) {
        return;
    }
    console.log("sending:", input.value);
    console.log("WebSocket state:", ws.readyState);
    ws.send(input.value);

    input.value = "";
}