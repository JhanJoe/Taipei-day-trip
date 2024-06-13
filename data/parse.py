import json
import mysql.connector
from dotenv import load_dotenv
import os

current_file_path = os.path.dirname(__file__)
project_root_path = os.path.dirname(current_file_path)
env_path = os.path.join(project_root_path, '.env')
load_dotenv(dotenv_path=env_path)


def load_data():
    with open('data/taipei-attractions.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 從json裡面提取資料，並按照json裡原本的"_id" 排序資料
    sorted_data = sorted(data['result']['results'], key=lambda x: x['_id'])

    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    print("資料庫連接成功")

    cursor = conn.cursor()

    for attraction in sorted_data:
        # 先檢查 id 是否已存在(避免重複加入資料進DB)
        cursor.execute("SELECT COUNT(*) FROM attractions WHERE attraction_id = %s", (attraction['_id'],))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO attractions (attraction_id, name, category, description, address, transport, mrt, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                attraction['_id'],
                attraction['name'],
                attraction['CAT'],
                attraction['description'],
                attraction['address'],
                attraction['direction'],
                attraction['MRT'],
                attraction['latitude'],
                attraction['longitude']
            ))

        attraction_id = attraction['_id']

        image_urls = attraction['file'].split('https://')
        image_urls = ['https://' + url for url in image_urls if url]

        for image_url in image_urls:
            if image_url.lower().endswith(('jpg','png')):
                cursor.execute("""
                    INSERT INTO images (attraction_id, url)
                    VALUES (%s, %s)
                """, (attraction_id, image_url))

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_data()
