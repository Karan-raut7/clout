from fastapi import FastAPI, WebSocket, WebSocketDisconnect,HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Request
import json
from argon2 import PasswordHasher
from sqlalchemy.orm import Session
from models import User, Room, Message
from database import get_db
from security import create_access_token,verify_access_token
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
ph = PasswordHasher()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
password_hasher = PasswordHasher()
class RoomCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    terms_accepted: bool


class UserLogin(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

@app.get("/profile")
def profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    user = db.query(User).filter(
    User.id == int(user_id)
).first()

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }
@app.get("/terms")
async def terms_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="terms.html",
        context={}
    )
@app.get("/privacy")
async def privacy_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="privacy.html",
        context={}
    )

@app.post("/register")
def register(user_data:UserCreate,
             db: Session = Depends(get_db)
             ):
    if not user_data.terms_accepted:
        raise HTTPException(
        status_code=400,
        detail="You must accept the Terms & Conditions"
    )
    existing_user =db.query(User).filter(
        User.username == user_data.username
        ).first()

    if existing_user:
        raise HTTPException(status_code=400,
                            detail="Username already exists"
                            )
    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()
    if existing_email:
        raise HTTPException(status_code=400,detail="Email already exists")
    
    hashed_password = password_hasher.hash(user_data.password)

    new_user = User(
    username=user_data.username,
    email=user_data.email,
    hashed_password=hashed_password,
    terms_accepted=True,
    terms_version="1.0"
)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return{
        "message": "User registered successfully",
        "user_id": new_user.id,
        "username": new_user.username
    }
@app.post("/login")
def login(
    user_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    try:
        password_hasher.verify(
            str(user.hashed_password),
            user_data.password
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
    data={"sub": str(user.id)}
)

    return {
    "access_token": access_token,
    "token_type": "bearer"
}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"message": "Database session works!"}





app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")





class ConnectionManager:

    def __init__(self):
        self.rooms = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()

        if room_id not in self.rooms:
            self.rooms[room_id] = []

        self.rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id not in self.rooms:
            return

        if websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)

        if not self.rooms[room_id]:
            del self.rooms[room_id]

    async def broadcast(self, message: str, room_id: int):
        if room_id not in self.rooms:
            return

        disconnected = []

        for connection in self.rooms[room_id]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection, room_id)


manager = ConnectionManager()




class RoomListManager:

    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.connections:
            await connection.send_text(message)


room_list_manager = RoomListManager()

@app.websocket("/ws/rooms")
async def room_list_websocket(websocket: WebSocket):

    await room_list_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        room_list_manager.disconnect(websocket)

@app.get("/login-page")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request}
    )


@app.post("/rooms")
async def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    existing_room = db.query(Room).filter(
        Room.name == room.name
    ).first()

    if existing_room:
        raise HTTPException(
            status_code=400,
            detail="Room already exists"
        )

    new_room = Room(
        name=room.name
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    room_data = {
        "id": new_room.id,
        "name": new_room.name
    }

    await room_list_manager.broadcast(
        json.dumps({
            "type": "room_created",
            "room": room_data
        })
    )

    return room_data


@app.get("/rooms")
async def get_rooms(
    db: Session = Depends(get_db)
):
    rooms = db.query(Room).all()

    return [
        {
            "id": room.id,
            "name": room.name,
            "users": len(manager.rooms.get(room.id, []))
        }
        for room in rooms
    ]


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={}
)
@app.get("/room/{room_id}")
async def room(request: Request, room_id: int):
    return templates.TemplateResponse(
        request=request,
        name="room.html",
        context={"room_id": room_id}
    )


@app.websocket("/ws/{room_id}")

async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    
    user_id = verify_access_token(token)

    if user_id is None:

        await websocket.close(code=1008)
        return

    user = db.query(User).filter(
        User.id == int(user_id)
        ).first()

    if user is None:
        await websocket.close(code=1008)
        return

    username = user.username
    await manager.connect(websocket,room_id)


# Get previous messages from this room
    messages = db.query(Message).filter(
        Message.room_id == room_id
    ).order_by(
        Message.created_at.asc()
        ).all()

    history = []

    for message in messages:
        message_user = db.query(User).filter(
            User.id == message.user_id
        ).first()

        
        history.append({
        "id": message.id,
        "message": message.content,
        "user_id": message.user_id,
        "username": message_user.username if message_user else "Unknown",
        "created_at": message.created_at.isoformat()
    })


    

    print("CONNECTED TO ROOM",
        room_id,
       
        "USER",
        user_id
        )
    await websocket.send_text(
        json.dumps({
        "type": "chat_history",
        "user_id": int(user_id),
        "messages": history
    })
)

    await manager.broadcast(
    json.dumps({
        "type": "user_joined",
        "username": username
    }),
    room_id
)

    try:
        while True:
           
           message = await websocket.receive_text()

           print("received:", message)

           new_message = Message(
               content=message,

               user_id=int(user_id),
               room_id=room_id
            )
           
           
           db.add(new_message)
           db.commit()
           db.refresh(new_message)

           data = {
               "type": "message",
               "user_id": user_id,
               "username": username,
               "message": message
               }
           await manager.broadcast(
               json.dumps(data),
               room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket,room_id)
    
    await manager.broadcast(
        json.dumps({
        "type": "user_left",
        "username": username
        
    }),
    room_id
)



@app.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(
        Room.id == room_id
    ).first()

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    db.delete(room)
    db.commit()

    await room_list_manager.broadcast(
        json.dumps({
            "type": "room_deleted",
            "room_id": room_id
        })
    )

    return {
        "message": "Room deleted"
    }
