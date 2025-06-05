from fastapi import HTTPException,APIRouter,Query
from datamodel import Course, DetectionResult
from datetime import datetime, timedelta, timezone
from typing import List
from schemas.course import SuggestionImport,BatchImportResponse,CourseImportItem,Course_Pydantic,ConflictCheckRequest,WeeklyResponse,BatchCourseCreate,ConflictCheckResponse,CourseUpdate
from tortoise.expressions import Q
from isoweek import Week
from tortoise.transactions import in_transaction
from zoneinfo import ZoneInfo 
from dateutil import relativedelta
from tortoise.exceptions import DoesNotExist
router = APIRouter(tags=["课表"])


async def check_time_conflict(teacher, week_num, weekday, location, new_start, new_end):
    # 查询同一老师当周当天的所有课程
    existing = await Course.filter(
        teacher=teacher,
        week_num=week_num,
        weekday=weekday
    )
    
    # 时间重叠检测逻辑
    for course in existing:
        if (new_start < course.end_time) and (new_end > course.start_time):
            raise ValueError(f"教师时间冲突：{course.name} ({course.start_time}-{course.end_time})")
        
    existing_count = await Course.filter(
        location=location,
        week_num=week_num,
        weekday=weekday,
    )

    for course in existing_count:
        if (new_start < course.end_time) and (new_end > course.start_time):
            raise ValueError(f"课室时间冲突：{course.name} ({course.start_time}-{course.end_time})")

@router.get("/courses/video/{course_id}")
async def get_course_video(course_id: int):
    try:
        if not await DetectionResult.filter(course_id=course_id).exists():
            return ''
        course = await DetectionResult.get(course_id=course_id)
        return course.file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/courses/batch")
async def batch_create_courses(courses: List[BatchCourseCreate]):
    try:
        print(courses)
        success_count = 0
        failed_items = []
        
        async with in_transaction():
            for index, course_data in enumerate(courses, start=1):
                try:
                    # 原有名称唯一性检查[1](@ref)
                    exists = await Course.exists(
                        name=course_data.name,
                        week_num=course_data.week_num,
                        weekday=course_data.weekday,
                        teacher=course_data.teacher,
                        class_name=course_data.class_name,
                        start_time=course_data.start_time,
                        end_time=course_data.end_time,
                        location=course_data.location
                    )
                    if exists:
                        raise ValueError("该课程已存在")
                        
                    # 新增时间冲突检测
                    await check_time_conflict(
                        teacher=course_data.teacher,
                        week_num=course_data.week_num,
                        weekday=course_data.weekday,
                        location=course_data.location,
                        new_start=course_data.start_time,
                        new_end=course_data.end_time
                    )
                        
                    await Course.create(**course_data.dict())
                    success_count += 1
                except Exception as e:
                    failed_items.append({
                        "row": index + 1,  # 与前端错误行号对齐
                        "message": str(e).replace("ValueError: ", "")
                    })
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/courses/weekly", response_model=WeeklyResponse)
async def get_weekly_courses(
    week_num: int = Query(..., ge=1, le=53),
    start_date: str = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$")
):
    try:
        # 动态计算年份
        semester_start = datetime(2025, 3, 3, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        # 2. 计算目标周的周一（基于学期起始周）
        target_monday = semester_start + relativedelta.relativedelta(weeks=week_num-1)
        
        # 3. 计算时间范围（东八区 → UTC）
        start = target_monday.astimezone(ZoneInfo("UTC"))
        end = start + relativedelta.relativedelta(days=7)  # 周一00:00到下一周一00:00
        
        # 4. 查询数据库（确保时区一致性）
        courses = await Course.filter(
            start_time__gte=start,
            end_time__lt=end
        ).all()

        return {
            "week_num": week_num,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "courses": [
                {
                    **(await Course_Pydantic.from_tortoise_orm(c)).dict(),
                    "start_time": c.start_time.astimezone(timezone(timedelta(hours=8))).isoformat(),
                    "end_time": c.end_time.astimezone(timezone(timedelta(hours=8))).isoformat()
                } for c in courses
            ]
        }
    except ValueError as e:
        raise HTTPException(400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        raise HTTPException(500, detail=f"服务器内部错误: {str(e)}")


# 按周获取课程
@router.get("/courses/week/{week_num}")
async def get_courses_by_week(week_num: int):
    start_date = datetime.strptime(f"2024-W{week_num}-1", "%Y-W%W-%w")
    end_date = start_date + timedelta(days=6)
    
    # 确保使用正确的查询方法获取查询集（QuerySet）对象
    courses = Course.filter(
        start_time__gte=start_date,
        end_time__lte=end_date
    )
    
    return {
        "week_num": week_num,
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "courses": await Course_Pydantic.from_queryset(courses)
    }

@router.get("/courses/locations")
async def get_locations():
    locations = await Course.all().distinct().values_list("location", flat=True)
    return {"data": list(filter(None, locations))}

@router.get("/courses/list")
async def get_course_list(
    keyword: str = Query(None, description="搜索关键词"),
    location: str = Query(None, description="上课地点"),
    weekday: int = Query(None, ge=1, le=7, description="星期几"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页显示的记录数")
):
    try:
        # 获取分页数据和总数
        courses, total = await Course.paginate_with_count(page=page, page_size=page_size, keyword=keyword, location=location, weekday=weekday)
        if not courses and page > 1:
            raise HTTPException(status_code=404, detail="Page not found")
        return {
            "data": await Course_Pydantic.from_queryset(courses),
            "meta": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

@router.get("/courses/detail/{course_id}", response_model=Course_Pydantic)
async def get_course(course_id: int):
    try:
        course = await Course.get(id=course_id)
        return await Course_Pydantic.from_tortoise_orm(course)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Course not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 创建课程
@router.post("/courses")
async def create_course(course):
    course_obj = await Course.create(**course.dict(exclude_unset=True))
    return await Course_Pydantic.from_tortoise_orm(course_obj)

# 更新课程
@router.patch("/courses/{course_id}")
async def update_course(course_id: int, course: CourseUpdate):
    await Course.filter(id=course_id).update(**course.dict(exclude_unset=True))
    return await Course_Pydantic.from_queryset_single(Course.get(id=course_id))

# 删除课程
@router.delete("/courses/{course_id}")
async def delete_course(course_id: int):
    deleted_count = await Course.filter(id=course_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}


@router.put("/courses/suggestion/{course_id}")
async def suggest_course(course_id: int,suggestion: str):
    await Course.filter(id=course_id).update(suggestion=suggestion)
    return {"message": "Suggestion updated"}

@router.post("/courses/import", response_model=BatchImportResponse)
async def import_courses(items: List[CourseImportItem]):
    success_count = 0
    failed_items = []
    
    for index, item in enumerate(items):
        try:
            # 检查时间冲突
            conflict = await Course.filter(
                location=item.location,
                start_time__lt=item.end_time,
                end_time__gt=item.start_time
            ).exists()
            
            if conflict:
                raise HTTPException(status_code=400, detail="时间地点冲突")
                
            # 创建课程
            await Course.create(**item.dict())
            success_count += 1
        except Exception as e:
            failed_items.append({
                "index": index,
                "data": item.dict(),
                "error": str(e.detail if hasattr(e, 'detail') else e)
            })
    
    return {
        "success_count": success_count,
        "failed_count": len(failed_items),
        "failed_items": failed_items
    }

async def parse_iso_time(time_str: str) -> datetime:
    """安全解析 ISO 时间并转换为 UTC"""
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc)  # 统一使用 UTC 时区
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid time format: {str(e)}")

#
        

@router.post("/check-conflict", response_model=ConflictCheckResponse)
async def check_time(params: ConflictCheckRequest):
    """时间冲突检测核心逻辑"""
    try:
        # 转换并验证时间
        start_time = await parse_iso_time(params.start_time)
        end_time = await parse_iso_time(params.end_time)
        
        if start_time >= end_time:
            raise HTTPException(status_code=422, detail="开始时间不能晚于结束时间")

        # 冲突检测查询条件
        conflict_query = Q(
            Q(location=params.location) &
            (
                Q(start_time__lt=end_time) & Q(end_time__gt=start_time)  # 时间重叠判断
            )
        )

        # 执行查询
        existing = await Course.filter(conflict_query).first()

        return {
            "conflict": existing is not None,
            "existing": existing.to_dict() if existing else None
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"冲突检测失败: {str(e)}"
        )