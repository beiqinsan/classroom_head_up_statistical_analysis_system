# user_routes.py（原问题中的路由文件）
from fastapi import APIRouter, HTTPException  # 注意这里导入 APIRouter
from datamodel import User
from schemas.user import UserCreate, UserResponse
from tortoise.exceptions import IntegrityError

router = APIRouter(tags=["用户"])  # 创建独立的路由器实例

@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    try:
        user = await User.create(**user_data.model_dump())
        return user
    except IntegrityError as e:
        raise HTTPException(400, detail="邮箱已存在")

@router.get("/users", response_model=list[UserResponse])
async def get_users():
    # 获取所有用户（使用QuerySet API）
    users = await User.all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    # 获取单个用户（带异常处理）
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(404, detail="用户不存在")
    return user

@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    # 删除用户（返回操作结果）
    deleted_count = await User.filter(id=user_id).delete()
    if not deleted_count:
        raise HTTPException(404, detail="用户不存在")
    return {"message": "删除成功"}
