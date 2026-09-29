const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "/login-page";
}


const roomNameInput = document.querySelector("#roomName");
const createRoomButton = document.querySelector("#createRoomButton");
const roomList = document.querySelector("#roomList");
const errorMessage = document.querySelector("#errorMessage");
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

const socket = new WebSocket(
    `${protocol}//${window.location.host}/ws/rooms`
);

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);

    console.log("WebSocket message:", data);

    if (data.type === "room_created") {
        addRoom(data.room);
    }
    if (data.type === "room_deleted") {
        const roomElement = document.querySelector(`[data-room-id="${data.room_id}"]`);
        if (roomElement) {
            roomElement.remove();
        }
    }
};
// =========================
// Load Rooms
// =========================

function addRoom(room) {
    const li = document.createElement("li");
    li.dataset.roomId = room.id;

    li.textContent = room.name + " ";

    const joinButton = document.createElement("button");
    joinButton.textContent = "Join";
    



    joinButton.addEventListener("click", function () {
        window.location.href = "/room/" + room.id;
    });

    li.appendChild(joinButton);
    
    
    const deleteBtn = document.createElement("button");
deleteBtn.textContent = "delete";

deleteBtn.addEventListener("click", async () => {
    const response = await fetch(`/rooms/${room.id}`, {
        method: "DELETE"
    });

    if (response.ok) {
        li.remove();
    }
});
    
    li.appendChild(deleteBtn);
    roomList.appendChild(li);

    

    
}
async function loadRooms() {
    
    try {
        roomList.textContent = "Loading rooms...";
        errorMessage.textContent = "";

        const response = await fetch("/rooms");

        

        if (!response.ok) {
            const data = await response.json();
            console.log("STATUS:", response.status);
            console.log("ERROR:", data.detail);

            errorMessage.textContent = data.detail;

            return;
        }
        const rooms = await response.json();
        roomList.innerHTML = "";
        if (rooms.length === 0) {
            const li = document.createElement("li");
            li.textContent = "No rooms available right now.";
            roomList.appendChild(li);
}
        
        else {
            rooms.forEach(function (room) {
            const li = document.createElement("li");
            li.dataset.roomId = room.id;
            

            li.textContent = room.name + " ";

            const joinButton = document.createElement("button");
            
            joinButton.textContent = "Join";
            const deleteBtn = document.createElement("button");
            deleteBtn.textContent = "delete";
            deleteBtn.addEventListener("click", async () => {
    const response = await fetch(`/rooms/${room.id}`, {
        method: "DELETE"
    });

    if (response.ok) {
        li.remove();
    }

    
});
li.appendChild(deleteBtn);
            joinButton.addEventListener("click", function () {
                window.location.href = "/room/" + room.id;

            
                
                

});

li.appendChild(joinButton);
li.appendChild(deleteBtn);
roomList.appendChild(li);

});
}

    } catch (error) {
        console.error(error);
        errorMessage.textContent = "Unable to connect to Clout. Please try again.";

    }
}

// =========================
// Create Room
// =========================



async function createRoom() {
    try {
        const name = roomNameInput.value.trim();

        if (!name) {
            return;
        }

        const response = await fetch("/rooms", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name
            })
        });
        roomNameInput.value = " "

        const data = await response.json();

        console.log(data);

    } catch (error) {
        console.error(error);
    }
}
    
    

    
createRoomButton.addEventListener("click", createRoom); 
roomNameInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();
        createRoom();
        

    }
});

loadRooms();

