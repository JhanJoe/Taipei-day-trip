from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from mysql.connector import Error

# 改用 router 執行
router = APIRouter()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='mysqlpw',
            database='taipei_day_trip',
            charset='utf8mb4'
        )
        return conn
    except Error as e:
        print(f"連接 MySQL 錯誤: {e}")
        raise HTTPException(status_code=500, detail="無法連接資料庫")
    
# Response models
class Attraction(BaseModel):
    id: int
    name: str
    category: str
    description: str
    address: str
    transport: str
    mrt: Optional[str]
    lat: float
    lng: float
    images: List[str]

class AttractionResponse(BaseModel):
    data: Attraction

# 改用 routuer 執行
@router.get("/api/attraction/{attractionId}", response_model=AttractionResponse)
async def get_attraction(attractionId: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                a.id,
                a.name,
                a.category,
                a.description,
                a.address,
                a.transport,
                a.mrt,
                a.latitude AS lat,
                a.longitude AS lng,
                GROUP_CONCAT(i.url SEPARATOR ',') AS images
            FROM attractions a
            LEFT JOIN images i ON a.attraction_id = i.attraction_id
            WHERE a.id = %s
            GROUP BY a.id
        """, (attractionId,))

        attraction = cursor.fetchone()

        # 如果查詢結果為空，或不包含id欄位，或id不匹配（eg. id=100或id=25的情況）
        if not attraction or 'id' not in attraction or attraction['id'] != attractionId:
            print(f"沒找到景點編號: {attractionId}")
            raise HTTPException(status_code=400, detail="您輸入的景點編號不存在")

        attraction['images'] = attraction['images'].split(',') if attraction['images'] else []

        return AttractionResponse(data=attraction)

    except Error as e:
        print(f"從 MySQL 獲取資料時出錯: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")
    finally:
        cursor.close()
        conn.close()
