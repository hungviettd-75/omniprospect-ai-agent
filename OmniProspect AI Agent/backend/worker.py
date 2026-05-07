import os
import asyncio
import logging
from celery import Celery
from dotenv import load_dotenv
from database import init_db
from models import User, Lead, AgentMonitor
from agents.scouter import ScouterAgent
from agents.researcher import ResearcherAgent
from agents.copywriter import CopywriterAgent

load_dotenv()

# Cấu hình Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("omniprospect_tasks", broker=REDIS_URL, backend=REDIS_URL)

logger = logging.getLogger(__name__)

# Khởi tạo Agents
scouter = ScouterAgent()
researcher = ResearcherAgent()
copywriter = CopywriterAgent()

def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@celery_app.task(name="tasks.run_scout")
def run_scout_task(keyword, owner_id):
    async def _run():
        await init_db()
        monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Scouter")
        if monitor:
            monitor.task_status = f"Scouting: {keyword}"
            monitor.progress = 30
            monitor.action_text = "Running"
            await monitor.save()
            
        count = await scouter.run_scouting(keyword, owner_id)
        
        if monitor:
            monitor.task_status = f"Found {count} leads"
            monitor.progress = 100
            monitor.action_text = "Done"
            await monitor.save()
        return count
    return run_async(_run())

@celery_app.task(name="tasks.run_research")
def run_research_task(lead_id, website_url, owner_id):
    async def _run():
        await init_db()
        r_monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Researcher")
        c_monitor = await AgentMonitor.find_one(AgentMonitor.owner_id == owner_id, AgentMonitor.agent_name == "Copywriter")
        
        if r_monitor:
            r_monitor.task_status = "Analyzing Web..."
            r_monitor.progress = 40
            r_monitor.action_text = "Running"
            await r_monitor.save()

        await researcher.analyze_lead(lead_id)

        if r_monitor:
            r_monitor.task_status = "Research Done"
            r_monitor.progress = 100
            r_monitor.action_text = "Done"
            await r_monitor.save()

        if c_monitor:
            c_monitor.task_status = "Writing Email..."
            c_monitor.progress = 50
            c_monitor.action_text = "Writing"
            await c_monitor.save()

        await copywriter.generate_email(lead_id)

        if c_monitor:
            c_monitor.task_status = "Email Ready"
            c_monitor.progress = 100
            c_monitor.action_text = "Done"
            await c_monitor.save()
        return True
    return run_async(_run())
