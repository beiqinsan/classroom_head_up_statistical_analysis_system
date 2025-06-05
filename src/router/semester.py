from fastapi import HTTPException,APIRouter,Query
from schemas.course import SEMESTER_CONFIG


router = APIRouter(tags=["学期"])  # 创建独立的路由器实例

@router.get("/semester/config")
async def get_semester_config():
    return SEMESTER_CONFIG
