const messageMenu = document.getElementById("messageMenu");
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
            console.log("HISTORY MESSAGE:", msg);

            const message = document.createElement("li");

            message.textContent = `${msg.username}: ${msg.message}`;

            message.classList.add("message");

            message.dataset.messageId = msg.message_id;
            message.dataset.userId = msg.user_id;
            message.dataset.content = msg.message;

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
    // Message deleted
    // =========================

    if (data.type === "message_deleted") {
        const message = document.querySelector(
            `.message[data-message-id="${data.message_id}"]`
        );
        if (message) {
            message.remove();
        }
        return;
    }

    // =========================
    // New message
    // =========================

    else if (data.type === "message") {

        const message = document.createElement("li");

        message.textContent = `${data.username}: ${data.message}`;

        message.classList.add("message");
        
        message.dataset.messageId = data.message_id;
        message.dataset.userId = data.user_id;
        message.dataset.content = data.message;

        console.log("CREATED MESSAGE:", {
            messageId: data.message_id,
            userId: data.user_id,
            element: message
        });

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

    // EDIT MODE
    if (editingMessageId !== null) {
    console.log("EDIT MODE");

    const newContent = input.value.trim();

    console.log("Message ID:", editingMessageId);
    console.log("New content:", newContent);

    fetch(`/rooms/${roomId}/messages/${editingMessageId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            content: newContent
        })
    })
    .then(response => {
        console.log("EDIT RESPONSE STATUS:", response.status);

        if (!response.ok) {
            throw new Error("Failed to edit message");
        }

        return response.json();
    })
    .then(updatedMessage => {
        console.log("MESSAGE UPDATED:", updatedMessage);

        selectedMessage.textContent =
            `${updatedMessage.user_id === currentUserId ? "You" : updatedMessage.user_id}: ${updatedMessage.content}`;

        selectedMessage.dataset.content = updatedMessage.content;

        input.value = "";
        editingMessageId = null;
        selectedMessage = null;
    })
    .catch(error => {
        console.error("EDIT ERROR:", error);
    });

    return;
}

    // NORMAL MESSAGE MODE
    console.log("sending:", input.value);
    console.log("WebSocket state:", ws.readyState);

    ws.send(input.value);

    input.value = "";
}

const backButton = document.getElementById("backButton");
const menuButton = document.getElementById("menuButton");

backButton.addEventListener("click", () => {
    window.location.href = "/";
});

menuButton.addEventListener("click", () => {
    alert("Menu coming soon!");
});

let selectedMessage = null;
let editingMessageId = null;

document.getElementById("messages").addEventListener("contextmenu", function (event) {
    const message = event.target.closest(".message");

    if (!message) {
        return;
    }

    event.preventDefault();

    const messageUserId = Number(message.dataset.userId);

    if (messageUserId !== currentUserId) {
        return;
    }

    selectedMessage = message;

    console.log(
    "Selected message ID:",
    selectedMessage.dataset.messageId
);

    messageMenu.style.display = "flex";

    
});

const editButton = document.getElementById("editMessage");
const deleteButton = document.getElementById("deleteMessage");

editButton.addEventListener("click", function () {
    if (!selectedMessage) {
        return;
    }

    editingMessageId = Number(selectedMessage.dataset.messageId);

    const oldText = selectedMessage.dataset.content;

    input.value = oldText;
    input.focus();

    messageMenu.style.display = "none";

    console.log("Editing:", {
        id: selectedMessage.dataset.messageId,
        content: oldText
    });
});

deleteButton.addEventListener("click", async function () {
    console.log("🔥 DELETE BUTTON CLICKED");

    if (!selectedMessage) {
        console.log("No selected message");
        return;
    }

    const messageId = Number(selectedMessage.dataset.messageId);

    console.log("Deleting message:", messageId);
    console.log("Token exists:", !!token);

    try {
        const response = await fetch(`/messages/${messageId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        console.log("DELETE status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Delete failed:", response.status, errorText);
            return;
        }

        messageMenu.style.display = "none";

        console.log("Message deletion request succeeded.");

    } catch (error) {
        console.error("DELETE request error:", error);
    }
});