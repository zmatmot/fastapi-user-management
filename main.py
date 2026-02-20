from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import uvicorn

# ==========================================
# 1. Database Configuration
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

# Create the SQLAlchemy engine
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

# Automatically create the 'users' table in the database if it doesn't exist
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. Pydantic Schemas (Data Validation)
# ==========================================
class UserCreate(BaseModel):
    username: str
    email: EmailStr

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
    description="Technical assessment using FastAPI and SQLite (Local)"
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 5. API Endpoints
# ==========================================

# Endpoint: Retrieve all users
@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Fetch a list of all users from the database."""
    users = db.query(UserDB).all()
    return users

# Endpoint: Create a new user
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Add a new user to the database after checking for duplicates."""
    # Check if the username or email already exists
    existing_user = db.query(UserDB).filter(
        (UserDB.username == user.username) | (UserDB.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already exists")
    
    # Save the new user to the database
    new_user = UserDB(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# ==========================================
# 6. Server Execution
# ==========================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)