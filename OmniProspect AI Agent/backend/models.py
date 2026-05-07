from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from beanie import Document

class LeadStatus(str, Enum):
    SCOUTED = "Scouted"
    RESEARCHED = "Researched"
    EMAILED = "Emailed"
    BOOKED = "Booked"
    APPROVED = "Approved"

class User(Document):
    username: str
    password_hash: str
    email: Optional[str] = None
    role: str = "user" # user, admin
    created_at: datetime = datetime.now()

    class Settings:
        name = "users"

class Lead(Document):
    owner_id: str # Liên kết với User ID
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    profile_url: str
    website_url: Optional[str] = None
    status: str = "New"
    research_notes: Optional[List[str]] = None
    draft_email: Optional[str] = None
    created_at: datetime = datetime.now()

    class Settings:
        name = "leads"

class Appointment(Document):
    owner_id: str
    lead_name: str
    company: str
    start_time: str
    meeting_link: Optional[str] = None
    summary: str
    status: str = "Confirmed"

    class Settings:
        name = "appointments"

class AgentMonitor(Document):
    owner_id: str
    agent_name: str
    task_status: str
    progress: int
    action_text: str
    updated_at: datetime = datetime.now()

    class Settings:
        name = "agent_monitor"
