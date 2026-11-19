const chatContainer = document.querySelector(".chat-container");

const isDM = chatContainer.dataset.isDm === "true";

let token = localStorage.getItem("access_token");
let ws = null;
let refreshPromise = null;


if (!token) {
    window.location.href = "/login-page";
}

async function refreshAccessToken() {

    if (!refreshPromise) {

        refreshPromise = fetch("/auth/refresh", {
            method: "POST",
            credentials: "same-origin"
        })
        .then(async response => {

            if (!response.ok) {
                throw new Error("Refresh failed");
            }

            const data = await response.json();

            token = data.access_token;
            localStorage.setItem("access_token", token);

            return token;
        })
        .catch(error => {

            localStorage.removeItem("access_token");
            window.location.href = "/login-page";

            throw error;
        })
        .finally(() => {
            refreshPromise = null;
        });
    }

    return refreshPromise;
}


async function apiFetch(url, options = {}) {

    const makeRequest = () => {

        const headers = new Headers(options.headers || {});

        headers.set("Authorization", `Bearer ${token}`);

        return fetch(url, {
            ...options,
            headers,
            credentials: "same-origin"
        });
    };

    let response = await makeRequest();

    if (response.status !== 401) {
        return response;
    }

    await refreshAccessToken();

    return makeRequest();
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
const kind = parts[1];           // "room" or "dm"
const roomId = Number(parts[2]);

if (kind === "dm") {
    apiFetch("/dms")
        .then((res) => res.json())
        .then((dms) => {
            const dm = dms.find((d) => d.thread_id === roomId);
            if (dm) document.getElementById("room-name").textContent = dm.username;
        });
}

const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsPath = kind === "dm" ? `/ws/dm/${roomId}` : `/ws/${roomId}`;



async function connectWebSocket() {

    try {
        
        const response = await apiFetch("/users");

        if (!response.ok) {
            throw new Error("Authentication failed");
        }

        
        ws = new WebSocket(
            `${protocol}//${window.location.host}${wsPath}?token=${encodeURIComponent(token)}`
        );

        ws.onopen = () => {
            console.log("CHAT WS CONNECTED");
        };

        ws.onmessage = handleWebSocketMessage;

        ws.onerror = (error) => {
            console.error("CHAT WS ERROR:", error);
        };

        ws.onclose = (event) => {
            console.log("CHAT WS CLOSED:", event.code, event.reason);
        };

    } catch (error) {
        console.error("WEBSOCKET CONNECTION ERROR:", error);
    }
}

connectWebSocket();

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

function handleWebSocketMessage(event) {
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
    if (data.type === "message_updated") {
    console.log("EDIT EVENT RECEIVED:", data);

    const messageElement = messagesList.querySelector(
        `.message[data-message-id="${data.message_id}"]`
    );

    if (messageElement) {
        messageElement.dataset.content = data.message;

        messageElement.textContent =
            `${messageElement.dataset.username}: ${data.message}`;
    }

    return;
}
};


function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    
    if (editingMessageId !== null) {

    const editUrl = isDM
        ? `/dm/${roomId}/messages/${editingMessageId}`
        : `/rooms/${roomId}/messages/${editingMessageId}`;

    apiFetch(editUrl, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: text }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to edit message");
            }

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

    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error("Socket not open, state:");
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
        const response = await apiFetch(`/rooms/${roomId}/messages/${messageId}`, {
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