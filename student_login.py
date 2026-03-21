import streamlit as st
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
import base64


# ============================================================
# ✅ PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Student Feedback Portal",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ✅ GLOBAL CSS (HIDE STREAMLIT UI + PREMIUM UI)
# ============================================================
st.markdown("""
<style>
/* Hide Streamlit default header + menu + footer */
header {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Reduce top empty space after header hidden */
.block-container {
    padding-top: 1rem !important;
}

/* Smooth background */
body {
    background-color: #f6f4fb;
}

/* Card UI */
.css-card {
    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 16px;
    padding: 18px 18px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
}

/* Instructions box */
.instruction-box {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px;
    padding: 14px;
    margin-top: 10px;
}

/* Sidebar background */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #2a0b5e 0%, #4a167f 100%);
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Submit Button (GREEN) */
div.stButton > button, div.stFormSubmitButton > button {
    background: linear-gradient(90deg, #16a34a 0%, #22c55e 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.3rem !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 20px rgba(34,197,94,0.25) !important;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    opacity: 0.95 !important;
    transform: translateY(-1px);
}

/* Login Button */
.login-btn button {
    background: linear-gradient(90deg, #6d28d9 0%, #7c3aed 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.65rem 1.3rem !important;
    font-weight: 700 !important;
    box-shadow: 0 10px 25px rgba(124,58,237,0.25) !important;
}
.login-btn button:hover {
    opacity: 0.95 !important;
    transform: translateY(-1px);
}

/* Mobile fixes */
@media (max-width: 768px){
    .css-card { padding: 14px 14px !important; }
}
.section-card {
    background: linear-gradient(90deg, rgba(109,40,217,0.12), rgba(124,58,237,0.06));
    border: 1px solid rgba(109,40,217,0.18);
    border-radius: 16px;
    padding: 14px 16px;
    margin: 10px 0 14px 0;
}
.section-title {
    font-size: 18px;
    font-weight: 800;
    color: #2a0b5e;
    margin: 0;
}
.section-subtitle {
    font-size: 13px;
    color: rgba(0,0,0,0.55);
    margin-top: 4px;
    margin-bottom: 0;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# ✅ SESSION STATE INIT
# ============================================================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "student_details" not in st.session_state:
    st.session_state.student_details = None

# Login loader flags
if "show_loader" not in st.session_state:
    st.session_state.show_loader = False

if "login_payload" not in st.session_state:
    st.session_state.login_payload = None

# Submit loader flags
if "submit_loader" not in st.session_state:
    st.session_state.submit_loader = False

if "submit_payload" not in st.session_state:
    st.session_state.submit_payload = None

if "show_exit_confirm" not in st.session_state:
    st.session_state.show_exit_confirm = False

if "missing_popup" not in st.session_state:
    st.session_state.missing_popup = False

if "missing_list" not in st.session_state:
    st.session_state.missing_list = []

if "exit_popup" not in st.session_state:
    st.session_state.exit_popup = False


# ============================================================
# ✅ HELPERS: Image -> Base64
# ============================================================
def img_to_base64(path: str):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()
#============================================================
def has_unsaved_answers():
    for q in questions_db:
        if st.session_state.get(f"q_{q['id']}") is not None:
            return True
    return False
#=============================================================
# ============================================================
# ✅ FULLSCREEN LOADER
# ============================================================
def show_custom_loading(message="Please wait..."):
    st.markdown(f"""
    <style>
    .fullscreen-loader {{
        position: fixed;
        top: 0; left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(255, 255, 255, 0.92);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 99999;
        flex-direction: column;
        backdrop-filter: blur(4px);
    }}
    .loader-ring {{
        width: 92px;
        height: 92px;
        border-radius: 50%;
        border: 6px solid rgba(124,58,237,0.15);
        border-top: 6px solid rgba(124,58,237,0.95);
        animation: spin 0.9s linear infinite;
        display:flex;
        align-items:center;
        justify-content:center;
        box-shadow: 0 14px 40px rgba(0,0,0,0.08);
        background:white;
    }}
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    .loader-text {{
        margin-top: 18px;
        font-size: 18px;
        font-weight: 650;
        color: #6b7280;
        text-align:center;
    }}
    </style>

    <div class="fullscreen-loader">
        <div class="loader-ring">
            <div style="font-size:32px;">🎓</div>
        </div>
        <div class="loader-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# ✅ QUESTIONS DB
# ============================================================
questions_db = [
    {"id": 1, "q": "How much of the syllabus was covered in the class?",
     "options": ["85 to 100%", "65 to 84%", "55 to 64%", "30 to 54%", "Below 30%"]},

    {"id": 2, "q": "How well did the teachers prepare for the classes?",
     "options": ["Thoroughly", "Satisfactorily", "Poorly", "Indifferently", "Won’t teach at all"]},

    {"id": 3, "q": "How well were the teachers able to communicate?",
     "options": ["Always effective", "Sometimes effective", "Just satisfactorily", "Generally ineffective", "Very poor communication"]},

    {"id": 4, "q": "The teacher’s approach to teaching can best be described as:",
     "options": ["Excellent", "Very good", "Good", "Fair", "Poor"]},

    {"id": 5, "q": "Fairness of the internal evaluation process by the teachers:",
     "options": ["Always fair", "Usually fair", "Sometimes unfair", "Usually unfair", "Unfair"]},

    {"id": 6, "q": "Was your performance in assignments discussed with you?",
     "options": ["Every time", "Usually", "Occasionally", "Rarely", "Never"]},

    {"id": 7, "q": "The institute takes active interest in promoting internship, student exchange, field visit opportunities for students:",
     "options": ["Regularly", "Often", "Sometimes", "Rarely", "Never"]},

    {"id": 8, "q": "The teaching and mentoring process in your institution facilitates you in cognitive, social and emotional growth:",
     "options": ["Significantly", "Very well", "Moderately", "Marginally", "Not at all"]},

    {"id": 9, "q": "The institution provides multiple opportunities to learn and grow:",
     "options": ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"]},

    {"id": 10, "q": "Teachers inform you about your expected competencies, course outcomes and program outcomes:",
     "options": ["Every time", "Usually", "Occasionally", "Rarely", "Never"]},

    {"id": 11, "q": "Your mentor does a necessary follow-up with an assigned task to you:",
     "options": ["Every time", "Usually", "Occasionally", "Rarely", "Never"]},

    {"id": 12, "q": "The teachers identify your strengths and encourage you with providing opportunities:",
     "options": ["Every time", "Usually", "Occasionally", "Rarely", "Never"]},

    {"id": 13, "q": "Teachers are able to identify your weaknesses and help you to overcome them:",
     "options": ["Every time", "Usually", "Occasionally", "Rarely", "Never"]},

    {"id": 14, "q": "The institution makes effort to engage students in the monitoring, review and continuous quality improvement of the teaching learning process:",
     "options": ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"]},

    {"id": 15, "q": "The institution/teachers use student centric methods, such as experiential learning, participative learning and problem-solving methodologies for enhancing learning experiences:",
     "options": ["To a great extent", "Moderate extent", "Some extent", "Very little", "Not at all"]},

    {"id": 16, "q": "Teachers encourage you to participate in extracurricular activities:",
     "options": ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"]},

    {"id": 17, "q": "Efforts are made by the institute/teachers to inculcate soft skills, life skills and employability skills to make you ready for the world of work:",
     "options": ["To a great extent", "Moderate extent", "Some extent", "Very little", "Not at all"]},

    {"id": 18, "q": "What percentage of teachers use ICT tools such as LCD projector, multimedia, etc. while teaching?",
     "options": ["Above 90%", "70-89%", "50-69%", "30-49%", "Below 29%"]},

    {"id": 19, "q": "The overall quality of teaching-learning process in your institute is very good:",
     "options": ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"]},

    {"id": 20, "q": "Overall rating of the institution:",
     "options": ["Excellent", "Very good", "Good", "Fair", "Poor"]},
]


# ============================================================
# ✅ GOOGLE SHEETS (EDIT THESE NAMES ONLY!)
# ============================================================
SPREADSHEET_NAME = "Student_Feedback_2025"   # ✅ Change if needed
SHEET_NAME = "Sheet1"                    # ✅ Change if needed


def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    return gspread.authorize(creds)


def get_feedback_sheet():
    client = get_gspread_client()
    sh = client.open(SPREADSHEET_NAME)

    try:
        ws = sh.worksheet(SHEET_NAME)
    except Exception:
        ws = sh.add_worksheet(title=SHEET_NAME, rows="2000", cols="60")

    # Ensure headers exist
    if not ws.row_values(1):
        headers = ["Timestamp", "Name", "RegNo", "AdmNo", "Class", "Semester", "Email","Suggestion"] + [f"Q{i}" for i in range(1, 21)]
        ws.append_row(headers)

    return ws


def get_existing_submissions():
    ws = get_feedback_sheet()
    return ws.get_all_records()


def save_to_google_sheets(student_data, answers_dict, suggestion):
    ws = get_feedback_sheet()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row_data = [
        timestamp,
        student_data["Name"],
        student_data["RegNo"],
        student_data["AdmNo"],
        student_data["Class"],
        student_data["Semester"],
        student_data["Email"],
        suggestion
    ]

    for i in range(1, 21):
        row_data.append(answers_dict.get(f"Q{i}", ""))

    ws.append_row(row_data)


# ============================================================
# ✅ HEADER (LOCAL IMAGES FIXED ✅)
# ============================================================
def render_header():
    try:
        # ✅ logos (base64)
        aicte_b64 = img_to_base64("logo_aicte.png")
        college_b64 = img_to_base64("logo_college.png")
        uoc_b64 = img_to_base64("logo_uoc.png")
        naac_b64 = img_to_base64("logo_naac.png")

        # ✅ Logo row (HTML only for images)
        st.markdown(f"""
        <div style="display:flex; justify-content:center; align-items:center; gap:22px; flex-wrap:wrap; margin-top:5px;">
            <img src="data:image/png;base64,{college_b64}" style="width:60px; height:60px; object-fit:contain;" />
            <img src="data:image/png;base64,{naac_b64}" style="width:60px; height:60px; object-fit:contain;" />
            <img src="data:image/png;base64,{aicte_b64}" style="width:60px; height:60px; object-fit:contain;" />
            <img src="data:image/png;base64,{uoc_b64}" style="width:60px; height:60px; object-fit:contain;" />
        </div>
        """, unsafe_allow_html=True)

    except Exception:
        # if images missing, ignore silently
        pass

    # ✅ Text part using Streamlit (100% stable)
    st.markdown("""
    <h1 style="text-align:center; margin-top:10px; margin-bottom:0px;">
    ASSABAH ARTS AND SCIENCE COLLEGE, VALAYAMKULAM
    </h1>

    <h3 style="text-align:center; font-weight:500; color:#555; margin-top:6px;">
    Internal Quality Assurance Cell (IQAC)
    </h3>

    <hr style="margin-top:18px; opacity:0.25;">
    """, unsafe_allow_html=True)


# ============================================================
# ✅ LOGIN PAGE
# ============================================================
def show_login_page():
    render_header()

    st.markdown("""
    <div class="css-card" style="max-width: 780px; margin: auto;">
        <h2 style="text-align:center;">🎓 Student Login</h2>
        <p style="text-align:center; opacity:0.8; margin-top:-8px;">
            Data Collection for Student Feedback for Academic Year 2025-26
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        name = st.text_input("Student Name")
        reg_no = st.text_input("Register Number")
        adm_no = st.text_input("Admission Number")

    with col2:
        email = st.text_input("Email ID")
        dept = st.selectbox("Class / Programme", [
        "Select Programme",

        # --- UG PROGRAMMES ---
        "B.A English Language & Literature",
        "BBA",
        "B.Com Finance",
        "B.Com Computer Application",
        "B.Com Travel & Tourism",
        "B.Com Co-Operation",
        "B.Com Banking & Insurance",
        "B.Sc Physics",
        "B.Sc Psychology",
        "B.Sc Chemistry",
        "B.Sc Food Technology",
        "B.Sc Geology",
        "BCA",
        "B.Sc Computer Science",
        "B.Sc Mathematics",
        "B.A Economics"

        # --- PG PROGRAMMES ---
        "M.Com Finance",
        "M.A English",
        "M.Sc Physics",
        "M.Sc Chemistry",
        "M.Sc Food Science & Technology"

        # --- (Optional - if applicable in your college) ---
        # "BCA",
        # "B.Sc Mathematics",
        # "B.Sc Chemistry"
        ])
        sem = st.selectbox("Semester", ["Select Semester", "First", "Second", "Third", "Fourth", "Fifth", "Sixth"])

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="login-btn">', unsafe_allow_html=True)
    login_clicked = st.button("Login to Survey", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if login_clicked:
        if not name or not reg_no or not adm_no or not email or dept == "Select Class" or sem == "Select Semester":
            st.error("⚠️ Please fill in ALL fields to proceed.")
            return

        # ✅ 2-step loader method (FASTEST in Streamlit)
        st.session_state.login_payload = {
            "Name": name.strip(),
            "RegNo": reg_no.strip(),
            "AdmNo": adm_no.strip(),
            "Email": email.strip(),
            "Class": dept,
            "Semester": sem
        }
        st.session_state.show_loader = True
        st.rerun()


# ============================================================
# ✅ PROCESS LOGIN (FULLSCREEN LOADER + GOOGLE SHEET CHECK)
# ============================================================
def process_login_if_needed():
    if st.session_state.get("show_loader") and st.session_state.get("login_payload"):
        show_custom_loading("Verifying Credentials...")

        student = st.session_state.login_payload

        submissions = get_existing_submissions()

        already = False
        for row in submissions:
            if str(row.get("RegNo", "")).strip().lower() == str(student["RegNo"]).strip().lower() and \
               str(row.get("AdmNo", "")).strip().lower() == str(student["AdmNo"]).strip().lower():
                already = True
                break

        if already:
            st.session_state.show_loader = False
            st.session_state.login_payload = None
            st.session_state.page = "login"

            @st.dialog("✅ Feedback Already Submitted")
            def dup_dialog():
                st.info("Our records show that you have already submitted the feedback.")
                st.success("Thank you for your valuable response.")
                if st.button("🔙 Back to Login", use_container_width=True):
                    st.rerun()

            dup_dialog()
            st.stop()

        # Success
        st.session_state.student_details = student
        st.session_state.page = "questions"
        st.session_state.show_loader = False
        st.session_state.login_payload = None
        st.rerun()

@st.dialog("⚠️ Please Answer All Questions")
def show_missing_questions_dialog():
    st.error("Some questions are not answered. Please complete them before submitting.")
    st.write("**Missing:**")
    st.write(", ".join(st.session_state.missing_list))

    if st.button("✅ OK, I'll Complete", use_container_width=True):
        st.session_state.missing_popup = False
        st.session_state.missing_list = []
        st.rerun()

@st.dialog("⚠️ Unsaved Feedback")
def show_exit_warning_dialog():
    st.warning("You have answered some questions but not submitted. If you exit now, your responses will be lost.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Continue Filling", use_container_width=True):
            st.session_state.exit_popup = False
            st.rerun()

    with c2:
        if st.button("🚪 Exit Anyway", use_container_width=True):
            # clear answers
            for q in questions_db:
                k = f"q_{q['id']}"
                if k in st.session_state:
                    del st.session_state[k]

            st.session_state.exit_popup = False
            st.session_state.student_details = None
            st.session_state.page = "login"
            st.rerun()

def section_heading(title, subtitle=""):
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">{title}</div>
        <div class="section-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# ✅ QUESTIONS PAGE
# ============================================================
def show_questions_page():
    student = st.session_state.get("student_details", {})

    # Sidebar profile
    with st.sidebar:
        st.title("👤 Profile")
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.07); padding:12px; border-radius:14px; border:1px solid rgba(255,255,255,0.12);'>
            <b>{student.get("Name","")}</b><br>
            <span style='font-size:12px; opacity:0.85;'>Reg: {student.get("RegNo","")}</span><br>
            <span style='font-size:12px; opacity:0.85;'>Adm: {student.get("AdmNo","")}</span><br>
            <span style='font-size:12px; opacity:0.85;'>{student.get("Class","")} • {student.get("Semester","")}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
        <div class="instruction-box">
            1. Select the most appropriate option.<br>
            2. All questions are mandatory.<br>
            3. Your identity is confidential.<br>
            4. Click <b>Submit</b> when done.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            unsaved = False
            for q in questions_db:
                if st.session_state.get(f"q_{q['id']}") is not None:
                    unsaved = True
                    break

            if unsaved:
                st.session_state.exit_popup = True
                show_exit_warning_dialog()
                st.stop()
            else:
                st.session_state.student_details = None
                st.session_state.page = "login"
                st.rerun()

    if st.session_state.show_exit_confirm:
        with st.modal("⚠️ Unsaved Feedback"):
            st.warning("You have answered some questions but not submitted the feedback. If you exit now, your responses will be lost.")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Continue Filling", use_container_width=True):
                    st.session_state.show_exit_confirm = False
                    st.rerun()

            with c2:
                if st.button("🚪 Exit Anyway", use_container_width=True):
                    # clear answers
                    for q in questions_db:
                        k = f"q_{q['id']}"
                        if k in st.session_state:
                            del st.session_state[k]

                    st.session_state.show_exit_confirm = False
                    st.session_state.student_details = None
                    st.session_state.page = "login"
                    st.rerun()

    # Main
    render_header()
    st.markdown("##  Students Feedback (2024-25)")

    # ✅ Using FORM (smooth for mobile - no flicker on each click)
    sections = [
    ("Teaching & Learning", "Coverage, preparation, communication & evaluation (Q1–Q6)", [1,2,3,4,5,6]),
    ("Mentoring & Support", "Internships, mentoring and student growth (Q7–Q13)", [7,8,9,10,11,12,13]),
    ("Skills & Engagement", "Participation, skills and student-centric learning (Q14–Q17)", [14,15,16,17]),
    ("ICT & Overall Satisfaction", "ICT usage and overall satisfaction (Q18–Q20)", [18,19,20]),
    ]

    q_lookup = {q["id"]: q for q in questions_db}

    with st.form("feedback_form"):
        st.info("👉 Please click each section below to answer the questions. All questions are mandatory.")
        for title, subtitle, ids in sections:
            with st.expander(f"{title}  •  {subtitle}", expanded=False):
                for qid in ids:
                    q = q_lookup[qid]

                    st.markdown(f"""
                    <div class="css-card">
                        <div style="font-size:16px; font-weight:650; color:#1F2937; margin-bottom:10px;">
                            {q['id']}. {q['q']}
                        </div>
                    """, unsafe_allow_html=True)

                    st.radio(
                        f"Select response for Q{q['id']}",
                        q["options"],
                        key=f"q_{q['id']}",
                        index=None,
                        label_visibility="collapsed"
                    )

                    st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="css-card">
            <div style="font-size:16px; font-weight:650; color:#1F2937; margin-bottom:10px;">
                💡 Any other suggestions / comments (optional)
            </div>
        </div>
        """, unsafe_allow_html=True)

        suggestion = st.text_area(
            "Write your suggestion here...",
            key="suggestion_box",
            height=120,
            placeholder="Your feedback helps us improve..."
        )
        st.caption("✅ After completing all sections, click Submit Feedback.")
        submit = st.form_submit_button("✅ Submit Feedback")

    if st.session_state.missing_popup:
        with st.modal("⚠️ Please Answer All Questions"):
            st.error("Some questions are not answered. Please complete them before submitting.")
            st.write("**Missing Questions:**")
            st.write(", ".join(st.session_state.missing_list))

            if st.button("✅ OK, I'll Complete", use_container_width=True):
                st.session_state.missing_popup = False
                st.session_state.missing_list = []
                st.rerun()

    if submit:
        missing_questions = []
        answers = {}

        for q in questions_db:
            val = st.session_state.get(f"q_{q['id']}")
            if val is None:
                missing_questions.append(f"Q{q['id']}")
            else:
                answers[f"Q{q['id']}"] = val

        if missing_questions:
            st.session_state.missing_popup = True
            st.session_state.missing_list = missing_questions
            show_missing_questions_dialog()
            st.stop()

        # ✅ 2-step submission loader
        st.session_state.submit_payload = {
        "student": student,
        "answers": answers,
        "suggestion": st.session_state.get("suggestion_box", "")
        }
        st.session_state.submit_loader = True
        st.rerun()


# ============================================================
# ✅ PROCESS SUBMISSION (FULLSCREEN LOADER + SAVE)
# ============================================================
def process_submit_if_needed():
    if st.session_state.get("submit_loader") and st.session_state.get("submit_payload"):
        show_custom_loading("Submitting feedback... Please wait...")

        payload = st.session_state.submit_payload
        student = payload["student"]
        answers = payload["answers"]

        save_to_google_sheets(student, answers, payload["suggestion"])

        st.session_state.submit_loader = False
        st.session_state.submit_payload = None
        st.session_state.page = "success"
        st.rerun()


# ============================================================
# ✅ SUCCESS PAGE
# ============================================================
def show_success_page():
    render_header()

    st.markdown("""
    <div class="css-card" style="max-width:800px; margin:auto; text-align:center;">
        <h2>✅ Feedback Submitted Successfully</h2>
        <p style="opacity:0.8; font-size:16px;">
            Thank you for your valuable feedback.
        </p>
        <p style="opacity:0.7;">
            Your responses have been recorded.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔙 Back to Login", use_container_width=True):
        for q in questions_db:
            k = f"q_{q['id']}"
            if k in st.session_state:
                del st.session_state[k]

        st.session_state.student_details = None
        st.session_state.page = "login"
        st.rerun()


# ============================================================
# ✅ MAIN ROUTER
# ============================================================
process_login_if_needed()
process_submit_if_needed()

if st.session_state.page == "login":
    show_login_page()
elif st.session_state.page == "questions":
    show_questions_page()
elif st.session_state.page == "success":
    show_success_page()
else:
    st.session_state.page = "login"
    st.rerun()
