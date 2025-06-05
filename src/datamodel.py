from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Tuple, List, Any
from tortoise.queryset import QuerySet
from tortoise.expressions import Q

class User(Model):
    # 表名默认为小写类名（users）
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50)
    email = fields.CharField(max_length=100, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    # 定义元数据（可选）
    class Meta:
        table = "user"  # 显式指定表名
        ordering = ["-created_at"]  # 默认排序

    # 添加自定义方法
    async def greet(self):
        return f"Hello, {self.name}!"

class DetectionResult(Model):
    id = fields.IntField(pk=True)
    filename = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=255)
    file_type = fields.CharField(max_length=50)
    result = fields.JSONField()
    created_at = fields.DatetimeField(auto_now_add=True)
    course = fields.ForeignKeyField(
        'models.Course', 
    )
class DetectionCount(Model):
    id = fields.IntField(pk=True)
    timestamp = fields.DatetimeField(default=datetime.now)
    lookup_count = fields.IntField()  # 抬头数量
    other_count = fields.IntField()  # 其他状态数量
    course = fields.ForeignKeyField(
        'models.Course', 
        related_name='detections'
    )

class Course(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    teacher = fields.CharField(max_length=50)
    location = fields.CharField(max_length=50)
    start_time = fields.DatetimeField(tz_aware=True)
    end_time = fields.DatetimeField(tz_aware=True)
    week_num = fields.IntField()  # 开学周数
    weekday = fields.IntField()   # 1-7表示周一至周日
    suggestion = fields.TextField(null=True)  # 新增大文本字段
    class_name = fields.CharField(max_length=50)  # 课程类型
    class_size = fields.IntField()  # 班级人数

    class Meta:
        table = "courses"
        indexes = [
            # 联合索引加速时间冲突查询
            ("teacher", "week_num", "weekday", "start_time"),
            ("teacher", "week_num", "weekday", "end_time")
        ]
    @classmethod
    async def paginate_with_count(
        cls,
        page: int = 1,
        page_size: int = 10,
        keyword: str = None,
        location: str = None,
        weekday: int = None,
    ) -> Tuple[QuerySet, int]:
        """
        增强版分页查询
        :param page: 页码
        :param page_size: 每页大小
        :param filters: 过滤条件字典，如 {"name__icontains": "数学"}
        :param order_by: 排序字段，如 "-created_at" 表示倒序
        :return: (当前页数据列表, 总记录数)
        """
        offset = (page - 1) * page_size
        queryset = cls.all()
        
        # 应用过滤条件
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) | 
                Q(teacher__icontains=keyword) |
                Q(location__icontains=keyword) |
                Q(class_name__icontains=keyword)
                
            )
        if location:
            queryset = queryset.filter(location=location)
        if weekday:
            queryset = queryset.filter(weekday=weekday)
        # 获取总数
        total = await queryset.count()
        

        # 获取分页数据

        
        return queryset.offset(offset).limit(page_size), total
