import streamlit as st
import requests
import os
import time
import extra_streamlit_components as stx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# =============================================
# INITIALIZATION & CONFIG
# =============================================
st.set_page_config(
    page_title="OmniProspect AI Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo Session State ngay lập tức
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "Landing"

cookie_manager = stx.CookieManager()

# Auto-login from cookies
try:
    cookies = cookie_manager.get_all()
    if not st.session_state.authenticated and cookies:
        saved_token = cookies.get("omni_token")
        saved_user = cookies.get("omni_user")
        if saved_token and saved_user:
            st.session_state.token = saved_token
            st.session_state.username = saved_user
            st.session_state.authenticated = True
except:
    pass

# =============================================
# CSS - PREMIUM DESIGN SYSTEM (ULTIMATE)
# =============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #0d21a1;
    --primary-light: #eef2ff;
    --accent: #4ade80;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --glass-bg: rgba(255, 255, 255, 0.9);
    --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

.stApp { 
    background: radial-gradient(circle at top right, #f1f5f9, #f8fafc) !important;
    font-family: 'Inter', sans-serif !important; 
}

/* === SIDEBAR STYLING === */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 14px 18px !important;
    border-radius: 12px !important;
    margin: 4px 12px !important;
    transition: all 0.2s ease !important;
    color: var(--text-muted) !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--primary-light) !important;
    color: var(--primary) !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: var(--primary-light) !important;
    color: var(--primary) !important;
    font-weight: 700 !important;
    box-shadow: inset 4px 0 0 var(--primary);
}

/* === TÙY BIẾN NÚT MŨI TÊN (SIDEBAR TOGGLE) === */
[data-testid="collapsedControl"] {
    display: flex !important;
    background-color: #0d21a1 !important; /* Màu xanh đậm Omni */
    color: white !important;
    border-radius: 0 15px 15px 0 !important;
    width: 55px !important;
    height: 55px !important;
    top: 25px !important;
    left: 0px !important;
    z-index: 1000000 !important;
    box-shadow: 4px 0 15px rgba(13, 33, 161, 0.4) !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
}

[data-testid="collapsedControl"]:hover {
    width: 65px !important;
    background-color: #0b1a7a !important;
}

[data-testid="collapsedControl"] button {
    color: white !important;
    scale: 1.8 !important; /* Làm mũi tên to hẳn lên */
    margin-left: 5px !important;
}

/* Tùy biến nút đóng (<) khi sidebar đang mở */
button[kind="headerNoPadding"] {
    background-color: #f1f5f9 !important;
    border-radius: 50% !important;
    color: #0d21a1 !important;
    margin-right: 10px !important;
    transition: transform 0.3s ease !important;
}
button[kind="headerNoPadding"]:hover {
    transform: scale(1.1) rotate(-90deg);
    background-color: #e2e8f0 !important;
}

/* === PREMIUM CARDS === */
.card {
    background: var(--glass-bg);
    backdrop-filter: blur(15px);
    border-radius: 24px;
    padding: 30px;
    box-shadow: var(--card-shadow);
    margin-bottom: 24px;
    border: 1px solid rgba(255, 255, 255, 0.6);
}

.stat-card {
    background: white;
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid #f1f5f9;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.text-gradient {
    background: linear-gradient(90deg, #0d21a1, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* === SỬA LỖI ẨN NÚT ĐIỀU KHIỂN === */
header[data-testid="stHeader"] {
    background: transparent !important;
}

#MainMenu, footer { 
    visibility: hidden; 
}

/* Đảm bảo nút mũi tên luôn nằm trên cùng và không bị ẩn */
[data-testid="collapsedControl"] {
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================
# HELPERS
# =============================================
def logout():
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.username = None
    cookie_manager.delete("omni_token")
    cookie_manager.delete("omni_user")
    st.rerun()

def auth_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

# =============================================
# SIDEBAR NAVIGATION
# =============================================
with st.sidebar:
    st.markdown("""<div style="padding: 20px 0; text-align: center;">
<div style="display: inline-flex; align-items: center; justify-content: center; width: 50px; height: 50px; background: #0d21a1; border-radius: 12px; color: white; font-size: 24px; font-weight: 800; margin-bottom: 10px;">O</div>
<h2 style="margin: 0; font-size: 20px; font-weight: 800;">OmniProspect</h2>
<p style="margin: 0; font-size: 10px; color: #64748b; letter-spacing: 1px; text-transform: uppercase;">Enterprise AI Hub</p>
</div>""", unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        st.markdown(f"""<div style="background: var(--primary-light); padding: 12px; border-radius: 12px; margin: 10px 12px 20px; display: flex; align-items: center; gap: 10px;">
        <div style="width: 32px; height: 32px; background: var(--primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; font-weight: 700;">{st.session_state.username[0].upper() if st.session_state.username else 'U'}</div>
        <div style="flex: 1;">
            <div style="font-size: 12px; font-weight: 700;">{st.session_state.username}</div>
            <div style="font-size: 10px; color: var(--text-muted);">Standard Account</div>
        </div>
    </div>""", unsafe_allow_html=True)

        menu_map = {
            "📊  Dashboard": "Dashboard",
            "🤖  Agents Monitor": "Agents",
            "📈  Analytics": "Analytics",
            "📣  Campaigns": "Campaign",
            "👥  Leads Database": "Leads",
            "📧  Review Queue": "Review",
            "📅  Calendar": "Calendar",
            "⚙️  Settings": "Settings"
        }
        
        def nav_change():
            st.session_state.page = menu_map[st.session_state.nav_radio]

        try:
            curr = [k for k, v in menu_map.items() if v == st.session_state.page][0]
        except:
            curr = list(menu_map.keys())[0]
            
        st.radio("Menu", list(menu_map.keys()), index=list(menu_map.keys()).index(curr), key="nav_radio", on_change=nav_change, label_visibility="collapsed")
        
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Đăng xuất", on_click=logout, use_container_width=True): pass
    else:
        st.info("Vui lòng đăng nhập để sử dụng tính năng.")

# =============================================
# AUTH SCREEN
# =============================================
if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("""<div style="text-align:center; padding: 60px 0;">
            <div style="font-size:50px; margin-bottom:10px;">🛡️</div>
            <h1 style="font-size:32px; font-weight:800;">OmniProspect AI</h1>
            <p style="color:#64748b;">Enterprise Prospecting Orchestrator</p>
        </div>""", unsafe_allow_html=True)
        
        mode = st.radio("Mode", ["Đăng nhập", "Đăng ký"], horizontal=True, label_visibility="collapsed")
        user_input = st.text_input("Username", key="l_user")
        pass_input = st.text_input("Password", type="password", key="l_pass")
        
        if mode == "Đăng nhập":
            if st.button("ĐĂNG NHẬP", use_container_width=True, type="primary"):
                try:
                    res = requests.post(f"{BACKEND_URL}/auth/login", json={"username": user_input, "password": pass_input}, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.username = data["username"]
                        st.session_state.authenticated = True
                        cookie_manager.set("omni_token", data["access_token"])
                        cookie_manager.set("omni_user", data["username"])
                        st.success("Đăng nhập thành công! Hệ thống đang tải và thiết lập bộ nhớ đệm...")
                        # Thêm khoảng thời gian chờ để CookieManager (vốn chạy qua JS iframe) kịp ghi cookie xuống trình duyệt
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Sai username hoặc mật khẩu.")
                except Exception as e:
                    st.error(f"⚠️ Không thể kết nối Backend: {e}")
        else:
            if st.button("ĐĂNG KÝ TÀI KHOẢN DEMO", use_container_width=True, type="primary"):
                try:
                    res = requests.post(f"{BACKEND_URL}/auth/register", json={"username": user_input, "password": pass_input}, timeout=5)
                    if res.status_code == 200:
                        st.success("✅ Đăng ký thành công! Hãy chuyển sang 'Đăng nhập' để truy cập.")
                    else:
                        st.error(res.json().get("detail", "Lỗi đăng ký"))
                except:
                    st.error("⚠️ Không thể kết nối Backend.")
    st.stop()

# =============================================
# MAIN PAGES
# =============================================
if st.session_state.page == "Landing":
    st.markdown("""<div style="text-align: center; padding: 60px 20px;">
        <div style="display: inline-block; padding: 8px 16px; background: rgba(13, 33, 161, 0.1); border-radius: 100px; color: #0d21a1; font-size: 12px; font-weight: 800; margin-bottom: 24px; letter-spacing: 2px;">WELCOME TO OMNIPROSPECT AI</div>
        <h1 style="font-size: 50px; font-weight: 800; margin-bottom: 20px;">Tự động hóa toàn bộ phễu <br><span class="text-gradient">Tìm kiếm khách hàng bằng AI</span></h1>
        <p style="font-size: 18px; color: #64748b; max-width: 800px; margin: 0 auto 50px;">OmniProspect vận hành các đặc vụ AI đa nhiệm giúp bạn quét Lead, nghiên cứu cá nhân hóa và tự động sắp xếp lịch họp.</p>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 50px;">
            <div class="card" style="width: 280px; text-align: left;">
                <div style="font-size: 30px; margin-bottom: 15px;">🔍</div>
                <h4 style="margin:0 0 10px 0;">Smart Scouting</h4>
                <p style="font-size:13px; color:#64748b;">Tìm kiếm Lead tiềm năng từ LinkedIn tự động.</p>
            </div>
            <div class="card" style="width: 280px; text-align: left;">
                <div style="font-size: 30px; margin-bottom: 15px;">🧠</div>
                <h4 style="margin:0 0 10px 0;">Deep Research</h4>
                <p style="font-size:13px; color:#64748b;">AI nghiên cứu chuyên sâu về website khách hàng.</p>
            </div>
            <div class="card" style="width: 280px; text-align: left;">
                <div style="font-size: 30px; margin-bottom: 15px;">📩</div>
                <h4 style="margin:0 0 10px 0;">AI Reach Out</h4>
                <p style="font-size:13px; color:#64748b;">Email cá nhân hóa với tỷ lệ phản hồi cực cao.</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    
    _, cb, _ = st.columns([1, 1.5, 1])
    with cb:
        if st.button("🚀 BẮT ĐẦU TRẢI NGHIỆM DASHBOARD", type="primary", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.rerun()

elif st.session_state.page == "Dashboard":
    st.markdown('<h1 style="font-size: 30px; font-weight: 800; margin-bottom: 25px;">Dashboard Tổng Quan</h1>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown('<div class="stat-card"><h5>Tổng Lead</h5><h2 class="text-gradient">1,284</h2></div>', unsafe_allow_html=True)
    c2.markdown('<div class="stat-card"><h5>Đã Nghiên Cứu</h5><h2 style="color:#4ade80;">850</h2></div>', unsafe_allow_html=True)
    c3.markdown('<div class="stat-card"><h5>Lịch Hẹn</h5><h2 style="color:#f59e0b;">18</h2></div>', unsafe_allow_html=True)
    c4.markdown('<div class="stat-card"><h5>API Health</h5><h2 style="color:#10b981;">99.9%</h2></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2, 1])
    with cl:
        st.markdown('<div class="card"><h3>🤖 Trạng thái AI Agents</h3>', unsafe_allow_html=True)
        try:
            monitors = requests.get(f"{BACKEND_URL}/agent-monitor", headers=auth_headers()).json()
            for m in monitors[:3]:
                st.write(f"**{m['agent_name']}**: {m['action_text']}")
                st.progress(m['progress']/100)
        except:
            st.info("Đang đồng bộ trạng thái từ Backend...")
        st.markdown('</div>', unsafe_allow_html=True)
    with cr:
        st.markdown('<div class="card"><h4>🕐 Hoạt động gần đây</h4><p style="font-size:13px;">● Scouter tìm thấy 5 lead mới<br>● Researcher hoàn tất phân tích VNG<br>● Đã gửi email tới VinGroup</p></div>', unsafe_allow_html=True)

elif st.session_state.page == "Campaign":
    st.title("📣 Chiến dịch Prospecting")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    with st.form("scout_f"):
        kw = st.text_input("Nhập từ khóa khách hàng (Ví dụ: CEO Fintech HCM)")
        if st.form_submit_button("Kích hoạt AI Agents"):
            if kw:
                try:
                    res = requests.post(f"{BACKEND_URL}/scout", params={"keyword": kw}, headers=auth_headers(), timeout=10)
                    if res.status_code == 200:
                        st.success("Chiến dịch đã được bắt đầu!")
                        time.sleep(1)
                        st.session_state.page = "Agents"
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {res.json().get('detail', res.text)}")
                except Exception as e:
                    st.error(f"Lỗi kết nối Backend: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "Agents":
    st.title("🤖 AI Agent Orchestration")
    st.markdown('<p style="color:#64748b;">Quản lý và theo dõi trạng thái các đặc vụ AI trong hệ thống.</p>', unsafe_allow_html=True)
    
    agents = [
        {"icon": "🔍", "name": "Scouter Agent", "desc": "LinkedIn Automation", "detail": "Quét và thu thập data khách hàng tiềm năng từ LinkedIn.", "color": "#eef2ff"},
        {"icon": "📊", "name": "Researcher Agent", "desc": "Deep Analysis (Gemini)", "detail": "Phân tích website và báo cáo để tìm nhu cầu khách hàng.", "color": "#f0fdf4"},
        {"icon": "✍️", "name": "Copywriter Agent", "desc": "Creative Personalization", "detail": "Tạo nội dung tiếp cận cá nhân hóa dựa trên kết quả nghiên cứu.", "color": "#fefce8"},
        {"icon": "📅", "name": "Scheduler Agent", "desc": "Meeting Coordinator", "detail": "Tự động phản hồi và chốt lịch họp qua Google Calendar.", "color": "#f1f5f9"},
    ]
    
    try:
        monitors = requests.get(f"{BACKEND_URL}/agent-monitor", headers=auth_headers()).json()
    except:
        monitors = []
    
    for i, a in enumerate(agents):
        m = monitors[i] if i < len(monitors) else {"progress": 0, "action_text": "Sẵn sàng", "task_status": "Idle"}
        st.markdown(f"""<div class="card" style="padding:20px;">
            <div style="display:flex; align-items:center; gap:16px;">
                <div style="width:50px; height:50px; background:{a['color']}; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px;">{a['icon']}</div>
                <div style="flex:1;">
                    <div style="font-weight:700; font-size:16px;">{a['name']}</div>
                    <div style="font-size:12px; color:#64748b;">{a['desc']} — {a['detail']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; color:#0d21a1;">{m['progress']}%</div>
                    <div style="font-size:11px; color:#64748b;">{m['action_text']}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.progress(m['progress'] / 100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚙️ Chạy nhanh Scouter Agent"):
        kw = st.text_input("Từ khóa tìm kiếm", key="agent_kw")
        if st.button("Chạy ngay", type="primary"):
            if kw:
                try:
                    res = requests.post(f"{BACKEND_URL}/scout", params={"keyword": kw}, headers=auth_headers(), timeout=10)
                    if res.status_code == 200:
                        st.success("Đã kích hoạt Scouter!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {res.json().get('detail', res.text)}")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

elif st.session_state.page == "Analytics":
    st.title("📈 Analytics & Insights")
    try:
        data = requests.get(f"{BACKEND_URL}/analytics", headers=auth_headers()).json()
    except:
        data = {"total_leads": 0, "researched_leads": 0, "approved_leads": 0, "total_appointments": 0, "status_distribution": {}}
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng Lead", data["total_leads"])
    c2.metric("Đã Nghiên Cứu", data.get("researched_leads", 0))
    c3.metric("Đã Duyệt", data.get("approved_leads", 0))
    c4.metric("Lịch Hẹn", data["total_appointments"])
    
    st.markdown("---")
    st.subheader("Phân bố trạng thái Lead")
    dist = data.get("status_distribution", {})
    if dist:
        for status, count in dist.items():
            st.write(f"**{status}**: {count}")
    else:
        st.info("Chưa có dữ liệu phân bố.")

elif st.session_state.page == "Leads":
    st.title("👥 Leads Database & AI Actions")
    try:
        leads = requests.get(f"{BACKEND_URL}/leads", headers=auth_headers()).json()
        if leads:
            for lead in leads[:20]:
                with st.expander(f"👤 {lead.get('name', 'N/A')} — {lead.get('company', '')}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**Chức vụ:** {lead.get('title', 'N/A')}")
                        st.write(f"**Trạng thái:** `{lead.get('status', 'N/A')}`")
                        st.write(f"**LinkedIn:** [Link]({lead.get('linkedin_url', '#')})")
                        if lead.get('research_summary'):
                            st.info(f"📊 **Nghiên cứu:** {lead['research_summary'][:200]}...")
                        if lead.get('draft_email'):
                            st.success(f"📧 **Email nháp:**\n\n{lead['draft_email']}")
                    
                    with c2:
                        st.markdown("**Hành động AI:**")
                        if st.button("🧠 Nghiên cứu (Researcher)", key=f"rs_{lead['_id']}", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/leads/{lead['_id']}/action", params={"action": "research"}, headers=auth_headers())
                            st.toast("Đang phân tích dữ liệu website...")
                            time.sleep(1)
                            st.success("Đã hoàn tất nghiên cứu!")
                            st.rerun()
                            
                        if st.button("✍️ Soạn Email (Copywriter)", key=f"cw_{lead['_id']}", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/leads/{lead['_id']}/action", params={"action": "draft"}, headers=auth_headers())
                            st.toast("Copywriter đang viết nội dung cá nhân hóa...")
                            time.sleep(1)
                            st.success("Đã đẩy email vào Review Queue!")
                            st.rerun()
                            
                        if st.button("📅 Xếp lịch (Scheduler)", key=f"sc_{lead['_id']}", use_container_width=True):
                            requests.post(f"{BACKEND_URL}/leads/{lead['_id']}/action", params={"action": "schedule"}, headers=auth_headers())
                            st.toast("Đang đồng bộ với Google Calendar...")
                            time.sleep(1)
                            st.success("Đã tạo Lịch hẹn thành công!")
                            st.rerun()
        else:
            st.info("Chưa có Lead nào. Hãy vào trang Campaign để chạy Scouter Agent!")
    except Exception as e:
        st.error(f"Không thể tải danh sách Lead. Hãy đảm bảo Backend đang chạy: {e}")

elif st.session_state.page == "Review":
    st.title("📧 Review Queue")
    st.markdown("Xem xét và phê duyệt các email do AI soạn thảo trước khi gửi đi.")
    try:
        leads = requests.get(f"{BACKEND_URL}/leads", headers=auth_headers()).json()
        review_leads = [l for l in leads if l.get("status") == "email_drafted"]
        if review_leads:
            for i, lead in enumerate(review_leads[:10]):
                st.markdown(f"### ✉️ Email cho {lead.get('name', 'N/A')}")
                st.text_area("Nội dung email", lead.get("draft_email", ""), key=f"rev_{i}", height=150)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Duyệt", key=f"ap_{i}"):
                        try:
                            # Lấy nội dung từ text_area thay vì từ lead gốc (để user có thể sửa trước khi duyệt)
                            content = st.session_state.get(f"rev_{i}", lead.get("draft_email", ""))
                            res = requests.post(f"{BACKEND_URL}/leads/{lead['_id']}/approve", json={"content": content}, headers=auth_headers())
                            if res.status_code == 200:
                                st.success("Đã duyệt!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Lỗi từ máy chủ.")
                        except Exception as e:
                            st.error(f"Lỗi kết nối: {e}")
                with c2:
                    if st.button("❌ Từ chối", key=f"rj_{i}"):
                        st.warning("Đã bỏ qua email này.")
                st.markdown("---")
        else:
            st.info("Không có email nào cần duyệt.")
    except Exception as e:
        st.error(f"Không thể tải Review Queue: {e}")

elif st.session_state.page == "Calendar":
    st.title("📅 Lịch Hẹn")
    try:
        apps = requests.get(f"{BACKEND_URL}/appointments", headers=auth_headers()).json()
        if apps:
            for a in apps:
                st.markdown(f"""<div class="card">
                    <h4>📞 {a.get('summary', 'Cuộc họp')}</h4>
                    <p>👤 {a.get('lead_name', '')} — {a.get('company', '')}</p>
                    <p>⏰ {a.get('start_time', '')}</p>
                </div>""", unsafe_allow_html=True)
                if a.get("meeting_link"):
                    if st.button(f"🔗 Tham gia", key=f"cal_{a.get('_id', '')}"):
                        st.info(f"Link: {a['meeting_link']}")
        else:
            st.info("Chưa có lịch hẹn nào.")
    except Exception as e:
        st.error(f"Không thể tải lịch hẹn: {e}")

elif st.session_state.page == "Settings":
    st.title("⚙️ Cài đặt hệ thống")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Thông tin tài khoản")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Backend URL:** {BACKEND_URL}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Kiểm tra kết nối")
    if st.button("🔍 Test Backend"):
        try:
            r = requests.get(f"{BACKEND_URL}/analytics", headers=auth_headers(), timeout=5)
            if r.status_code == 200:
                st.success("✅ Backend hoạt động tốt!")
            else:
                st.warning(f"Backend phản hồi mã: {r.status_code}")
        except:
            st.error("❌ Không thể kết nối Backend.")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title(st.session_state.page)
    st.info("Trang này đang được phát triển.")

