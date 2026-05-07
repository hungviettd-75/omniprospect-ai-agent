import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Lead, Appointment, LeadStatus

load_dotenv()

async def create_demo_data():
    mongodb_url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(mongodb_url)
    db_name = mongodb_url.split('/')[-1].split('?')[0] or "omniprospect"
    await init_beanie(database=client[db_name], document_models=[Lead, Appointment])

    print("--- Dang don dep du lieu cu ---")
    await Lead.find_all().delete()
    await Appointment.find_all().delete()

    print("--- Dang tao Leads mau ---")
    leads = [
        Lead(
            name="Nguyen Minh Anh",
            title="CEO",
            company="Logistics Pro",
            profile_url="https://linkedin.com/in/minhanh",
            website_url="https://logisticspro.vn",
            status=LeadStatus.SCOUTED,
            created_at=datetime.now()
        ),
        Lead(
            name="Tran Quoc Bao",
            title="Operations Manager",
            company="VinaShip",
            profile_url="https://linkedin.com/in/quocbao",
            website_url="https://vinaship.com.vn",
            status=LeadStatus.RESEARCHED,
            research_notes=[
                "Vấn đề: Chi phí vận tải biển tăng 25% trong quý 1",
                "Tin mới: VinaShip vừa đạt giải thưởng Top 10 Doanh nghiệp Logistics uy tín",
                "Công nghệ: Đang tìm kiếm giải pháp AI để tối ưu lộ trình vận chuyển"
            ],
            draft_email="Tiêu đề: Giải pháp tối ưu lộ trình cho VinaShip\n\nChào anh Bảo,\n\nChúc mừng VinaShip vừa lọt Top 10 Doanh nghiệp Logistics uy tín. Tôi thấy VinaShip đang tìm cách tối ưu lộ trình để giảm 25% chi phí vận tải. \n\nGiải pháp AI SDR của Tin Học Hùng Việt có thể tự động hóa quy trình này giúp anh.\n\nAnh có rảnh 15p sáng mai để tôi demo thực tế không?\n\nTrân trọng.",
            created_at=datetime.now()
        ),
        Lead(
            name="Le Hong Nhung",
            title="Supply Chain Director",
            company="GreenWorld",
            profile_url="https://linkedin.com/in/hongnhung",
            website_url="https://greenworld.com.vn",
            status=LeadStatus.SCOUTED,
            created_at=datetime.now()
        )
    ]
    for l in leads: await l.insert()

    print("--- Dang tao Lich hen mau ---")
    apps = [
        Appointment(
            lead_name="Le Hong Nhung",
            company="GreenWorld",
            start_time=datetime.now() + timedelta(days=1, hours=2),
            end_time=datetime.now() + timedelta(days=1, hours=3),
            summary="Hop demo AI Automation cho GreenWorld",
            meeting_link="https://meet.google.com/abc-defg-hij"
        ),
        Appointment(
            lead_name="Pham Duc Thang",
            company="Thang Loi Express",
            start_time=datetime.now() + timedelta(days=2, hours=1),
            end_time=datetime.now() + timedelta(days=2, hours=2),
            summary="Thao luan hop tac trien khai Chatbot",
            meeting_link="https://meet.google.com/xyz-uvw-rst"
        )
    ]
    for a in apps: await a.insert()

    print("Success: Da khoi tao du lieu Demo!")

if __name__ == "__main__":
    asyncio.run(create_demo_data())
