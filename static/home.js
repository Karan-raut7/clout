
let token = localStorage.getItem("access_token");
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

        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }

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

    // Wait for the shared refresh operation.
    await refreshAccessToken();

    // Retry using the updated access token.
    return makeRequest();

console.log("Access token rejected. Attempting refresh...");
    // Access token expired. Request a new one.
    const refreshResponse = await fetch("/auth/refresh", {
        method: "POST",
        credentials: "same-origin"
    });

    // Refresh failed
    if (!refreshResponse.ok) {
        localStorage.removeItem("access_token");
        window.location.href = "/login-page";
        throw new Error("Session expired");
    }

    // Save new access token
    const refreshData = await refreshResponse.json();

    token = refreshData.access_token;

    localStorage.setItem("access_token", token);

    // Retry original request
    const retryHeaders = new Headers(options.headers || {});

    retryHeaders.set("Authorization", `Bearer ${token}`);

    return fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: "same-origin"
    });
}

const roomNameInput = document.querySelector("#roomName");
const createRoomButton = document.querySelector("#createRoomButton");
const roomList = document.querySelector("#roomList");
const dmList = document.querySelector("#dmList");
const userList = document.querySelector("#userList");
const errorMessage = document.querySelector("#errorMessage");

function authHeaders(extra = {}) {
    return {
        ...extra,
        Authorization: `Bearer ${token}`
    };
}

//  Logout 
// Logout
document.querySelector("#logout").addEventListener("click", async () => {
    try {
        await fetch("/auth/logout", {
            method: "POST",
            credentials: "same-origin"
        });
    } catch (error) {
        console.error("Logout error:", error);
    }

    localStorage.removeItem("access_token");
    window.location.href = "/login-page";
});

// Tabs: Private Chats / Groups 
const tabs = document.querySelectorAll(".tab");
const sections = {
    private: document.querySelector("#private-section"),
    groups: document.querySelector("#groups-section"),
};

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.toggle("active", t === tab));
        Object.entries(sections).forEach(([key, el]) => {
            el.classList.toggle("active", key === tab.dataset.tab);
        });
    });
});

//  Rooms 
function buildRoomItem(room) {
    const li = document.createElement("li");
    li.dataset.roomId = room.id;
    li.textContent = room.name + " ";

    const joinButton = document.createElement("button");
    joinButton.textContent = "Join";
    joinButton.addEventListener("click", () => {
        window.location.href = "/room/" + room.id;
    });

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "delete";
    deleteBtn.addEventListener("click", async () => {
        const res = await apiFetch(`/rooms/${room.id}`, {
            method: "DELETE",
            headers: authHeaders(),
        });
        if (res.ok) li.remove();
    });

    li.append(joinButton, deleteBtn);
    return li;
}

function addRoom(room) {
    roomList.appendChild(buildRoomItem(room));
}

async function loadRooms() {
    const res = await apiFetch("/rooms", { headers: authHeaders() });
    if (!res.ok) return;

    const rooms = await res.json();
    roomList.innerHTML = "";

    if (rooms.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No rooms available right now.";
        roomList.appendChild(li);
        return;
    }

    rooms.forEach((room) => addRoom(room));
}

async function createRoom() {
    const name = roomNameInput.value.trim();
    if (!name) {
        errorMessage.textContent = "Room name is required";
        return;
    }

    const res = await apiFetch("/rooms", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ name }),
    });

    const data = await res.json();
    if (!res.ok) {
        errorMessage.textContent = data.detail || "Could not create room";
        return;
    }

    roomNameInput.value = "";
}

createRoomButton.addEventListener("click", createRoom);
roomNameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        createRoom();
    }
});

//  Live updates over WebSocket 
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const socket = new WebSocket(`${protocol}//${window.location.host}/ws/rooms`);

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "room_created") {
        addRoom(data.room);
    }

    if (data.type === "room_deleted") {
        const roomElement = roomList.querySelector(`[data-room-id="${data.room_id}"]`);
        if (roomElement) roomElement.remove();
    }
};

//  Direct messages and users 
async function loadDirectMessages() {
    const res = await apiFetch("/dms", { headers: authHeaders() });
    if (!res.ok) return;

    const dms = await res.json();
    dmList.innerHTML = "";

    if (dms.length === 0) {
        dmList.innerHTML = "<li>No chats yet.</li>";
        return;
    }

    dms.forEach((dm) => {
        const li = document.createElement("li");
        li.textContent = dm.username + " ";

        const openBtn = document.createElement("button");
        openBtn.textContent = "Open";
        openBtn.addEventListener("click", () => {
            window.location.href = "/dm/" + dm.thread_id;
        });

        li.appendChild(openBtn);
        dmList.appendChild(li);
    });
}

async function loadUsers() {
    const res = await apiFetch("/users", { headers: authHeaders() });
    if (!res.ok) return;

    const users = await res.json();
    userList.innerHTML = "";

    users.forEach((user) => {
        const li = document.createElement("li");
        li.textContent = user.username + " ";

        const chatBtn = document.createElement("button");
        chatBtn.textContent = "Message";
        chatBtn.addEventListener("click", async () => {
            const res = await apiFetch(`/dms/${user.id}`, {
                method: "POST",
                headers: authHeaders(),
            });
            if (!res.ok) {
                errorMessage.textContent = "Couldn't open that chat. Try again.";
                return;
            }
            const data = await res.json();
            window.location.href = "/dm/" + data.thread_id;
        });

        li.appendChild(chatBtn);
        userList.appendChild(li);
    });
}

// ---------- Filters ----------
document.querySelectorAll(".filter-btn[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");
        console.log("Selected filter:", button.dataset.filter);
    });
});

// ---------- Startup ----------
if (token) {
    loadRooms();
    loadDirectMessages();
    loadUsers();
}