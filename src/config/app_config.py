from database.database import init_db, close_db
from contextlib import asynccontextmanager
from fastapi import FastAPI
#from video_stream import app_state, capture_frames, scheduled_detection
import cv2
import concurrent.futures
import asyncio
import time
from router import upload
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化资源
    await init_db()  # 初始化数据库
    #app_state.cap = cv2.VideoCapture(0)  # 打开摄像头
    #app_state.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)  # 创建线程池
    # 启动后台任务
    """app_state.tasks = [
        asyncio.create_task(capture_frames()),  # 启动帧捕获任务
        asyncio.create_task(scheduled_detection())  # 启动定时检测任务
    ]"""
    #app_state.camera_active.set()  # 设置相机激活标志
    
    yield
    """
    # 关闭流程
    app_state.shutdown_flag.set()  # 设置关闭标志
    app_state.camera_active.clear()  # 清除相机激活标志
    # 取消所有任务
    for task in app_state.tasks:
        task.cancel()
    await asyncio.gather(*app_state.tasks, return_exceptions=True)  # 等待所有任务完成
    # 释放资源
    if app_state.cap and app_state.cap.isOpened():
        app_state.cap.release()  # 释放摄像头
    app_state.thread_pool.shutdown(wait=True)  # 关闭线程池"""
    await close_db()  # 关闭数据库
    
