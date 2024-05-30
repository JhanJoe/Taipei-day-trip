from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector

router = APIRouter()

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='mysqlpw',
        database='taipei_day_trip',
        charset='utf8mb4'
    )
    return conn

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

class AttractionsResponse(BaseModel):
    nextPage: Optional[int]
    data: List[Attraction]

@router.get("/api/attractions", response_model=AttractionsResponse)
def get_attractions(page: int = Query(..., ge=0), keyword: Optional[str] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        offset = page * 12
        
        base_query = """
            SELECT
                a.id, 
                a.name, 
                a.category, 
                a.description, 
                a.address, 
                a.transport, 
                a.mrt, 
                a.latitude as lat, 
                a.longitude as lng,
                   GROUP_CONCAT(i.url) as images
            FROM attractions a
            LEFT JOIN images i ON a.attraction_id = i.attraction_id
        """
        
        filters = []
        params = []
        
        if keyword:
            # 添加關鍵字過濾條件
            filters.append("(a.name LIKE %s OR a.mrt = %s)")
            params.append(f"%{keyword}%")
            params.append(keyword)
        
        if filters: 
            base_query += " WHERE " + " AND ".join(filters) 
        
        # 修改查詢語句，取多一條記錄用來判斷是否有下一頁
        base_query += " GROUP BY a.id LIMIT 13 OFFSET %s" 
        params.append(offset) 
        
        cursor.execute(base_query, tuple(params)) 
        attractions = cursor.fetchall() 
        
        # 檢查是否有下一頁（這邊從==改用>是為了避免剛好只有12條資料時也會顯示next_page）
        next_page = page + 1 if len(attractions) > 12 else None 
        
        if len(attractions) > 12:
            attractions = attractions[:12]
        
        # 處理圖片
        for attraction in attractions:
            if attraction["images"]:
                attraction["images"] = [url for url in attraction["images"].split(",")]
            else:
                attraction["images"] = []
        
        return {
            "data": attractions,
            "nextPage": next_page
        }
        

    except Exception:
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")
    finally:
        cursor.close()
        conn.close()
