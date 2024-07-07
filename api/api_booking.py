from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from starlette.responses import JSONResponse
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import date
from api.api_user import get_user_status_func

current_file_path = os.path.dirname(__file__)
project_root_path = os.path.dirname(current_file_path)
env_path = os.path.join(project_root_path, '.env')
load_dotenv(dotenv_path=env_path)

router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_user_status(request: Request, token: str = Depends(oauth2_scheme)):
    try:
        request.headers._list.append((b'authorization', f'Bearer {token}'.encode('latin-1')))    
        user = await get_user_status_func(request)
        if not user:
            raise HTTPException(status_code=403, detail="Invalid token or user not authenticated")
        return user
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Exception in verify_user_status: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

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

def decode_token_email(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except InvalidTokenError:
        return None

class GetBookingResponse(BaseModel):
    data: dict

class CreateBookingRequest(BaseModel):
    attractionId: int
    date: str
    time: str
    price: int

class CreateBookingResponse(BaseModel):
    ok: bool

class DeleteBookingResponse(BaseModel):
    ok: bool

# 取得預定資料
@router.get("/api/booking", response_model= GetBookingResponse)
async def get_booking(user: Optional[dict] = Depends(verify_user_status)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        user_email = user["email"]
        
        with get_db_connection() as conn: 
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT 
                        b.email, b.attraction_url_id, b.date, b.time, b.price, b.phone, b.status,
                        a.id, a.attraction_id, a.name, a.address,
                        i.url 
                    FROM 
                        booking b
                    JOIN 
                        attractions a ON b.attraction_url_id = a.id
                    LEFT JOIN
                        images i ON a.attraction_id = i.attraction_id
                    WHERE 
                        b.email = %s AND b.status = '待付款'
                    LIMIT 1
                """
                cursor.execute(query, (user_email,)) 
                booking = cursor.fetchone()

                if not booking:
                    raise HTTPException(status_code=400, detail="找不到預定行程")
                
                # 解決日期格式問題(轉為字符串讓json可以處理)
                if isinstance(booking["date"], date):
                    booking["date"] = booking["date"].isoformat()

                response_data = {
                    "attraction": {
                        "id": booking["attraction_url_id"],
                        "name": booking["name"],
                        "address": booking["address"],
                        "image": booking["url"]
                    },
                    "date": booking["date"],
                    "time": booking["time"],
                    "price": booking["price"],
                }
                return JSONResponse(content={"data": response_data})
    
    except mysql.connector.Error as e:
        print(f"MySQL error: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤: 資料庫錯誤")
    
    except Exception as e:
        print(f"Exception occurred: {e}")
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {e}")


# 建立新的預定行程 
@router.post("/api/booking", response_model= CreateBookingResponse)
async def create_booking(
    request: CreateBookingRequest, 
    user: dict = Depends(verify_user_status)
):
    user_email = user["email"]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO booking (email, attraction_url_id, date, time, price, status) 
                    VALUES (%s, %s, %s, %s, %s, "待付款")
                    ON DUPLICATE KEY UPDATE 
                    attraction_url_id = VALUES(attraction_url_id),
                    date = VALUES(date),
                    time = VALUES(time),
                    price = VALUES(price)
                    """, (user_email, request.attractionId, request.date, request.time, request.price))
                
                conn.commit()
        return CreateBookingResponse(ok=True)

    except Exception as e:
        print(f"Exception occurred: {e}")
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {e}")


# 刪除目前的預定行程 
@router.delete("/api/booking", response_model=DeleteBookingResponse)
async def delete_booking(user: dict = Depends(verify_user_status)): 
    user_email = user["email"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM booking WHERE email = %s", (user_email,))
        conn.commit()

        if cursor.rowcount == 0: 
            raise HTTPException(status_code=400, detail="沒有找到預定行程")

        return DeleteBookingResponse(ok=True)

    except Exception as e:
        print(f"Exception occurred: {e}")
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()