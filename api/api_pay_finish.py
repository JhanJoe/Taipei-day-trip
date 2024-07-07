from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import httpx
from starlette.responses import JSONResponse
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from datetime import datetime
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from api.api_user import get_user_status_func
import random
import string

current_file_path = os.path.dirname(__file__)
project_root_path = os.path.dirname(current_file_path)
env_path = os.path.join(project_root_path, '.env')
load_dotenv(dotenv_path=env_path)

router = APIRouter()

PARTNER_KEY = os.getenv('PARTNER_KEY')
MERCHANT_ID = os.getenv('MERCHANT_ID')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# pay and finish model
class Attraction(BaseModel):
    id: int
    name: str
    address: str
    image: str

class Trip(BaseModel):
    attraction: Attraction
    date: str
    time: str

class Contact(BaseModel):
    name: str
    email: str
    phone: str

class ErrorResponse(BaseModel):
    error: bool
    message: str

# pay model
class Order(BaseModel):
    price: int
    trip: Trip
    contact: Contact

class OrderRequest(BaseModel):
    prime: str
    order: Order

class PaymentResponse(BaseModel):
    status: int
    message: str

class OrderResponseData(BaseModel):
    number: str
    payment: PaymentResponse

class OrderResponse(BaseModel):
    data: OrderResponseData

# finish model
class hasOrdered(BaseModel):
    number: str
    price: int
    trip: Trip
    contact: Contact
    status: int

class hasOrderedResponse(BaseModel):
    data: hasOrdered


    
# 驗證使用者登入狀況
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
    
# 生成訂單號
def generate_order_number(email):
    now = datetime.now()
    random_str = ''.join(random.choices(string.digits, k=8))
    order_number = f"{now.strftime('%Y%m%d%H%M%S')}{email.split('@')[0].upper()}{random_str}"
    return order_number

# 建立付款訂單
@router.post("/api/orders", response_model=OrderResponse)
async def create_order(order_request: OrderRequest, user: str = Depends(verify_user_status)):
    print("建立付款訂單", order_request) 

    # order_request 包含前端發送的所有資料
    prime = order_request.prime
    price = order_request.order.price
    attraction_id = order_request.order.trip.attraction.id
    attraction_name = order_request.order.trip.attraction.name
    contact_email = order_request.order.contact.email
    contact_name = order_request.order.contact.name
    contact_phone = order_request.order.contact.phone

    order_number = generate_order_number(contact_email)
    payment_status = 0 # 用於orders table - status
    payment_message = "付款失敗" 
    
    # 付款請求（to tappay）
    url = "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": PARTNER_KEY
    }

    # 要給tappay的付款請求資料
    payment_data = {
        "prime": prime,
        "partner_key": PARTNER_KEY,
        "merchant_id": MERCHANT_ID,
        "details": "TapPay Test",
        "amount": price,
        "cardholder": {
            "phone_number": contact_phone,
            "name": contact_name,
            "email": contact_email,
        },
        "remember": False
    }

    # 使用httpx.AsyncClient發送請求到 TapPay 的 pay-by-prime 
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payment_data)
            payment_response = response.json() 

            if response.status_code == 200 and payment_response['status'] == 0:
                payment_status = 1
                payment_message = "付款成功"
            else:
                payment_message = payment_response.get('msg', '付款失敗')
    
    except Exception as e:
        print(f"Exception in create_order: {e}")
        payment_message = "付款失敗，請稍後再試"

    # 驗證訂單並更新資料庫
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    """
                    INSERT INTO orders (order_number, email, name, phone, attraction_url_id, date, time, ordercreated_time, amount, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order_number,
                        contact_email,
                        contact_name,
                        contact_phone,
                        attraction_id,
                        order_request.order.trip.date,
                        order_request.order.trip.time,
                        now,
                        price,
                        payment_status
                    )
                )
                conn.commit()

                # 如果付款成功，另更新 booking table 的狀態
                if payment_status == 1:
                    cursor.execute(
                        """
                        UPDATE booking SET status = '已付款'
                        WHERE email = %s AND attraction_url_id = %s AND status = '待付款'
                        """,
                        (contact_email, attraction_id)
                    )
                    conn.commit()

    except Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    
    # 根據付款結果返回回應的資料
    response_data = {
        "data": {
            "number": order_number,
            "payment": {
                "status": payment_status,
                "message": payment_message
            }
        }
    }

    if payment_status == 1:
        return JSONResponse(content=response_data)
    else:
        return JSONResponse(content=response_data, status_code=400)


# 取得訂單資訊 (thankyou.html)
@router.get("/api/order/{order_number}", response_model=hasOrderedResponse, responses={403: {"model": ErrorResponse}})
async def get_order(order_number: str, user: str = Depends(verify_user_status)):
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:       
                cursor.execute("""
                    SELECT o.order_number, o.phone, o.date, o.time, o.ordercreated_time, o.amount, o.status,
                        a.id AS attraction_url_id, a.name AS attraction_name, a.address AS attraction_address,
                        i.url,
                        u.name AS user_name, u.email AS user_email
                    FROM orders o
                    JOIN attractions a ON o.attraction_url_id = a.id
                    JOIN user_data u ON o.email = u.email
                    JOIN 
                        (SELECT attraction_id, MIN(image_id) as min_id
                        FROM images
                        GROUP BY attraction_id) img_min ON a.attraction_id = img_min.attraction_id
                    JOIN
                        images i ON img_min.min_id = i.image_id
                    WHERE o.order_number = %s AND o.email = %s
                """, (order_number, user['email']))

                order = cursor.fetchone()

                if not order:
                    raise HTTPException(status_code=404, detail="Order not found")
                
                # 將 date 轉換為字符串
                date_str = order['date'].strftime('%Y-%m-%d')

                order_data = hasOrdered(
                    number=order['order_number'],
                    price=order['amount'],
                    trip=Trip(
                        attraction=Attraction(
                            id=order['attraction_url_id'],
                            name=order['attraction_name'],
                            address=order['attraction_address'],
                            image=order['url']
                        ),
                        date=date_str,
                        time=order['time']
                    ),
                    contact=Contact(
                        name=order['user_name'],
                        email=order['user_email'],
                        phone=order['phone']
                    ),
                    status=order['status']
                )
                return hasOrderedResponse(data=order_data)
    
    except Exception as e:
        print(f"Exception in get_order: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


