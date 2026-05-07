import os
import google.generativeai as genai
from models import Lead, Appointment
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    async def detect_intent_and_schedule(self, lead_id: str, customer_message: str):
        """
        Phân tích tin nhắn của khách hàng. Nếu khách đồng ý họp, tự động lên lịch.
        """
        lead = await Lead.get(lead_id)
        if not lead: return

        # Intent Detection Siêu Tinh Gọn
        prompt = f"""
        Phân tích phản hồi: "{customer_message}"
        
        Trả về JSON thuần túy (không text bao quanh):
        {{
            "intent": "[INTERESTED, BUSY, NOT_INTERESTED, QUESTION]",
            "time": "ISO format (nếu INTERESTED và có ngày/giờ, còn lại null)"
        }}
        """
        
        try:
            res = self.model.generate_content(prompt)
            import json
            data = json.loads(res.text.replace("```json", "").replace("```", "").strip())
            
            if data["intent"] == "INTERESTED":
                # 2. Tạo lịch hẹn (ưu tiên thời gian khách đề xuất)
                start_time = data.get("time")
                if not start_time:
                    start_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0)
                else:
                    try:
                        start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    except:
                        start_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0)
                new_app = Appointment(
                    lead_name=lead.name,
                    company=lead.company,
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=30),
                    summary=f"Họp giới thiệu giải pháp AI cho {lead.company}",
                    meeting_link="https://meet.google.com/abc-defg-hij"
                )
                await new_app.insert()
                
                # 3. Gửi thông báo Telegram
                from main import send_telegram_msg
                msg = f"📅 LỊCH HẸN MỚI!\n\nKhách hàng: {lead.name}\nCông ty: {lead.company}\nThời gian: {start_time.strftime('%H:%M %d/%m/%Y')}\nLink Meet: {new_app.meeting_link}"
                import asyncio
                asyncio.create_task(send_telegram_msg(msg))
                
                logger.info(f"AI đã tự động chốt lịch họp và gửi Telegram cho {lead.name}")
                return new_app
            
            return data
        except Exception as e:
            logger.error(f"Lỗi SchedulerAgent: {e}")
            return None
