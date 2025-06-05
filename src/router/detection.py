from fastapi import APIRouter, Query
from datamodel import DetectionCount
from datetime import datetime
from schemas.detection import DetectionCountResponse

router = APIRouter(tags=["目标检测数据"])

@router.get("/detection")
async def get_detections(course_id: int, start: datetime = None, end: datetime = None):
    query = DetectionCount.filter(course_id=course_id)
    if start:
        query = query.filter(timestamp__gte=start)
    if end:
        query = query.filter(timestamp__lte=end)
    return await query.order_by('-timestamp')