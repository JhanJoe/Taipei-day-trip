from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from starlette.responses import JSONResponse
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
from passlib.context import CryptContext  

current_file_path = os.path.dirname(__file__)
project_root_path = os.path.dirname(current_file_path)
env_path = os.path.join(project_root_path, '.env')
load_dotenv(dotenv_path=env_path)

router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'), 
            charset='utf8mb4'
        )
        return conn
    except Error as e:
        print(f"連接 MySQL 錯誤: {e}")
        raise HTTPException(status_code=500, detail="無法連接資料庫")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict):
    to_encode = data.copy() #將傳入資料字典進行複製，確保不修改原始數據
    expire = datetime.utcnow() + timedelta(days=7)  
    to_encode.update({"exp": expire}) 
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256") 

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms="HS256") 
    except InvalidTokenError: 
        return None

# 打包驗證函數以讓其他api也可以重用
async def get_user_status_func(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        return None
    try:
        token = token.split("Bearer ")[1]
        payload = decode_token(token) 
        if not payload:
            return None
        email = payload.get("sub")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, email FROM user_data WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return None
        return {"id": user[0], "name": user[1], "email": user[2]}
    except jwt.ExpiredSignatureError: #捕獲 JWT 過期錯誤，返回 403 HTTP 異常
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError: #捕獲 JWT 無效錯誤，返回 403 HTTP 異常
        raise HTTPException(status_code=403, detail="Invalid token")
    except Exception as e: #捕獲所有其他異常，返回 500 HTTP 異常
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    ok: bool

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str

class StatusResponse(BaseModel):
    id: int
    name: str
    email: str


# 註冊API 
@router.post("/api/user", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    name = request.name
    email = request.email
    password = request.password

    if not (name and email and password):
        raise HTTPException(status_code=400, detail="姓名、email、密碼不得為空") 
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM user_data WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            raise HTTPException(status_code=400, detail="您欲註冊的email已存在，無法註冊")
        
        hashed_password = hash_password(password)

        cursor.execute("INSERT INTO user_data (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        conn.commit()

        return {"ok": True}

    except HTTPException as http_err:
        raise http_err  
    
    except Exception as e:
        print(f"Exception occurred: {e}")
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {e}")

    finally:
        cursor.close()
        conn.close()

# 登入 API
@router.put("/api/user/auth", response_model=LoginResponse)
async def login(request: LoginRequest):
    email = request.email
    password = request.password

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name, email, password FROM user_data WHERE email = %s", (email,)) 
        user = cursor.fetchone()
        if not user or not verify_password(password, user[2]):
            raise HTTPException(status_code=400, detail="無效的憑證")
        
        token_data = {
            "sub": user[1], 
            "name": user[0]
        } 
        access_token = create_token(token_data)
        return {"token": access_token}

    except HTTPException as http_err:
        print(f"HTTPException occurred: {http_err}")
        raise http_err  
    
    except mysql.connector.Error as db_err:
        print(f"Database error occurred: {db_err}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")
    
    except Exception as e: 
        print(f"Exception occurred: {e}")  
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {e}")


# 登入狀態檢查 API
@router.get("/api/user/auth", response_model=Optional[StatusResponse])
async def get_user_status(request: Request):
    user = await get_user_status_func(request) 
    if user:
        return JSONResponse(content={"data": user})
    return None


