import os
import httpx
import google.generativeai as genai
from models import Lead, LeadStatus
import logging
import json

logger = logging.getLogger(__name__)

import urllib.parse

class ResearcherAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def analyze_lead(self, lead_id: str):
        lead = await Lead.get(lead_id)
        if not lead or not lead.website_url:
            logger.warning(f"Lead {lead_id} không có URL website để nghiên cứu.")
            return

        logger.info(f"Đang nghiên cứu website: {lead.website_url}")
        
        try:
            # 1. Đọc nội dung website và stripping HTML
            async with httpx.AsyncClient() as client:
                # Mã hóa URL để xử lý tên miền có dấu (IDN)
                encoded_url = urllib.parse.quote(lead.website_url, safe=':/')
                reader_url = f"https://r.jina.ai/{encoded_url}"
                response = await client.get(reader_url, timeout=20)
                raw_html = response.text

            # Sử dụng BeautifulSoup để loại bỏ rác
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose() # Xóa sạch tag script và style
            
            # Chỉ giữ lại innerText và loại bỏ khoảng trắng dư thừa
            text = soup.get_text(separator=' ').strip()
            text = " ".join(text.split())
            
            # Loại bỏ Stop-words tiếng Việt cơ bản để tiết kiệm token
            stop_words = ["và", "của", "là", "các", "những", "một", "trong", "cho", "đến", "với", "đã", "đang"]
            words = text.split()
            filtered_words = [w for w in words if w.lower() not in stop_words]
            text = " ".join(filtered_words)

            # Đếm token và cắt bớt nếu > 4000
            token_count = self.model.count_tokens(text).total_tokens
            if token_count > 4000:
                # Cắt bớt theo tỷ lệ ước tính 1 token ~ 4 ký tự để tối ưu tốc độ
                text = text[:16000] 
                logger.info(f"Đã cắt bớt nội dung vì vượt quá giới hạn token: {token_count}")

            web_content = text

            # 2. Sử dụng Gemini với Schema Enforcement & Max Output Tokens
            prompt = f"""
            Nhiệm vụ: Bạn là chuyên gia phân tích dữ liệu tinh gọn cho công ty Tin Học Hùng Việt.
            Trích xuất thông tin từ website khách hàng: {lead.company}
            
            Nội dung:
            {web_content}
            """
            
            res = self.model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "max_output_tokens": 200, # Giới hạn output để tiết kiệm chi phí
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "Pain_Point": {"type": "STRING"},
                            "Latest_News": {"type": "STRING"},
                            "Key_Tech": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["Pain_Point", "Latest_News", "Key_Tech"]
                    }
                }
            )
            
            data = json.loads(res.text)
            
            # 3. Chuyển đổi thành List để tương thích với model hiện tại và lưu vào DB
            # Chúng ta sẽ lưu 3 điểm: Pain Point, Latest News và Tech Stack
            tech_str = ", ".join(data.get("Key_Tech", []))
            notes = [
                f"Vấn đề: {data.get('Pain_Point')}",
                f"Tin mới: {data.get('Latest_News')}",
                f"Công nghệ: {tech_str}"
            ]
            
            lead.research_notes = notes
            lead.status = "Researched"
            await lead.save()
            logger.info(f"Đã phân tích tinh gọn cho lead: {lead.name}")
            
        except Exception as e:
            logger.error(f"Lỗi khi nghiên cứu website: {e}")
            lead.research_notes = ["Không thể truy cập website", "Cần kiểm tra thủ công", "Dữ liệu chưa sẵn sàng"]
            await lead.save()
