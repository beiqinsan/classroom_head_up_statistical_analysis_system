from tortoise.contrib.pydantic import pydantic_model_creator
from datamodel import Course
from pydantic import BaseModel,field_validator,ValidationInfo
from typing import List
from datetime import datetime, timedelta,date

Course_Pydantic = pydantic_model_creator(Course, name="Course")
CourseIn_Pydantic = pydantic_model_creator(
    Course, 
    name="CourseIn",
    exclude_readonly=True
)
class CourseOut(BaseModel):
    id: int
    name: str
    teacher: str
    location: str
    start_time: datetime
    end_time: datetime
    week_num: int
    weekday: int
    class_name: str
    class_size: int

    class Config:
        from_attributes = True


class CourseImportItem(BaseModel):
    name: str
    teacher: str
    location: str
    start_time: str  # ISO 8601 格式
    end_time: str
    week_num: int
    weekday: int

class BatchImportResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_items: List[dict]

# 请求模型
class ConflictCheckRequest(BaseModel):
    location: str
    start_time: str  # ISO 8601 格式
    end_time: str    # ISO 8601 格式

# 响应模型
class ConflictCheckResponse(BaseModel):
    conflict: bool
    existing: dict | None  # 冲突课程详情

class WeeklyResponse(BaseModel):
    week_num: int
    start_date: str
    end_date: str
    courses: List[CourseOut]

class CourseUpdate(BaseModel):
    name: str
    teacher: str
    location: str
    start_time: datetime
    end_time: datetime
    week_num: int
    weekday: int
    suggestion: str
    @field_validator('week_num')
    def validate_week_num(cls, v: int, info: ValidationInfo):
        if not 1 <= v <= SEMESTER_CONFIG.total_weeks:
            raise ValueError(f'周数必须在1-{SEMESTER_CONFIG.total_weeks}之间')
        
        start_time = info.data.get('start_time')
        if not start_time:
            raise ValueError('需先验证 start_time 字段')
        
        # 计算学期周数（以学期开始日期为基准）
        semester_start_monday = SEMESTER_CONFIG.start_date - timedelta(days=SEMESTER_CONFIG.start_date.weekday())
        course_monday = start_time.date() - timedelta(days=start_time.weekday())
        semester_week = (course_monday - semester_start_monday).days // 7 + 1
        
        if semester_week != v:
            raise ValueError(f'输入周数 {v} 与实际学期周数 {semester_week} 不符')
        
        return v
    
    @field_validator('weekday')
    def validate_weekday(cls, v: int, info: ValidationInfo):
        if not 1 <= v <= 7:
            raise ValueError('星期值必须在1-7之间')
        
        start_time = info.data.get('start_time')
        if not start_time:
            raise ValueError('需先验证 start_time 字段')
        
        # 统一使用ISO星期值（周一=1，周日=7）
        actual_weekday = start_time.isoweekday()
        if actual_weekday != v:
            raise ValueError(f'输入星期值 {v} 与实际日期星期值 {actual_weekday} 不符')
        
        return v
    
    @field_validator('end_time')
    def validate_time_order(cls, v: datetime, values):
        start_time = values.data.get('start_time')
        if start_time and v <= start_time:
            raise ValueError('结束时间必须晚于开始时间')
        return v

class SuggestionImport(BaseModel):
    id: int
    suggestion: str

class BatchCourseCreate(BaseModel):
    name: str
    teacher: str
    location: str
    start_time: datetime
    end_time: datetime
    week_num: int
    weekday: int
    class_name: str
    class_size: int
    @field_validator('week_num')
    def validate_week_num(cls, v: int, info: ValidationInfo):
        if not 1 <= v <= SEMESTER_CONFIG.total_weeks:
            raise ValueError(f'周数必须在1-{SEMESTER_CONFIG.total_weeks}之间')
        
        start_time = info.data.get('start_time')
        if not start_time:
            raise ValueError('需先验证 start_time 字段')
        
        # 计算学期周数（以学期开始日期为基准）
        semester_start_monday = SEMESTER_CONFIG.start_date - timedelta(days=SEMESTER_CONFIG.start_date.weekday())
        course_monday = start_time.date() - timedelta(days=start_time.weekday())
        semester_week = (course_monday - semester_start_monday).days // 7 + 1
        
        if semester_week != v:
            raise ValueError(f'输入周数 {v} 与实际学期周数 {semester_week} 不符')
        
        return v
    
    @field_validator('weekday')
    def validate_weekday(cls, v: int, info: ValidationInfo):
        if not 1 <= v <= 7:
            raise ValueError('星期值必须在1-7之间')
        
        start_time = info.data.get('start_time')
        if not start_time:
            raise ValueError('需先验证 start_time 字段')
        
        # 统一使用ISO星期值（周一=1，周日=7）
        actual_weekday = start_time.isoweekday()
        if actual_weekday != v:
            raise ValueError(f'输入星期值 {v} 与实际日期星期值 {actual_weekday} 不符')
        
        return v
    
    @field_validator('end_time')
    def validate_time_order(cls, v: datetime, values):
        start_time = values.data.get('start_time')
        if start_time and v <= start_time:
            raise ValueError('结束时间必须晚于开始时间')
        return v
    
class SemesterConfig(BaseModel):
    start_date: date  # 学期开始日期
    total_weeks: int  # 学期总周数（默认20周）

# 全局配置（可从数据库或配置文件中加载）
SEMESTER_CONFIG = SemesterConfig(start_date=date(2025, 3, 3), total_weeks=20)