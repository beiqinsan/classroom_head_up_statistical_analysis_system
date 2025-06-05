from fastapi import FastAPI
from config.app_config import lifespan
from fastapi.exceptions import RequestValidationError
from router import userapi, course, aigc_spark, semester, detection, upload
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Tortoise-ORM示例", lifespan=lifespan)  # 创建FastAPI应用
app.include_router(userapi.router)  # 添加路由
app.include_router(course.router)
app.include_router(aigc_spark.router)
app.include_router(semester.router)
app.include_router(detection.router)
app.include_router(upload.router)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/1")
def helloworld():
    return {"message": "Hello, World!"}