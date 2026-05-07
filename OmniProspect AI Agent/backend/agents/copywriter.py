import os
import google.generativeai as genai
from models import Lead
import logging

logger = logging.getLogger(__name__)

class CopywriterAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_email(self, lead_id: str):
        lead = await Lead.get(lead_id)
        if not lead or not lead.research_notes:
            logger.warning(f"Lead {lead_id} chưa có dữ liệu nghiên cứu để soạn email.")
            return

        logger.info(f"Đang soạn email cho: {lead.name}")
        
        # 3 điểm tin từ Researcher
        notes_str = "\n".join([f"- {note}" for note in lead.research_notes])

        # Master Prompt SDR Pro
        prompt = f"""
        Bạn là một SDR chuyên nghiệp tại Việt Nam. Soạn email cá nhân hóa gửi {lead.name} ({lead.company}).
        
        Dữ liệu nghiên cứu:
        {notes_str}
        
        Cấu trúc bắt buộc:
        Tiêu đề: [Ngắn gọn < 5 từ]
        Hook: [Liên kết trực tiếp tới Tin mới/Latest_News]
        Value: [Giải pháp cho Vấn đề/Pain_Point trong 1 câu]
        CTA: [Gợi ý lịch hẹn 15p]
        
        Yêu cầu tối ưu: 
        - Định dạng Markdown. 
        - Tuyệt đối không dùng sáo rỗng (VD: "Hy vọng email này..."). 
        - Tổng email < 100 tokens. 
        - Ngôn ngữ: Tiếng Việt chuyên nghiệp.
        """
        
        try:
            res = self.model.generate_content(
                prompt,
                generation_config={"max_output_tokens": 250} # Giới hạn email ngắn gọn
            )
            lead.draft_email = res.text
            await lead.save()
            logger.info(f"Đã soạn xong email cho: {lead.name}")
        except Exception as e:
            logger.error(f"Lỗi khi soạn email: {e}")
