from datamodel import User, DetectionResult, DetectionCount, Course
from tortoise.transactions import atomic
from tortoise.exceptions import DoesNotExist
import cv2
import os
import uuid
import threading
from queue import Queue
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import HTTPException, UploadFile, File, APIRouter, Form
from fastapi.responses import JSONResponse
import aiofiles
import utils.yolomodel as yolo

router = APIRouter(tags=["upload"])

@router.post("/upload")
async def upload_and_detect(file: UploadFile = File(...)):
    allowed_types = ["image/jpeg", "image/png", "video/mp4"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, detail="仅支持JPEG/PNG图片或MP4视频")

    file_ext = file.filename.split(".")[-1]
    new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}.{file_ext}"
    save_path = os.path.join("uploads\\temp", new_filename)

    try:
        async with aiofiles.open(save_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)

        if file.content_type == "video/mp4":
            result_filename, result_path, stats = process_video_with_threads(save_path, new_filename)
        else:
            results = yolo.model(save_path)
            stats = count_objects(results)
            result_filename, result_path = generate_image_result(results, new_filename)

        response_data = build_response_data(
            original_file=new_filename,
            result_file=result_filename,
            file_type=file.content_type,
            result_path=result_path,
            stats=stats
        )
        return JSONResponse(content=response_data)

    except Exception as e:
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except PermissionError:
                pass  # 文件可能被其他进程锁定，稍后清理
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

def process_video_with_threads(video_path: str, original_filename: str) -> tuple:
    """多线程优化版视频处理"""
    # 初始化视频参数
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 结果文件配置
    result_filename = f"result_{original_filename.split('.')[0]}.mp4"
    result_path = os.path.join("uploads\\temp", result_filename)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(result_path, fourcc, fps, (width, height))
    print(cv2.cuda.getCudaEnabledDeviceCount())
    # 共享队列
    frame_queue = Queue()  # 控制内存使用
    result_queue = Queue()
    
    # 统计变量（使用线程安全结构）
    stats = {
        "blow_head_count": 0,
        "raise_head_count": 0,
        "other_objects": 0
    }
    stats_lock = threading.Lock()

    # 工作线程定义
    def detection_worker():
        while True:
            frame_data = frame_queue.get()
            if frame_data is None:
                break
            frame_idx, frame = frame_data
            results = yolo.model(source=frame, conf=0.5)
            result_queue.put((frame_idx, results))
            frame_queue.task_done()

    # 启动线程池
    num_workers = 4 # 根据CPU核心数调整
    threads = []
    for _ in range(num_workers):
        t = threading.Thread(target=detection_worker)
        t.start()
        threads.append(t)

    # 主线程：帧读取与结果写入
    detection_interval = int(int(fps)/4)  # 每秒检测4次
    current_write_frame = 0
    pending_results = {}

    for current_frame in range(0, total_frames, detection_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            break
        frame_queue.put((current_frame, frame))

    # 等待所有检测完成
    frame_queue.join()

    # 收集并排序结果
    while not result_queue.empty():
        frame_idx, results = result_queue.get()
        pending_results[frame_idx] = results

    # 按顺序写入视频
    for frame_idx in sorted(pending_results.keys()):
        results = pending_results[frame_idx]
        plotted_frame = results[0].plot() if results else frame
        # 重复写入间隔帧
        for _ in range(detection_interval):
            if current_write_frame >= total_frames:
                break
            out.write(plotted_frame)
            current_write_frame += 1
    
    # 清理线程
    for _ in range(num_workers):
        frame_queue.put(None)
    for t in threads:
        t.join()

    # 统计处理
    for results in pending_results.values():
        if results:
            with stats_lock:
                update_stats(stats, results[0])
    
    stats["total_people"] = sum(stats.values())
    return result_filename, result_path, stats


def update_stats(stats: Dict[str, int], result) -> None:
    """实时更新统计信息"""
    boxes = result.boxes
    for box in boxes:
        class_id = int(box.cls)
        if class_id == 0:
            stats["blow_head_count"] += 1
        elif class_id == 1:
            stats["raise_head_count"] += 1
        elif class_id == 2:
            stats["other_objects"] += 1

def generate_image_result(results, original_filename: str) -> tuple:
    """图片结果生成（保持原逻辑）"""
    result_filename = f"result_{original_filename}"
    result_path = os.path.join("uploads\\temp", result_filename)
    plotted_img = results[0].plot()
    cv2.imwrite(result_path, plotted_img)
    return result_filename, result_path

def build_response_data(original_file: str, result_file: str, file_type: str,result_path: str, stats: Dict) -> Dict:
    """构建响应数据（保持原逻辑）"""
    return {
        "original_file": original_file,
        "result_file": result_file,
        "file_type": file_type,
        "result_path": result_path,
        "stats": stats
    }
def count_objects(results) -> Dict[str, Any]:
    """统计检测结果中的对象数量"""
    stats = {
        "blow_head_count": 0,  # 低头人数
        "raise_head_count": 0,  # 抬头人数
        "total_people": 0,
        "other_objects": 0
    }
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls)
            if class_id == 0:  # 低头
                stats["blow_head_count"] += 1
            elif class_id == 1:  # 抬头
                stats["raise_head_count"] += 1
            elif class_id == 2:  # 转头
                stats["other_objects"] += 1
    
    stats["total_people"] = stats["blow_head_count"] + stats["raise_head_count"] + stats["other_objects"]
    return stats


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    course_id: int = Form(...),
):
    """视频上传与处理端点"""
    # 验证文件类型
    if file.content_type != "video/mp4":
        raise HTTPException(400, "仅支持MP4视频格式")

    # 获取课程信息
    try:
        course = await Course.get(id=course_id)
    except DoesNotExist:
        raise HTTPException(404, f"课程ID {course_id} 不存在")

    # 保存原始视频
    video_id = f"vid_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    save_path = os.path.join("uploads\\course", f"{video_id}.mp4")
    
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(await file.read())

    # 处理视频并保存结果到数据库
    processing_result = await process_video_and_save(
        video_path=save_path,
        course=course,
        original_filename=video_id + ".mp4"
    )

    return {
        "video_id": video_id,
        "processed_seconds": processing_result['total_seconds'],
        "saved_records": processing_result['saved_records'],
        "course_id": course_id
    }

@atomic()
async def process_video_and_save(video_path: str, course: Course, original_filename: str):
    """视频处理核心逻辑"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_seconds = int(total_frames / fps)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    result_filename = f"result_{original_filename.split('.')[0]}.mp4"
    result_path = os.path.join("uploads\\course", result_filename)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(result_path, fourcc, 1, (width, height))
    saved_records = 0

    # 每秒处理一帧
    for second in range(total_seconds):
        # 定位到当前秒的第一帧
        target_frame = int(second * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        ret, frame = cap.read()
        if not ret:
            break

        # 执行检测
        results = yolo.model(source=frame, conf=0.5)
        detection_data = parse_detection_results(results)

        # 计算时间戳
        detection_time = course.start_time + timedelta(seconds=second)
        annotated_frame = draw_detections(frame, results)
        out.write(annotated_frame)
        # 保存到数据库
        await DetectionCount.create(
            timestamp=detection_time,
            lookup_count=detection_data['lookup'],
            other_count=detection_data['other']+detection_data['blow'],
            course=course
        )
        saved_records += 1
    out.release()
    cap.release()
    await DetectionResult.create(
        filename=result_filename,
        file_type="video/mp4",
        file_path=result_path,
        result=detection_data,
        course=course
        )
    return {
        "total_seconds": total_seconds,
        "saved_records": saved_records
    }

def draw_detections(frame, results):
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls)
            conf = box.conf.item()
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            
            # 根据类别设置颜色
            color = (0, 255, 0) if cls_id == 1 else (0, 0, 255)  # 抬头绿色/低头红色
            label = f"{yolo.model.names[cls_id]} {conf:.2f}"
            
            # 绘制边界框和标签
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return frame

def parse_detection_results(results) -> dict:
    """解析YOLO检测结果"""
    counts = {
        "lookup": 0,  # 抬头
        "blow": 0,    # 低头 
        "other": 0    # 其他
    }
    
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls)
            if cls_id == 0:
                counts["blow"] += 1
            elif cls_id == 1:
                counts["lookup"] += 1
            else:
                counts["other"] += 1
                
    return counts
