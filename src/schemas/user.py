from pydantic import BaseModel
from datetime import datetime
class UserCreate(BaseModel):
    """用户创建请求模型"""
    name: str
    email: str

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    name: str
    email: str
    created_at: datetime

    # 配置ORM模式支持
    class Config:
        from_attributes = True  # 允许从ORM对象直接转换