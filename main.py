from fastapi import FastAPI, WebSocket, WebSocketDisconnect,HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from fastapi import Request
import json
from argon2 import PasswordHasher
from sqlalchemy.orm import Session
from models import User, Room, Message
from database import get_db
from security import create_access_token,verify_access_token,hash_refresh_token
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from database import engine,SessionLocal
from models import Base,Room,User,Message,RoomMember,DMThread,DMMessage
from dotenv import load_dotenv
from sqlalchemy import select
import secrets,hashlib
import datetime as dt
from models import RefreshToken
from sqlalchemy import or_
from fastapi import Response,Cookie
from services.auth_service import create_refresh_token
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime,timezone










from fastapi import Form
load_dotenv()





app = FastAPI()

def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def is_room_member(db: Session, room_id: int, user_id: int) -> bool:
    return db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id
    ).first() is not None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
password_hasher = PasswordHasher()

class RoomCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    terms_accepted: bool

class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)

class EmailRequest(BaseModel):
    email: str


class UserLogin(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Get user ID from JWT
    user_id = verify_access_token(token)

    # Token is invalid or expired
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Find the user in database
    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    # User doesn't exist
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    

    return user


@app.get("/profile")
def profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
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
async def register(
    user_data:UserCreate,
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
        raise HTTPException(status_code=400,
                            detail="Email already exists")
    
    hashed_password = password_hasher.hash(
        user_data.password
        )
    
    

    
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        terms_accepted=True,
        terms_version="1.0",
        
        
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
    response: Response,
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

    try:
        # Generate access token
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )

        # Generate and store refresh token
        refresh_token = create_refresh_token(
            db=db,
            user_id=user.id
        )

        db.commit()

        # Send refresh token through HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Authentication failed"
        )    

@app.post("/auth/refresh")
def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):

    # 1. Check whether cookie exists
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    # 2. Hash incoming token
    token_hash = hash_refresh_token(refresh_token)

    # 3. Find token in database and lock its row
    stored_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    if not stored_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    # 4. Check whether token was already revoked
    if stored_token.revoked_at is not None:

        # Possible token reuse: revoke entire family
        db.query(RefreshToken).filter(
            RefreshToken.family_id == stored_token.family_id
        ).update(
            {
                RefreshToken.revoked_at: datetime.now(timezone.utc)
            },
            synchronize_session=False
        )

        db.commit()

        response.delete_cookie(
            key="refresh_token",
            path="/"
        )

        raise HTTPException(
            status_code=401,
            detail="Refresh token reuse detected"
        )

    # 5. Check expiration
    if stored_token.expires_at <= datetime.now(timezone.utc):
        stored_token.revoked_at = datetime.now(timezone.utc)
        db.commit()

        response.delete_cookie(
            key="refresh_token",
            path="/"
        )

        raise HTTPException(
            status_code=401,
            detail="Refresh token expired"
        )

    try:
        # 6. Generate new access token
        access_token = create_access_token(
            data={"sub": str(stored_token.user_id)}
        )

        # 7. Generate new refresh token
        new_refresh_token = create_refresh_token(
            db=db,
            user_id=stored_token.user_id,
            family_id=stored_token.family_id
        )

        # 8. Revoke old refresh token
        stored_token.revoked_at = datetime.now(timezone.utc)

        # 9. Track replacement token
        stored_token.replaced_by_token_hash = hash_refresh_token(
            new_refresh_token
        )

        db.commit()

        # 10. Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/"
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    

    except Exception:
        db.rollback()
        raise

@app.post("/auth/logout")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)

        stored_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if stored_token:
            stored_token.revoked_at = datetime.now(timezone.utc)
            db.commit()

    response.delete_cookie(
        key="refresh_token",
        path="/"
    )

    return {"message": "Logged out successfully"}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"message": "Database session works!"}





from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

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
dm_manager = ConnectionManager()




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
    rooms = db.query(Room).filter(Room.is_direct.is_(False)).all()

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
async def room(
    request: Request,
    room_id: int,
    db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    return templates.TemplateResponse(
        request=request,
        name="room.html",
        context={"room_id": room_id, 
                 "room_name": room.name
                 }
        
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

    room = db.query(Room).filter(Room.id == room_id).first()

    if room is None:
        await websocket.close(code=1008)
        return

    if room.is_direct and not is_room_member(db, room_id, user.id):
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
        "message_id": message.id,
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
               "message_id": new_message.id,
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

@app.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    message = db.query(Message).filter(
        Message.id == message_id
    ).first()

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own messages"
        )

    
    room_id = message.room_id

    db.delete(message)
    db.commit()

    
    await manager.broadcast(
        json.dumps({
            "type": "message_deleted",
            "message_id": message_id
        }),
        room_id
    )

    return {
        "message": "Message deleted",
        "message_id": message_id
    }

@app.put("/rooms/{room_id}/messages/{message_id}")
def update_message(room_id : int,
                   message_id:int,
                   message: MessageUpdate,
                   db: Session = Depends(get_db),
                   current_user : User = Depends(get_current_user)
                   ):
    
    editable_message = db.query(Message).filter(
        Message.id == message_id,
        Message.room_id == room_id
        ).first()
    

    if editable_message is None:
            raise HTTPException(status_code=404,
                                detail="message doesn't exist"
                                )
    if editable_message.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Message doesn't exist"
        )

    
    
    editable_message.content= message.content
    db.commit()
    db.refresh(editable_message)

    return editable_message




@app.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Private chats can't be deleted, so one person can't wipe out a conversation for both
    if room.is_direct:
        raise HTTPException(status_code=403, detail="Direct chats can't be deleted")

    db.delete(room)
    db.commit()

    await room_list_manager.broadcast(
        json.dumps({
            "type": "room_deleted",
            "room_id": room_id
        })
    )

    return {"message": "Room deleted"}




    


@app.get("/forgot-password-page")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {}
    )

@app.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(User.id != current_user.id).all()
    return [{"id": u.id, "username": u.username} for u in users]



@app.post("/dms/{other_user_id}")
def open_dm(
    other_user_id: int,
    me: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if other_user_id == me.id:
        raise HTTPException(status_code=400, detail="You can't message yourself")
    if db.get(User, other_user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    thread = get_or_create_thread(db, me.id, other_user_id)
    return {"thread_id": thread.id}


@app.get("/dms")
def list_dms(
    me: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    threads = db.query(DMThread).filter(
        or_(DMThread.user_a_id == me.id, DMThread.user_b_id == me.id)
    ).all()

    result = []
    for t in threads:
        other_id = t.user_b_id if t.user_a_id == me.id else t.user_a_id
        other = db.get(User, other_id)
        result.append({"thread_id": t.id, "username": other.username})
    return result

dm_connections: dict[int, set[WebSocket]] = {}

@app.websocket("/ws/dm/{thread_id}")
async def dm_socket(websocket: WebSocket, thread_id: int, token: str):
    user_id = verify_access_token(token)
    if user_id is None:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        thread = db.get(DMThread, thread_id)
        me_id = int(user_id)
        if thread is None or me_id not in (thread.user_a_id, thread.user_b_id):
            await websocket.close(code=1008)
            return

        me = db.get(User, me_id)
        history = (
            db.query(DMMessage)
            .filter(DMMessage.thread_id == thread_id)
            .order_by(DMMessage.id)
            .all()
        )
        await websocket.accept()
        dm_connections.setdefault(thread_id, set()).add(websocket)

        await websocket.send_json({
            "type": "chat_history",
            "user_id": me_id,
            "messages": [
                {
                    "message_id": m.id,
                    "user_id": m.user_id,
                    "username": db.get(User, m.user_id).username,
                    "message": m.content,
                }
                for m in history
            ],
        })

        while True:
            text = await websocket.receive_text()
            msg = DMMessage(thread_id=thread_id, user_id=me_id, content=text)
            db.add(msg)
            db.commit()
            db.refresh(msg)

            payload = {
                "type": "message",
                "message_id": msg.id,
                "user_id": me_id,
                "username": me.username,
                "message": text,
            }
            for conn in list(dm_connections.get(thread_id, [])):
                await conn.send_json(payload)

    except WebSocketDisconnect:
        pass
    finally:
        dm_connections.get(thread_id, set()).discard(websocket)
        db.close()

def get_or_create_thread(db: Session, a: int, b: int) -> DMThread:
    lo, hi = sorted((a, b))
    thread = db.query(DMThread).filter_by(user_a_id=lo, user_b_id=hi).first()
    if thread is None:
        thread = DMThread(user_a_id=lo, user_b_id=hi)
        db.add(thread)
        db.commit()
        db.refresh(thread)
    return thread

@app.get("/dm/{thread_id}")
def dm_page(thread_id: int, request: Request, db: Session = Depends(get_db)):
    thread = db.get(DMThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    return templates.TemplateResponse(request, "room.html", {
        "room_name": "Direct message",
        "room_id": thread_id,
        "is_dm": True,
    })
@app.put("/dm/{thread_id}/messages/{message_id}")
async def update_dm_message(
    thread_id: int,
    message_id: int,
    message: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    thread = db.query(DMThread).filter(
        DMThread.id == thread_id,
        or_(
            DMThread.user_a_id == current_user.id,
            DMThread.user_b_id == current_user.id
        )
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Conversation not found")

    editable_message = db.query(DMMessage).filter(
        DMMessage.id == message_id,
        DMMessage.thread_id == thread_id,
        DMMessage.user_id == current_user.id
    ).first()

    if not editable_message:
        raise HTTPException(status_code=404, detail="Message not found")

    editable_message.content = message.content

    db.commit()
    db.refresh(editable_message)

    # Notify everyone connected to this DM thread
    payload = {
        "type": "message_updated",
        "message_id": editable_message.id,
        "user_id": editable_message.user_id,
        "message": editable_message.content
    }
    print("BROADCASTING EDIT:", payload)
    print("CONNECTED CLIENTS:", len(dm_connections.get(thread_id, set())))

    for conn in list(dm_connections.get(thread_id, set())):
        try:
            await conn.send_json(payload)
        except Exception:
            dm_connections.get(thread_id, set()).discard(conn)

    return {
        "message": "Message updated successfully",
        "message_id": editable_message.id,
        "content": editable_message.content
    }