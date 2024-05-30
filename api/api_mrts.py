from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import mysql.connector

router = APIRouter()
class MRTListResponseModel(BaseModel):
    data: list[str]

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='mysqlpw',
        database='taipei_day_trip',
        charset='utf8mb4'
    )

@router.get("/api/mrts", response_model=MRTListResponseModel)
async def get_mrts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""    
            SELECT mrt, COUNT(*) AS attraction_count
            FROM attractions
            WHERE mrt IS NOT NULL
            GROUP BY mrt
            ORDER BY attraction_count DESC
        """)
        mrts_counts = cursor.fetchall()

        mrt_list = [mrt[0] for mrt in mrts_counts]  

        return MRTListResponseModel(data=mrt_list)

    except Exception:
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")
    finally:
        cursor.close()
        conn.close()
