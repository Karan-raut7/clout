const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "/login-page";
}

const roomNameInput = document.querySelector("#roomName");
const createRoomButton = document.querySelector("#createRoomButton");
const roomList = document.querySelector("#roomList");
const dmList = document.querySelector("#dmList");
const userList = document.querySelector("#userList");
const errorMessage = document.querySelector("#errorMessage");

function authHeaders(extra = {}) {
    return { ...extra, Authorization: `Bearer ${token}` };
}

//  Logout 
document.querySelector("#logout").addEventListener("click", () => {
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
        const res = await fetch(`/rooms/${room.id}`, {
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
    const res = await fetch("/rooms", { headers: authHeaders() });
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

    const res = await fetch("/rooms", {
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
    const res = await fetch("/dms", { headers: authHeaders() });
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
            window.location.href = "/room/" + dm.room_id;
        });

        li.appendChild(openBtn);
        dmList.appendChild(li);
    });
}

async function loadUsers() {
    const res = await fetch("/users", { headers: authHeaders() });
    if (!res.ok) return;

    const users = await res.json();
    userList.innerHTML = "";

    users.forEach((user) => {
        const li = document.createElement("li");
        li.textContent = user.username + " ";

        const chatBtn = document.createElement("button");
        chatBtn.textContent = "Message";
        chatBtn.addEventListener("click", async () => {
            const res = await fetch(`/dms/${user.id}`, {
                method: "POST",
                headers: authHeaders(),
            });
            if (!res.ok) {
                errorMessage.textContent = "Couldn't open that chat. Try again.";
                return;
            }
            const data = await res.json();
            window.location.href = "/room/" + data.room_id;
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