from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Optional
import uvicorn

# ==========================================
# 1. Database Configuration (SQLite for Local Testing)
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. Database Model
# ==========================================
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

Base.metadata.create_all(bind=engine)

# ==========================================
# 3. Pydantic Schemas (Data Validation)
# ==========================================
class UserCreate(BaseModel):
    username: str
    email: EmailStr

# Schema for updates (fields are optional so users can update specific fields)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

# ==========================================
# 4. FastAPI Application Setup
# ==========================================
app = FastAPI(
    title="User Management API", 
    description="Full CRUD RESTful API using FastAPI and SQLite"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 5. API Endpoints (CRUD Loop)
# ==========================================

# [READ ALL] - Retrieve all users
@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return users

# [READ ONE] - Retrieve a specific user by ID
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# [CREATE] - Create a new user
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(
        (UserDB.username == user.username) | (UserDB.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already exists")
    
    new_user = UserDB(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# [UPDATE] - Update user information by ID
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    # 1. Find the target user in the database
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check if the provided username is already taken by another user
    if user_update.username:
        existing_username = db.query(UserDB).filter(UserDB.username == user_update.username, UserDB.id != user_id).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already exists")
        db_user.username = user_update.username

    # 3. Check if the provided email is already taken by another user
    if user_update.email:
        existing_email = db.query(UserDB).filter(UserDB.email == user_update.email, UserDB.id != user_id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        db_user.email = user_update.email

    db.commit()
    db.refresh(db_user)
    return db_user

# [DELETE] - Delete a user by ID
@app.delete("/users/{user_id}", status_code=200)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return {"message": f"User ID {user_id} has been deleted successfully"}

# ==========================================
# 6. Server Execution
# ==========================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)