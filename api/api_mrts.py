from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import mysql.connector
from dotenv import load_dotenv
import os

current_file_path = os.path.dirname(__file__)
project_root_path = os.path.dirname(current_file_path)
env_path = os.path.join(project_root_path, '.env')
load_dotenv(dotenv_path=env_path)

router = APIRouter()
class MRTListResponseModel(BaseModel):
    data: list[str]

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
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
