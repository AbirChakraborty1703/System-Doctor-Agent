"""Premium Streamlit dashboard for SystemDoctor AI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from agents.orchestrator import OrchestratorAgent
from packages.schemas import DeviceMetadata, OSType, Question, SessionStatus, TroubleshootingSession


THEMES = {
    "Dark": {
        "bg": "#0b1220",
        "bg_alt": "#111a2c",
        "surface": "rgba(16, 24, 40, 0.88)",
        "surface_2": "rgba(20, 29, 48, 0.96)",
        "border": "rgba(148, 163, 184, 0.18)",
        "text": "#eef4ff",
        "muted": "#a8b7d1",
        "primary": "#93c5fd",
        "primary_strong": "#60a5fa",
        "accent": "#34d399",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "danger": "#fb7185",
        "shadow": "0 20px 50px rgba(0, 0, 0, 0.28)",
        "bubble_user": "linear-gradient(135deg, rgba(96, 165, 250, 0.22), rgba(52, 211, 153, 0.18))",
        "bubble_ai": "rgba(12, 18, 32, 0.95)",
    },
    "Light": {
        "bg": "#f5f7fb",
        "bg_alt": "#edf2f8",
        "surface": "rgba(255, 255, 255, 0.94)",
        "surface_2": "rgba(255, 255, 255, 0.98)",
        "border": "rgba(82, 107, 146, 0.16)",
        "text": "#0f172a",
        "muted": "#5b6b84",
        "primary": "#2563eb",
        "primary_strong": "#1d4ed8",
        "accent": "#0f766e",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "shadow": "0 18px 45px rgba(15, 23, 42, 0.10)",
        "bubble_user": "linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(15, 118, 110, 0.10))",
        "bubble_ai": "rgba(255, 255, 255, 0.97)",
    },
}

STATUS_LABELS = {
    SessionStatus.INTAKE: ("Ready", "The assistant is waiting for a new issue description."),
    SessionStatus.QUESTIONING: ("Diagnosing", "Adaptive questions are collecting evidence."),
    SessionStatus.DIAGNOSIS_READY: ("Analyzing", "Evidence is sufficient to rank probable causes."),
    SessionStatus.REMEDIATION_READY: ("Fix Plan Ready", "A safe remediation plan has been prepared."),
    SessionStatus.VERIFYING: ("Verifying", "The workflow is checking whether the fix worked."),
    SessionStatus.RESOLVED: ("Completed", "The issue has been marked resolved."),
    SessionStatus.ESCALATED: ("Escalated", "The case needs human or hardware support."),
}

WORKFLOW_STAGES = [
    (SessionStatus.INTAKE, "Intake"),
    (SessionStatus.QUESTIONING, "Evidence"),
    (SessionStatus.DIAGNOSIS_READY, "Diagnosis"),
    (SessionStatus.REMEDIATION_READY, "Remediation"),
    (SessionStatus.VERIFYING, "Verification"),
    (SessionStatus.RESOLVED, "Resolved"),
]

CATEGORY_OPTIONS = [
    ("Auto-detect", ""),
    ("Hardware", "hardware"),
    ("Software", "software"),
    ("Performance", "performance"),
    ("Update / Driver", "update_driver"),
    ("Boot / BIOS", "bios_boot"),
    ("Storage", "storage"),
    ("Network", "network"),
    ("OS-specific", "os_specific"),
]


@st.cache_resource

def get_orchestrator() -> OrchestratorAgent:
    return OrchestratorAgent()



def _os_from_label(label: str) -> OSType:
    lookup = {
        "Windows": OSType.WINDOWS,
        "macOS": OSType.MACOS,
        "Linux": OSType.LINUX,
        "Unknown": OSType.UNKNOWN,
    }
    return lookup.get(label, OSType.UNKNOWN)



def _ensure_state() -> None:
    defaults = {
        "session_id": None,
        "current_question": None,
        "ui_theme": "Light",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



def _active_step(status: SessionStatus) -> int:
    order = [stage for stage, _ in WORKFLOW_STAGES]
    if status in order:
        return order.index(status)
    return 0



def _status_badge_html(status: SessionStatus) -> str:
    label, _ = STATUS_LABELS.get(status, (status.value.title(), ""))
    return f"<span class='status-pill status-{status.value}'>{label}</span>"



def _risk_badge_html(risk: str) -> str:
    return f"<span class='risk-pill risk-{risk}'>{risk.upper()}</span>"



def _confidence_class(confidence: float) -> str:
    if confidence >= 0.7:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"



def _inject_css(theme_name: str) -> None:
    palette = THEMES.get(theme_name, THEMES["Dark"])
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

            :root {{
                --bg: {palette['bg']};
                --bg-alt: {palette['bg_alt']};
                --surface: {palette['surface']};
                --surface-2: {palette['surface_2']};
                --border: {palette['border']};
                --text: {palette['text']};
                --muted: {palette['muted']};
                --primary: {palette['primary']};
                --primary-strong: {palette['primary_strong']};
                --accent: {palette['accent']};
                --success: {palette['success']};
                --warning: {palette['warning']};
                --danger: {palette['danger']};
                --shadow: {palette['shadow']};
                --bubble-user: {palette['bubble_user']};
                --bubble-ai: {palette['bubble_ai']};
            }}

            html, body, [class*="css"], .stApp {{
                font-family: 'IBM Plex Sans', system-ui, sans-serif;
                color: var(--text);
            }}

            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 28%),
                    radial-gradient(circle at 85% 10%, rgba(15, 118, 110, 0.10), transparent 26%),
                    linear-gradient(180deg, var(--bg-alt), var(--bg));
            }}

            .block-container {{
                padding-top: 1.25rem;
                padding-bottom: 2.5rem;
                max-width: 1500px;
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #f8fbff, #eef4fb);
                border-right: 1px solid rgba(82, 107, 146, 0.10);
            }}

            [data-testid="stSidebar"] * {{
                color: #0f172a;
            }}

            .sidebar-brand {{
                border: 1px solid rgba(82, 107, 146, 0.14);
                border-radius: 18px;
                padding: 1rem 1rem 0.9rem 1rem;
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(241, 245, 249, 0.98));
                box-shadow: var(--shadow);
                margin-bottom: 1rem;
            }}

            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] .stTextInput input,
            [data-testid="stSidebar"] .stTextArea textarea,
            [data-testid="stSidebar"] .stMultiSelect div {{
                background: rgba(255, 255, 255, 0.96) !important;
                color: #0f172a !important;
                border-color: rgba(82, 107, 146, 0.20) !important;
            }}

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] span {{
                color: #22314d;
            }}

            .hero-card, .glass-card, .panel-card, .summary-card {{
                border: 1px solid var(--border);
                background: var(--surface);
                backdrop-filter: blur(12px);
                border-radius: 24px;
                box-shadow: var(--shadow);
            }}

            .hero-card {{
                padding: 1.45rem 1.5rem;
                margin-bottom: 1rem;
                background:
                    linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(15, 118, 110, 0.10)),
                    var(--surface);
            }}

            .hero-title {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 2.05rem;
                line-height: 1.05;
                margin: 0 0 0.35rem 0;
                letter-spacing: -0.04em;
            }}

            .hero-subtitle {{
                color: var(--muted);
                font-size: 0.98rem;
                margin: 0;
            }}

            .status-pill, .risk-pill, .stage-pill {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 0.35rem;
                border-radius: 999px;
                padding: 0.22rem 0.72rem;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                white-space: nowrap;
            }}

            .status-pill {{
                background: rgba(37, 99, 235, 0.10);
                color: var(--primary-strong);
                border: 1px solid rgba(37, 99, 235, 0.18);
            }}

            .stage-trail {{
                display: grid;
                grid-template-columns: repeat(6, minmax(0, 1fr));
                gap: 0.55rem;
                margin: 0.85rem 0 1rem 0;
            }}

            .stage-node {{
                border-radius: 18px;
                border: 1px solid var(--border);
                padding: 0.72rem 0.75rem;
                background: var(--surface);
                min-height: 72px;
            }}

            .stage-node.active {{
                border-color: rgba(37, 99, 235, 0.48);
                box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.14), var(--shadow);
            }}

            .stage-node.complete {{
                border-color: rgba(74, 222, 128, 0.36);
                opacity: 0.96;
            }}

            .stage-node-label {{
                display: block;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }}

            .stage-node-desc {{
                color: var(--muted);
                font-size: 0.76rem;
                line-height: 1.2;
            }}

            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.75rem;
                margin-bottom: 1rem;
            }}

            .metric-card {{
                padding: 0.95rem 1rem;
                border-radius: 18px;
                border: 1px solid var(--border);
                background: var(--surface);
                box-shadow: var(--shadow);
            }}

            .metric-label {{
                display: block;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--muted);
                margin-bottom: 0.2rem;
            }}

            .metric-value {{
                font-size: 1.1rem;
                font-weight: 700;
                color: var(--text);
            }}

            .section-title {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.05rem;
                margin: 0 0 0.85rem 0;
                letter-spacing: -0.02em;
            }}

            .conversation-shell, .insight-shell {{
                border-radius: 24px;
                border: 1px solid var(--border);
                background: var(--surface);
                box-shadow: var(--shadow);
                padding: 1rem 1rem 1.1rem 1rem;
            }}

            .conversation-scroll {{
                max-height: 520px;
                overflow-y: auto;
                padding-right: 0.4rem;
            }}

            .bubble {{
                border-radius: 20px;
                padding: 0.95rem 1rem;
                margin-bottom: 0.75rem;
                max-width: 96%;
                border: 1px solid var(--border);
            }}

            .bubble.ai {{
                background: var(--bubble-ai);
                color: var(--text);
            }}

            .bubble.user {{
                background: var(--bubble-user);
                color: var(--text);
                margin-left: auto;
            }}

            .bubble-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.6rem;
                margin-bottom: 0.35rem;
                font-size: 0.8rem;
                color: var(--muted);
            }}

            .bubble-title {{
                font-weight: 700;
                color: var(--text);
            }}

            .bubble-copy {{
                font-size: 0.95rem;
                line-height: 1.5;
                white-space: pre-wrap;
            }}

            .bubble.ai .bubble-copy a, .bubble.user .bubble-copy a {{
                color: var(--primary);
            }}

            .question-banner {{
                margin-top: 0.6rem;
                padding: 0.95rem 1rem;
                border-radius: 18px;
                border: 1px solid rgba(37, 99, 235, 0.18);
                background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(15, 118, 110, 0.08));
            }}

            .confidence-bar {{
                height: 10px;
                border-radius: 999px;
                background: rgba(148, 163, 184, 0.18);
                overflow: hidden;
                margin: 0.45rem 0 0.35rem 0;
            }}

            .confidence-fill.high {{ background: linear-gradient(90deg, #4ade80, #16a34a); }}
            .confidence-fill.medium {{ background: linear-gradient(90deg, #fbbf24, #d97706); }}
            .confidence-fill.low {{ background: linear-gradient(90deg, #fb7185, #ef4444); }}

            .diag-card {{
                border-radius: 18px;
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.06);
                padding: 0.92rem 0.95rem;
                margin-bottom: 0.8rem;
            }}

            .diag-title {{
                display: flex;
                justify-content: space-between;
                gap: 0.8rem;
                align-items: baseline;
                margin-bottom: 0.3rem;
            }}

            .diag-subtle {{
                color: var(--muted);
                font-size: 0.84rem;
            }}

            .evidence-block {{
                border-radius: 18px;
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.04);
                padding: 0.9rem;
                margin-bottom: 0.75rem;
            }}

            .evidence-list {{
                margin: 0.4rem 0 0 1.05rem;
                color: var(--text);
            }}

            .step-card {{
                border-radius: 18px;
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.05);
                padding: 0.9rem 0.95rem;
                margin-bottom: 0.75rem;
            }}

            .step-head {{
                display: flex;
                justify-content: space-between;
                gap: 0.75rem;
                align-items: center;
                margin-bottom: 0.45rem;
            }}

            .footer-card {{
                margin-top: 1rem;
                padding: 0.95rem 1rem;
                border-radius: 20px;
                border: 1px solid var(--border);
                background: var(--surface);
                box-shadow: var(--shadow);
                display: flex;
                justify-content: space-between;
                gap: 0.85rem;
                align-items: center;
                flex-wrap: wrap;
            }}

            .footer-meta {{
                color: var(--muted);
                font-size: 0.9rem;
            }}

            .thinking-dot {{
                display: inline-flex;
                width: 9px;
                height: 9px;
                border-radius: 999px;
                background: var(--primary);
                box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.38);
                animation: pulse 1.8s infinite;
            }}

            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.38); }}
                70% {{ box-shadow: 0 0 0 12px rgba(56, 189, 248, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }}
            }}

            .block-container .stDownloadButton button {{
                border-radius: 999px;
                border: 1px solid rgba(37, 99, 235, 0.20);
                background: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(15, 118, 110, 0.14));
                color: var(--text);
                font-weight: 700;
            }}

            .block-container .stButton button {{
                border-radius: 999px;
                font-weight: 700;
            }}

            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stRadio [role="radiogroup"],
            .stChatInput textarea {{
                background: var(--surface-2) !important;
                color: var(--text) !important;
                border: 1px solid var(--border) !important;
                border-radius: 14px !important;
            }}

            .stForm {{
                background: transparent;
            }}

            .stButton button {{
                border: 1px solid rgba(37, 99, 235, 0.22) !important;
                background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(15, 118, 110, 0.12)) !important;
                color: var(--text) !important;
            }}

            .stButton button:hover {{
                border-color: rgba(37, 99, 235, 0.36) !important;
            }}

            .stMetric {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 0.25rem 0.35rem;
                box-shadow: var(--shadow);
            }}

            .stTabs [data-baseweb="tab-list"] {{
                gap: 0.35rem;
                background: transparent;
            }}

            .stTabs [data-baseweb="tab"] {{
                border-radius: 999px;
                border: 1px solid var(--border);
                background: var(--surface);
                color: var(--muted);
                padding: 0.5rem 0.85rem;
            }}

            .stTabs [aria-selected="true"] {{
                color: var(--text) !important;
                border-color: rgba(37, 99, 235, 0.28) !important;
                background: rgba(37, 99, 235, 0.12) !important;
            }}

            @media (max-width: 1100px) {{
                .metric-grid, .stage-trail {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            }}

            @media (max-width: 760px) {{
                .metric-grid, .stage-trail {{ grid-template-columns: 1fr; }}
                .hero-title {{ font-size: 1.65rem; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )



def _render_sidebar() -> tuple[DeviceMetadata, str]:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.25rem;font-weight:700;">SystemDoctor AI</div>
            <div style="opacity:0.82;margin-top:0.15rem;">AI-Powered System Diagnosis</div>
            <div style="opacity:0.65;font-size:0.86rem;margin-top:0.35rem;">Enterprise troubleshooting cockpit for hardware, software, and OS incidents.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    theme = st.sidebar.radio(
        "Theme",
        ["Dark", "Light"],
        index=0 if st.session_state.ui_theme == "Dark" else 1,
        horizontal=True,
    )
    st.session_state.ui_theme = theme

    st.sidebar.markdown("### System Context")
    os_label = st.sidebar.selectbox(
        "Operating System",
        ["Unknown", "Windows", "macOS", "Linux"],
        index=0,
    )
    category_label = st.sidebar.selectbox(
        "Issue Category",
        [label for label, _ in CATEGORY_OPTIONS],
        index=0,
    )
    device_type = st.sidebar.selectbox(
        "Device Type",
        ["", "Laptop", "Desktop", "Workstation", "VM", "Server"],
        index=0,
    )

    with st.sidebar.expander("Advanced context", expanded=False):
        device_model = st.text_input("Device Model", placeholder="e.g. Dell XPS 15 9530")
        symptom_duration = st.text_input("Symptom Duration", placeholder="e.g. 2 days, since last update")
        recent_update = st.text_input("Recent Update", placeholder="e.g. KB update, macOS patch")
        recent_driver_change = st.text_input("Recent Driver Change", placeholder="e.g. GPU driver 551.xx")
        error_message = st.text_input("Error Message", placeholder="Any code or exact text")
        boot_status = st.text_input("Boot Status", placeholder="Normal, loop, no display, etc.")
        overheating = st.text_input("Overheating Symptoms", placeholder="Fan loud, thermal shutdown")
        storage = st.text_input("Storage Symptoms", placeholder="Disk full, I/O errors")
        online_search_enabled = st.checkbox(
            "Enable Safe Online Insight Enrichment",
            value=False,
            help="Uses allowlisted trusted domains and only enriches when it adds confidence.",
        )

    if st.sidebar.button("Start New Session", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.current_question = None
        st.rerun()

    os_value = _os_from_label(os_label)
    category_value = next((value for label, value in CATEGORY_OPTIONS if label == category_label), "")

    return (
        DeviceMetadata(
            os=os_value,
            expected_category=category_value or None,
            device_type=device_type or None,
            device_model=device_model or None,
            symptom_duration=symptom_duration or None,
            recent_update=recent_update or None,
            recent_driver_change=recent_driver_change or None,
            error_message=error_message or None,
            boot_status=boot_status or None,
            overheating_symptoms=overheating or None,
            storage_symptoms=storage or None,
            online_search_enabled=online_search_enabled,
        ),
        theme,
    )



def _render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;">
                <div>
                    <h1 class="hero-title">SystemDoctor AI Diagnostic Console</h1>
                    <p class="hero-subtitle">A premium troubleshooting cockpit that turns system symptoms into evidence-backed diagnoses, safe fixes, and verified outcomes.</p>
                </div>
                <div style="text-align:right;">
                    <div class="status-pill">Ready for diagnosis</div>
                    <div style="color:var(--muted);font-size:0.86rem;margin-top:0.35rem;">Adaptive questions • ranked causes • risk-aware repair</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _render_workflow_rail(session: TroubleshootingSession) -> None:
    active_index = _active_step(session.status)
    blocks = []
    for index, (_, label) in enumerate(WORKFLOW_STAGES):
        css_class = "stage-node"
        if index < active_index:
            css_class += " complete"
        elif index == active_index:
            css_class += " active"
        blocks.append(
            f"""
            <div class="{css_class}">
                <span class="stage-node-label">{label}</span>
                <div class="stage-node-desc">{'Completed' if index < active_index else ('Current step' if index == active_index else 'Pending')}</div>
            </div>
            """
        )

    st.markdown(f"<div class='stage-trail'>{''.join(blocks)}</div>", unsafe_allow_html=True)



def _render_metrics(session: TroubleshootingSession) -> None:
    triage = session.triage
    top_conf = session.diagnoses[0].confidence if session.diagnoses else 0.0
    plan_risk = session.remediation.risk_level.value if session.remediation else "low"
    loops = session.loops

    metrics = [
        ("Category", triage.category.value if triage else "unknown"),
        ("Severity", triage.severity.value if triage else "unknown"),
        ("Top Confidence", f"{top_conf:.0%}" if top_conf else "—"),
        ("Verification Loops", str(loops)),
    ]

    st.markdown(
        "<div class='metric-grid'>" +
        "".join(
            f"<div class='metric-card'><span class='metric-label'>{label}</span><div class='metric-value'>{value}</div></div>"
            for label, value in metrics
        ) +
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='summary-card' style='padding:0.9rem 1rem;margin-bottom:1rem;'><strong>Session status:</strong> {_status_badge_html(session.status)} <span style='margin-left:0.5rem;color:var(--muted);'>Risk posture: {_risk_badge_html(plan_risk)}</span></div>",
        unsafe_allow_html=True,
    )



def _bubble(role: str, title: str, content: str, meta: str = "") -> str:
    return f"""
    <div class="bubble {role}">
        <div class="bubble-head">
            <div class="bubble-title">{title}</div>
            <div>{meta}</div>
        </div>
        <div class="bubble-copy">{content}</div>
    </div>
    """



def _render_conversation(session: TroubleshootingSession, current_question: Optional[Question]) -> None:
    st.markdown("<div class='conversation-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Troubleshooting Conversation</div>", unsafe_allow_html=True)
    st.caption("The assistant will keep asking the next best question until the evidence is strong enough to diagnose safely.")

    bubbles = [
        _bubble(
            "user",
            "User issue",
            session.user_issue,
            "Initial symptom description",
        ),
    ]

    if session.triage:
        triage = session.triage
        bubbles.append(
            _bubble(
                "ai",
                "Triage summary",
                (
                    f"Category: <strong>{triage.category.value}</strong><br>"
                    f"Severity: <strong>{triage.severity.value}</strong><br>"
                    f"OS: <strong>{triage.inferred_os.value}</strong><br>"
                    f"Confidence: <strong>{triage.confidence:.0%}</strong><br>"
                    f"{triage.rationale}"
                ),
                "Deterministic first-pass classification",
            )
        )

    for qa in session.qa_history:
        bubbles.append(
            _bubble(
                "ai",
                "Assistant question",
                qa.question,
                qa.created_at.strftime("%H:%M UTC") if qa.created_at else "",
            )
        )
        bubbles.append(
            _bubble(
                "user",
                "User answer",
                qa.answer,
                "Captured evidence",
            )
        )

    if current_question and session.status == SessionStatus.QUESTIONING:
        bubbles.append(
            _bubble(
                "ai",
                "Next best question",
                current_question.text,
                "Processing signal selection",
            )
        )

    st.markdown("<div class='conversation-scroll'>" + "".join(bubbles) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)



def _collect_next_question(orchestrator: OrchestratorAgent, session: TroubleshootingSession) -> tuple[TroubleshootingSession, Optional[Question]]:
    if session.status != SessionStatus.QUESTIONING:
        st.session_state.current_question = None
        return session, None

    cached = st.session_state.current_question
    if cached:
        try:
            return session, Question.model_validate(cached)
        except Exception:
            st.session_state.current_question = None

    with st.spinner("Selecting the next best diagnostic question..."):
        question = orchestrator.next_question(session)

    if question is None:
        with st.spinner("Synthesizing diagnosis and remediation plan..."):
            session = orchestrator.run_diagnosis(session)
            session = orchestrator.build_remediation(session)
        st.session_state.current_question = None
        st.rerun()

    st.session_state.current_question = question.model_dump(mode="json")
    return session, question



def _process_answer(orchestrator: OrchestratorAgent, session: TroubleshootingSession, question: Question, answer: str) -> None:
    with st.spinner("Updating the evidence graph and recalibrating the diagnosis..."):
        orchestrator.submit_answer(session, question, answer)
        session = orchestrator.load_session(session.session_id) or session
        next_question = orchestrator.next_question(session)
        if next_question is None:
            session = orchestrator.run_diagnosis(session)
            session = orchestrator.build_remediation(session)
            st.session_state.current_question = None
        else:
            st.session_state.current_question = next_question.model_dump(mode="json")

    st.rerun()



def _render_answer_input(orchestrator: OrchestratorAgent, session: TroubleshootingSession, current_question: Optional[Question]) -> None:
    if session.status != SessionStatus.QUESTIONING or not current_question:
        return

    answer = st.chat_input(
        f"Answer: {current_question.text}",
        key="diagnostic_chat_input",
    )
    if answer and answer.strip():
        _process_answer(orchestrator, session, current_question, answer.strip())



def _render_diagnosis_cards(session: TroubleshootingSession) -> None:
    if not session.diagnoses:
        st.info("No diagnosis available yet. Continue answering questions to increase evidence quality.")
        return

    for candidate in session.diagnoses[:3]:
        confidence_class = _confidence_class(candidate.confidence)
        st.markdown(
            f"""
            <div class="diag-card">
                <div class="diag-title">
                    <div style="font-weight:700;font-size:1rem;">{candidate.title}</div>
                    <div class="status-pill">{candidate.category.value.replace('_', ' ').title()}</div>
                </div>
                <div class="diag-subtle">Confidence: {candidate.confidence:.0%}</div>
                <div class="confidence-bar"><div class="confidence-fill {confidence_class}" style="width:{max(5, int(candidate.confidence * 100))}%;height:100%;border-radius:999px;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Evidence details", expanded=False):
            if candidate.supporting_evidence:
                st.markdown("**Supporting evidence**")
                for item in candidate.supporting_evidence[:4]:
                    st.markdown(f"- {item}")
            if candidate.conflicting_evidence:
                st.markdown("**Conflicting evidence**")
                for item in candidate.conflicting_evidence[:3]:
                    st.markdown(f"- {item}")

    if session.diagnoses[0].confidence < 0.45:
        st.warning("Top diagnosis confidence is low. Continue evidence collection or verify before using risky remediation.")



def _render_evidence_panel(session: TroubleshootingSession) -> None:
    if session.evidence:
        st.markdown("<div class='evidence-block'><strong>Collected signals</strong><div class='diag-subtle'>Structured evidence gathered during the interview</div></div>", unsafe_allow_html=True)
        for signal, value in session.evidence.items():
            st.markdown(f"- **{signal}**: {value}")
    else:
        st.info("No structured evidence has been captured yet.")

    if session.qa_history:
        with st.expander("Interview history", expanded=False):
            for item in session.qa_history:
                st.markdown(f"**Q:** {item.question}")
                st.markdown(f"**A:** {item.answer}")

    if session.diagnoses:
        top = session.diagnoses[0]
        if top.conflicting_evidence:
            st.markdown("<div class='evidence-block'><strong>Primary conflicts</strong></div>", unsafe_allow_html=True)
            for item in top.conflicting_evidence:
                st.markdown(f"- {item}")



def _render_remediation_panel(session: TroubleshootingSession) -> None:
    if not session.remediation:
        st.info("Remediation will appear after diagnosis is strong enough.")
        return

    st.markdown(
        f"<div class='evidence-block'><strong>Plan risk:</strong> {_risk_badge_html(session.remediation.risk_level.value)}</div>",
        unsafe_allow_html=True,
    )

    if session.remediation.warnings:
        for warning in session.remediation.warnings[:6]:
            st.warning(warning)

    for step in session.remediation.steps:
        with st.container(border=False):
            st.markdown(
                f"""
                <div class="step-card">
                    <div class="step-head">
                        <div><strong>Step {step.step_no}</strong> - {step.action}</div>
                        <div>{_risk_badge_html(step.risk_level.value)}</div>
                    </div>
                    <div class="diag-subtle">{'Confirmation required' if step.requires_confirmation else 'Safe to review'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if step.command:
                st.code(step.command, language="bash")
            if step.checkpoint:
                st.caption(f"Checkpoint: {step.checkpoint}")
            if step.rollback:
                st.caption(f"Rollback: {step.rollback}")
            if step.blocked and step.block_reason:
                st.error(step.block_reason)

    if session.remediation.escalation_advice:
        st.error(session.remediation.escalation_advice)



def _render_verification_panel(orchestrator: OrchestratorAgent, session: TroubleshootingSession) -> None:
    if not session.remediation or session.status != SessionStatus.VERIFYING:
        return

    st.markdown("<div class='evidence-block'><strong>Verification</strong><div class='diag-subtle'>Confirm whether the remediation changed behavior.</div></div>", unsafe_allow_html=True)
    cols = st.columns(3)
    if cols[0].button("Yes, fixed", use_container_width=True):
        result = orchestrator.verify(session, "yes fixed")
        if result.next_action == "close_session":
            st.success("Issue marked as resolved.")
        st.session_state.current_question = None
        st.rerun()
    if cols[1].button("Partially improved", use_container_width=True):
        result = orchestrator.verify(session, "partially improved still present")
        if result.next_action == "refine_and_retry":
            st.info("Collecting more evidence for a second pass.")
        st.session_state.current_question = None
        st.rerun()
    if cols[2].button("No, still unresolved", use_container_width=True):
        result = orchestrator.verify(session, "no still unresolved")
        if result.next_action == "escalate":
            st.error("The case has been escalated.")
        st.session_state.current_question = None
        st.rerun()



def _render_report_panel(orchestrator: OrchestratorAgent, session: TroubleshootingSession) -> None:
    report_md = orchestrator.export_report_markdown(session)
    st.download_button(
        label="Export Session Report",
        data=report_md,
        file_name=f"systemdoctor_report_{session.session_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.caption(f"Session ID: {session.session_id}")
    st.caption(f"Last updated: {session.updated_at.isoformat()}")



def _render_intake(orchestrator: OrchestratorAgent, metadata: DeviceMetadata) -> None:
    st.markdown(
        """
        <div class="glass-card" style="padding:1rem 1.05rem;">
            <div class="section-title">Start a diagnostic session</div>
            <div class="diag-subtle" style="margin-bottom:0.8rem;">Describe the system problem in natural language. The assistant will triage, ask follow-up questions, and produce a safe recovery path.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("intake_form", border=False):
        issue = st.text_area(
            "System issue",
            placeholder="Example: My Windows laptop restarts randomly after yesterday's update and sometimes shows a black screen.",
            height=150,
        )
        submitted = st.form_submit_button("Start Troubleshooting", use_container_width=True)

    if submitted and issue.strip():
        session = orchestrator.start_session(issue.strip(), metadata)
        st.session_state.session_id = session.session_id
        st.session_state.current_question = None
        st.rerun()



def _render_footer(session: TroubleshootingSession) -> None:
    summary = []
    if session.triage:
        summary.append(f"{session.triage.category.value} / {session.triage.severity.value}")
    summary.append(session.status.value.replace("_", " ").title())
    if session.remediation:
        summary.append(f"Risk {session.remediation.risk_level.value}")

    st.markdown(
        f"""
        <div class="footer-card">
            <div>
                <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;">SystemDoctor AI</div>
                <div class="footer-meta">{' • '.join(summary) if summary else 'Ready'}</div>
            </div>
            <div class="footer-meta">Production-style diagnostic dashboard for enterprise troubleshooting workflows.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _ensure_question_state(orchestrator: OrchestratorAgent, session: TroubleshootingSession) -> tuple[TroubleshootingSession, Optional[Question]]:
    session, question = _collect_next_question(orchestrator, session)
    if session.status != SessionStatus.QUESTIONING:
        return session, None
    return session, question



def main() -> None:
    st.set_page_config(
        page_title="SystemDoctor AI",
        page_icon="🛠️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _ensure_state()
    metadata, theme = _render_sidebar()
    _inject_css(theme)

    orchestrator = get_orchestrator()
    _render_hero()

    session_id = st.session_state.session_id
    if not session_id:
        _render_intake(orchestrator, metadata)
        return

    session = orchestrator.load_session(session_id)
    if not session:
        st.warning("Session not found. Start a new diagnostic session.")
        st.session_state.session_id = None
        st.session_state.current_question = None
        st.rerun()
        return

    session, current_question = _ensure_question_state(orchestrator, session)
    if session.status != SessionStatus.QUESTIONING:
        st.session_state.current_question = None

    _render_workflow_rail(session)
    _render_metrics(session)

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        _render_conversation(session, current_question)
        _render_answer_input(orchestrator, session, current_question)
    with right:
        tabs = st.tabs(["Diagnosis", "Evidence", "Fixes", "Verify", "Report"])
        with tabs[0]:
            _render_diagnosis_cards(session)
        with tabs[1]:
            _render_evidence_panel(session)
        with tabs[2]:
            _render_remediation_panel(session)
        with tabs[3]:
            _render_verification_panel(orchestrator, session)
        with tabs[4]:
            _render_report_panel(orchestrator, session)

    _render_footer(session)


if __name__ == "__main__":
    main()
