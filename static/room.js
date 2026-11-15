const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "/login-page";
}

const messageMenu = document.getElementById("messageMenu");
const messagesList = document.getElementById("messages");
const input = document.getElementById("messageText");
const sendButton = document.getElementById("sendButton");
const backButton = document.getElementById("backButton");
const menuButton = document.getElementById("menuButton");
const editButton = document.getElementById("editMessage");
const deleteButton = document.getElementById("deleteMessage");

let currentUserId = null;
let selectedMessage = null;
let editingMessageId = null;

const parts = window.location.pathname.split("/");
const roomId = Number(parts[2]);

const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const ws = new WebSocket(
    `${protocol}//${window.location.host}/ws/${roomId}?token=${encodeURIComponent(token)}`
);

ws.onopen = () => console.log("CHAT WS CONNECTED");
ws.onerror = (error) => console.error("CHAT WS ERROR:", error);
ws.onclose = (event) => console.log("CHAT WS CLOSED:", event.code, event.reason);

function addSystemMessage(text) {
    const li = document.createElement("li");
    li.textContent = text;
    li.classList.add("system-message");
    messagesList.appendChild(li);
}

function addChatMessage(msg) {
    const li = document.createElement("li");
    li.textContent = `${msg.username}: ${msg.message}`;
    li.classList.add("message");
    li.dataset.messageId = msg.message_id;
    li.dataset.userId = msg.user_id;
    li.dataset.username = msg.username;
    li.dataset.content = msg.message;

    if (Number(msg.user_id) === currentUserId) {
        li.classList.add("my-message");
    } else {
        li.classList.add("other-message");
    }

    messagesList.appendChild(li);
}

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("CHAT SERVER DATA:", data);

    if (data.type === "chat_history") {
        currentUserId = Number(data.user_id);
        data.messages.forEach(addChatMessage);
        return;
    }

    if (data.type === "message") {
        addChatMessage(data);
        return;
    }

    if (data.type === "message_deleted") {
        const message = messagesList.querySelector(
            `.message[data-message-id="${data.message_id}"]`
        );
        if (message) message.remove();
        return;
    }

    if (data.type === "user_joined") {
        addSystemMessage(`${data.username} joined the chat`);
        return;
    }

    if (data.type === "user_left") {
        addSystemMessage(`${data.username} left the chat`);
        return;
    }
};

//  Sending and editing 
function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // EDIT MODE
    if (editingMessageId !== null) {
        fetch(`/rooms/${roomId}/messages/${editingMessageId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ content: text }),
        })
            .then((response) => {
                if (!response.ok) throw new Error("Failed to edit message");
                return response.json();
            })
            .then((updatedMessage) => {
                selectedMessage.textContent =
                    `${selectedMessage.dataset.username}: ${updatedMessage.content}`;
                selectedMessage.dataset.content = updatedMessage.content;

                input.value = "";
                editingMessageId = null;
                selectedMessage = null;
            })
            .catch((error) => console.error("EDIT ERROR:", error));
        return;
    }

    // NORMAL MESSAGE
    if (ws.readyState !== WebSocket.OPEN) {
        console.error("Socket not open, state:", ws.readyState);
        return;
    }

    ws.send(input.value);
    input.value = "";
}

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});
sendButton.addEventListener("click", sendMessage);

//  Navigation 
backButton.addEventListener("click", () => {
    window.location.href = "/";
});

menuButton.addEventListener("click", () => {
    alert("Menu coming soon!");
});

// Right-click menu for your own messages 
messagesList.addEventListener("contextmenu", (event) => {
    const message = event.target.closest(".message");
    if (!message) return;

    event.preventDefault();

    if (Number(message.dataset.userId) !== currentUserId) return;

    selectedMessage = message;
    messageMenu.style.display = "flex";
});

editButton.addEventListener("click", () => {
    if (!selectedMessage) return;

    editingMessageId = Number(selectedMessage.dataset.messageId);
    input.value = selectedMessage.dataset.content;
    input.focus();
    messageMenu.style.display = "none";
});

deleteButton.addEventListener("click", async () => {
    if (!selectedMessage) return;

    const messageId = Number(selectedMessage.dataset.messageId);

    try {
        const response = await fetch(`/rooms/${roomId}/messages/${messageId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
            console.error("Delete failed:", response.status, await response.text());
            return;
        }

        messageMenu.style.display = "none";
    } catch (error) {
        console.error("DELETE request error:", error);
    }
});