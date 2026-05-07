import os
import sys
import logging
import httpx

# Đảm bảo Python tìm được các module nội bộ (database, models, agents)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smtplib
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from celery import Celery

from database import init_db
from models import Lead, Appointment, AgentMonitor, User
from agents.scouter import ScouterAgent
from agents.researcher import ResearcherAgent
from agents.copywriter import CopywriterAgent

# Load environment
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security Config
SECRET_KEY = os.getenv("JWT_SECRET", "omni-prospect-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")
security = HTTPBearer()

app = FastAPI(title="OmniProspect AI Agent API")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "app": "OmniProspect AI Agent API", "version": "1.0.0"}

# Agents
scouter = ScouterAgent()
researcher = ResearcherAgent()
copywriter = CopywriterAgent()

# {owner_id: [agent_status]}
agent_status_db = {}

@app.on_event("startup")
async def startup_event():
    try:
        db_status = await init_db()
        if db_status is None:
            logger.error("❌ Không thể khởi tạo Database. Vui lòng kiểm tra lại MONGODB_URL.")
            return

        # Tự động tạo user admin mặc định nếu chưa có user nào
        admin_user = await User.find_one(User.username == "admin")
        if not admin_user:
            new_admin = User(
                username="admin",
                password_hash=get_password_hash("admin123")
            )
            await new_admin.insert()
            logger.info("✅ Default admin user created: admin/admin123")
    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng trong startup_event: {e}")

# --- Auth Helpers ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        user = await User.find_one(User.username == username)
        if user is None:
            raise HTTPException(status_code=401, detail="User không tồn tại")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

# Celery Instance
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("omniprospect_tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- Default Agent Status (In MongoDB) ---
async def init_user_agents(owner_id: str):
    existing = await AgentMonitor.find(AgentMonitor.owner_id == owner_id).to_list()
    if not existing:
        default_agents = [
            {"agent_name": "Scouter", "task_status": "Ready", "progress": 0, "action_text": "Idle"},
            {"agent_name": "Researcher", "task_status": "Ready", "progress": 0, "action_text": "Idle"},
            {"agent_name": "Copywriter", "task_status": "Ready", "progress": 0, "action_text": "Idle"},
            {"agent_name": "Scheduler", "task_status": "Ready", "progress": 0, "action_text": "Idle"}
        ]
        for a in default_agents:
            await AgentMonitor(owner_id=owner_id, **a).insert()
        return await AgentMonitor.find(AgentMonitor.owner_id == owner_id).to_list()
    return existing

# --- Endpoints: Auth ---
class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/register")
async def register(req: AuthRequest):
    existing = await User.find_one(User.username == req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    user = User(
        username=req.username,
        password_hash=get_password_hash(req.password)
    )
    await user.insert()
    return {"status": "success"}

@app.post("/auth/login")
async def login(req: AuthRequest):
    user = await User.find_one(User.username == req.username)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai username hoặc mật khẩu")
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

# --- Endpoints: Data ---
@app.get("/leads", response_model=List[Lead])
async def get_leads(user: User = Depends(get_current_user)):
    return await Lead.find(Lead.owner_id == str(user.id)).to_list()

@app.get("/appointments")
async def get_appointments(user: User = Depends(get_current_user)):
    return await Appointment.find(Appointment.owner_id == str(user.id)).to_list()

@app.get("/agent-monitor", response_model=List[AgentMonitor])
async def get_agent_status(user: User = Depends(get_current_user)):
    return await init_user_agents(str(user.id))

@app.post("/scout")
async def scout_leads(keyword: str, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    owner_id = str(user.id)
    await init_user_agents(owner_id)
    
    # Kiểm tra hạn mức Demo (10 leads/ngày)
    day_ago = datetime.now() - timedelta(days=1)
    leads_today = await Lead.find(
        Lead.owner_id == owner_id,
        Lead.created_at >= day_ago
    ).count()
    
    if leads_today >= 10:
        raise HTTPException(
            status_code=400, 
            detail=f"Tài khoản Demo đã đạt hạn mức giới hạn (10 leads/24h). Hiện tại bạn đã có {leads_today} leads."
        )

    # Cập nhật trạng thái ban đầu
    monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Scouter")
    if monitor:
        monitor.task_status = f"Queued: {keyword}"
        monitor.progress = 10
        monitor.action_text = "Pending"
        await monitor.save()

    # Chạy trực tiếp bằng BackgroundTasks (không cần Redis/Celery cho Demo)
    background_tasks.add_task(run_scout_background, keyword, owner_id)
    return {"status": "Task Started"}

async def run_scout_background(keyword: str, owner_id: str):
    """Chạy Scouter Agent trực tiếp trong background."""
    try:
        # Cập nhật trạng thái: Đang chạy
        monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Scouter")
        if monitor:
            monitor.task_status = "Running"
            monitor.progress = 30
            monitor.action_text = f"Đang quét: {keyword}"
            await monitor.save()

        # Chạy Scouter (method đúng là run_scouting, nó tự lưu lead vào DB)
        new_count = await scouter.run_scouting(keyword, owner_id)
        
        # Cập nhật trạng thái: Hoàn thành
        if monitor:
            monitor.task_status = "Completed"
            monitor.progress = 100
            monitor.action_text = f"Tìm thấy {new_count} leads mới"
            await monitor.save()
            
        logger.info(f"✅ Scouter hoàn thành: {new_count} leads cho {owner_id}")
    except Exception as e:
        logger.error(f"❌ Scouter lỗi: {e}")
        monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Scouter")
        if monitor:
            monitor.task_status = "Error"
            monitor.progress = 0
            monitor.action_text = str(e)[:100]
            await monitor.save()

@app.post("/research/{lead_id}")
async def research(lead_id: str, user: User = Depends(get_current_user), website_url: Optional[str] = None):
    owner_id = str(user.id)
    await init_user_agents(owner_id)
    
    lead = await Lead.get(lead_id)
    if not lead or lead.owner_id != owner_id:
        raise HTTPException(status_code=404)
    
    if website_url:
        lead.website_url = website_url
        await lead.save()

    # Cập nhật trạng thái Researcher
    monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Researcher")
    if monitor:
        monitor.task_status = "Research Queued"
        monitor.progress = 10
        monitor.action_text = "Pending"
        await monitor.save()

    celery_app.send_task("tasks.run_research", args=[lead_id, website_url, owner_id])
    return {"status": "Task Queued"}

@app.post("/leads/{lead_id}/action")
async def lead_action(lead_id: str, action: str, user: User = Depends(get_current_user)):
    lead = await Lead.get(lead_id)
    if not lead or lead.owner_id != str(user.id):
        raise HTTPException(status_code=404)
        
    if action == "research":
        lead.status = "Researched"
        lead.research_summary = "Website cho thấy họ đang tập trung vào tăng trưởng người dùng. Phù hợp để bán giải pháp AI Automation."
    elif action == "draft":
        lead.status = "email_drafted"
        lead.draft_email = f"Xin chào {lead.name or 'bạn'},\n\nTôi thấy {lead.company} đang phát triển rất tốt. Chúng tôi có giải pháp AI giúp bạn tự động hóa quy trình.\n\nPhản hồi lại email này nếu bạn quan tâm nhé."
    elif action == "schedule":
        lead.status = "Booked"
        # Xóa draft nếu đã lên lịch
        from models import Appointment
        apt = Appointment(
            owner_id=str(user.id),
            lead_name=lead.name or "N/A",
            company=lead.company or "N/A",
            start_time=(datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y 10:00"),
            meeting_link="https://meet.google.com/xyz-demo-link",
            summary=f"Họp giới thiệu AI với {lead.company}"
        )
        await apt.insert()
        
    await lead.save()
    return {"status": "success"}

class ApproveRequest(BaseModel):
    content: str

@app.post("/leads/{lead_id}/approve")
async def approve_lead(lead_id: str, request: ApproveRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    lead = await Lead.get(lead_id)
    if not lead or lead.owner_id != str(user.id):
        raise HTTPException(status_code=404)
    
    lead.draft_email, lead.status = request.content, "Approved"
    await lead.save()
    
    def send_smtp_email(to_email, subject, content):
        smtp_user, smtp_pass = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")
        if not smtp_user or not smtp_pass: return
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = smtp_user, to_email, subject
            msg.attach(MIMEText(content, 'plain'))
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"SMTP Error: {e}")

    background_tasks.add_task(send_smtp_email, lead.profile_url, "Hợp tác kinh doanh", lead.draft_email)
    return {"status": "sent"}

@app.get("/analytics")
async def get_analytics(user: User = Depends(get_current_user)):
    owner_id = str(user.id)
    leads = await Lead.find(Lead.owner_id == owner_id).to_list()
    apps = await Appointment.find(Appointment.owner_id == owner_id).to_list()
    
    new_leads = len([l for l in leads if l.status == "New"])
    researched = len([l for l in leads if l.status == "Researched"])
    approved = len([l for l in leads if l.status == "Approved"])
    
    return {
        "total_leads": len(leads),
        "researched_leads": researched,
        "approved_leads": approved,
        "total_appointments": len(apps),
        "status_distribution": {"New": new_leads, "Researched": researched, "Approved": approved}
    }

@app.post("/test-telegram")
async def test_tg(user: User = Depends(get_current_user)):
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id, "text": f"🚀 OmniProspect Test Notification (Request by {user.username})"})
    return {"status": "ok"}
