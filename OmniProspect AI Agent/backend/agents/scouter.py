import os
import httpx
import logging
from models import Lead, LeadStatus
from datetime import datetime

logger = logging.getLogger(__name__)

class ScouterAgent:
    def __init__(self):
        self.api_key = os.getenv("SCRAPER_API_KEY")
        # Ví dụ: Dùng Apify LinkedIn Scraper URL
        self.apify_url = "https://api.apify.com/v2/acts/apify~linkedin-search-scraper/run-sync-get-dataset-items"

    async def run_scouting(self, keyword: str, owner_id: str):
        logger.info(f"Bắt đầu quét Lead với từ khóa: {keyword} cho user: {owner_id}")
        
        # 1. Giả lập hoặc Kết nối API thật
        leads_found = []
        
        if not self.api_key or self.api_key == "your_scraping_api_key_here":
            logger.warning("Chưa có SCRAPER_API_KEY. Sử dụng dữ liệu mẫu để test.")
            # Tạo dữ liệu giả lập dựa trên từ khóa để người dùng thấy kết quả mới
            leads_found = [
                {
                    "name": f"Manager {keyword}", 
                    "title": f"Director of {keyword}", 
                    "company": f"{keyword} Global", 
                    "website": f"https://{keyword.lower().replace(' ', '')}global.com",
                    "url": f"https://linkedin.com/in/{keyword.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
                },
                {
                    "name": f"Lead {keyword}", 
                    "title": f"Expert in {keyword}", 
                    "company": f"Vietnam {keyword} Corp", 
                    "website": f"https://{keyword.lower().replace(' ', '')}corp.vn",
                    "url": f"https://linkedin.com/in/lead_{keyword.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
                }
            ]
        else:
            # Code kết nối Apify thật (Ví dụ)
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        self.apify_url,
                        params={"token": self.api_key},
                        json={"queries": keyword, "limit": 10}
                    )
                    if resp.status_code == 201 or resp.status_code == 200:
                        data = resp.json()
                        # Giả định cấu trúc data từ Apify
                        for item in data:
                            leads_found.append({
                                "name": item.get("name"),
                                "title": item.get("occupation"),
                                "company": item.get("company"),
                                "website": item.get("website"), # Thêm website từ API thật nếu có
                                "url": item.get("url")
                            })
            except Exception as e:
                logger.error(f"Lỗi khi gọi API Scraper: {e}")

        # 2. Logic kiểm tra trùng lặp (Deduplication) và Lưu vào MongoDB
        from models import Appointment # import thêm
        
        new_leads_count = 0
        for i, item in enumerate(leads_found):
            # Kiểm tra xem Profile URL đã tồn tại cho user này chưa
            exists = await Lead.find_one(Lead.profile_url == item["url"], Lead.owner_id == owner_id)
            
            if not exists:
                # Tạo dữ liệu giả lập cho luồng Demo:
                # - Lead 1: Trạng thái email_drafted (Để hiện trong Review Queue)
                # - Lead 2: Trạng thái Booked (Để hiện trong Calendar)
                
                status = "email_drafted" if i == 0 else "Booked"
                draft_email = f"Chào {item['name']},\n\nTôi thấy {item['company']} đang phát triển rất mạnh trong mảng {keyword}. Chúng tôi có một giải pháp AI tự động hóa hoàn toàn phù hợp với định hướng của công ty.\n\nLiệu chúng ta có thể sắp xếp 15 phút trao đổi tuần tới không?\n\nTrân trọng," if i == 0 else None
                
                new_lead = Lead(
                    owner_id=owner_id,
                    name=item["name"],
                    title=item["title"],
                    company=item["company"],
                    profile_url=item["url"],
                    website_url=item.get("website"),
                    status=status,
                    draft_email=draft_email,
                    created_at=datetime.now()
                )
                await new_lead.insert()
                new_leads_count += 1
                logger.info(f"Đã lưu Lead mới cho user {owner_id}: {item['name']} - Status: {status}")
                
                # Nếu là Booked, tạo luôn Lịch hẹn
                if status == "Booked":
                    apt = Appointment(
                        owner_id=owner_id,
                        lead_name=item["name"],
                        company=item["company"],
                        start_time=f"{(datetime.now()).strftime('%d/%m/%Y')} 14:00",
                        meeting_link="https://meet.google.com/abc-xyz-demo",
                        summary=f"Họp giới thiệu giải pháp AI cho {item['company']}",
                        status="Confirmed"
                    )
                    await apt.insert()
            else:
                logger.info(f"Bỏ qua Lead trùng lặp cho user {owner_id}: {item['url']}")

        return new_leads_count
