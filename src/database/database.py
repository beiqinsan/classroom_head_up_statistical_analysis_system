from tortoise import Tortoise, fields
from tortoise.models import Model
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

class Settings(BaseSettings):
    load_dotenv()
    mysql_host: str = os.getenv("MYSQL_HOST")
    mysql_port: int = os.getenv("MYSQL_PORT")
    mysql_user: str = os.getenv("MYSQL_USER")
    mysql_password: str = os.getenv("MYSQL_PASSWORD")
    mysql_db: str = os.getenv("MYSQL_DB")

    # ...其他配置同前

settings = Settings()

TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": f"mysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}",

    },
    "apps": {
        "models": {
            "models": ["datamodel"],  # 包含数据模型和迁移模型
            "default_connection": "default",
        }
    },
    "charset": "utf8mb4",
    "use_tz": False,          # 关闭时区支持
    "timezone": "Asia/Shanghai"  # 设置时区
}


async def init_db():
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    await Tortoise.generate_schemas()



async def close_db():
    """关闭数据库连接"""
    # 使用Tortoise的close_connections()方法关闭数据库连接
    await Tortoise.close_connections()