import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Lead, Appointment, User, AgentMonitor

logger = logging.getLogger(__name__)

async def init_db():
    """Khởi tạo kết nối MongoDB và Beanie duy nhất cho toàn ứng dụng."""
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url or "<db_password>" in mongodb_url:
        logger.error("❌ MONGODB_URL chưa được cấu hình đúng trong .env")
        return None

    try:
        client = AsyncIOMotorClient(mongodb_url)
        # Ping thử kết nối
        await client.admin.command('ping')
        
        # Khởi tạo Beanie với tất cả Models
        db_name = mongodb_url.split('/')[-1].split('?')[0] or "omniprospect"
        await init_beanie(database=client[db_name], document_models=[Lead, Appointment, User, AgentMonitor])
        
        logger.info(f"✅ Đã kết nối MongoDB: {db_name}")
        return client
    except Exception as e:
        logger.error(f"❌ Lỗi kết nối MongoDB: {e}")
        return None
