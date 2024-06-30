from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_404_NOT_FOUND
from api.api_attractions import router as attractions_router
from api.api_attractionId import router as attractionId_router
from api.api_mrts import router as mrts_router
from api.api_user import router as user_router
from api.api_booking import router as booking_router

app=FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")

app.include_router(attractions_router)
app.include_router(attractionId_router)
app.include_router(mrts_router)
app.include_router(user_router)
app.include_router(booking_router)

# 處理所有的 HTTPException，返回自定義錯誤格式
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail
        }
    )

# 處理所有 RequestValidationError，返回自定義422錯誤格式。
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "您的查詢方式不符合標準 (ERROR: 422)"
        }
    )

# 專門處理 404 錯誤
@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == HTTP_404_NOT_FOUND:
        return JSONResponse(
            status_code=404,
            content={
                "error": True,
                "message": "您的查詢方式不符合標準 (ERROR: 404)"
            }
        )
    return await custom_http_exception_handler(request, exc)

# 處理所有未捕獲的異常，返回自定義的500錯誤格式
@app.exception_handler(Exception)
async def custom_generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "內部伺服器錯誤 (ERROR: 500)"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)