"""
CCBM Dashboard — визуализация метрик и аудита.

Streamlit приложение для мониторинга:
- Статистика сжатия контекста
- Security Audit результаты
- Quality Gates метрики
- Glass Box Audit trail
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

# Настройка страницы
st.set_page_config(
    page_title="CCBM Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Заголовок
st.title("🔐 CCBM Dashboard")
st.markdown("**Certified Context Budget Manager** — мониторинг и аудит")

# Боковая панель
st.sidebar.header("Навигация")
page = st.sidebar.radio(
    "Страницы:",
    ["📊 Overview", "🔒 Security Audit", "⚡ Quality Gates", "📝 Audit Trail", "⚙️ Settings"],
)

# Данные (в реальности будут загружаться из API/файлов)
@st.cache_data
def load_metrics():
    """Загрузка метрик проекта."""
    return {
        "version": "0.7.0",
        "tests_passed": 222,
        "tests_total": 222,
        "components": 11,
        "skills": 6,
        "loc": 6000,
        "coverage": 100,
        "security_score": 6.0,
    }


@st.cache_data
def load_security_report():
    """Загрузка security отчёта."""
    report_path = Path("docs/SECURITY_AUDIT_REPORT.md")
    if report_path.exists():
        return report_path.read_text(encoding="utf-8")
    return "Security report not found."


@st.cache_data
def load_quality_gates():
    """Загрузка Quality Gates метрик."""
    return {
        "correctness": 1.0,
        "validation": 1.0,
        "coverage": 0.87,
        "monitoring": 0.8,
        "documentation": 0.9,
        "readiness_score": 0.934,
    }


# Страница Overview
if page == "📊 Overview":
    st.header("📊 Project Overview")
    
    # Метрики
    metrics = load_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tests Passed", f"{metrics['tests_passed']}/{metrics['tests_total']}", "100%")
    
    with col2:
        st.metric("Components", metrics['components'], "+1 this week")
    
    with col3:
        st.metric("Code Coverage", f"{metrics['coverage']}%", "✅")
    
    with col4:
        st.metric("Security Score", f"{metrics['security_score']}/10", "⚠️")
    
    # Графики
    st.subheader("📈 Project Evolution")
    
    evolution_data = {
        "Phase 1": 93,
        "Phase 2": 125,
        "Phase 3": 145,
        "Phase 4": 160,
        "Phase 5": 180,
        "Phase 6": 197,
        "Phase 7": 222,
    }
    
    st.line_chart(list(evolution_data.values()))
    st.caption("Рост количества тестов по фазам")
    
    # Компоненты
    st.subheader("🧩 Components")
    
    components = {
        "Criticality Analyzer": "✅",
        "Optimization Engine": "✅",
        "Chernoff Verifier": "✅",
        "Numeric Invariant Verifier": "✅",
        "Audit Engine": "✅",
        "MCP Server": "✅",
        "LLMLingua Integration": "✅",
        "Quality Gates": "✅",
        "Glass Box Audit": "✅",
        "Security Audit": "✅",
        "KazRoBERTa NER": "✅",
    }
    
    for comp, status in components.items():
        st.write(f"{status} {comp}")

# Страница Security Audit
elif page == "🔒 Security Audit":
    st.header("🔒 Security Audit")
    
    # Score
    security_score = 6.0
    st.metric("Security Score", f"{security_score}/10")
    
    # Progress bar
    st.progress(security_score / 10.0)
    
    # Findings
    st.subheader("📋 Findings Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.error("🔴 CRITICAL: 0")
    
    with col2:
        st.warning("🟠 HIGH: 0")
    
    with col3:
        st.info("🟡 MEDIUM: 4")
    
    with col4:
        st.success("🟢 LOW: 0")
    
    # Report
    st.subheader("📄 Full Report")
    report = load_security_report()
    st.markdown(report)

# Страница Quality Gates
elif page == "⚡ Quality Gates":
    st.header("⚡ Quality Gates")
    
    gates = load_quality_gates()
    
    # Readiness Score
    st.metric("Readiness Score", f"{gates['readiness_score']:.1%}")
    
    # Components
    st.subheader("📊 Component Scores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Correctness (30%)", f"{gates['correctness']:.0%}")
        st.metric("Validation (25%)", f"{gates['validation']:.0%}")
    
    with col2:
        st.metric("Coverage (20%)", f"{gates['coverage']:.0%}")
        st.metric("Monitoring (15%)", f"{gates['monitoring']:.0%}")
    
    # Chart
    st.subheader("📊 Score Breakdown")
    
    score_data = {
        "Correctness": gates['correctness'] * 100,
        "Validation": gates['validation'] * 100,
        "Coverage": gates['coverage'] * 100,
        "Monitoring": gates['monitoring'] * 100,
        "Documentation": gates['documentation'] * 100,
    }
    
    st.bar_chart(score_data)
    
    # Verdict
    if gates['readiness_score'] >= 0.95:
        st.success("✅ MERGE APPROVED")
    elif gates['readiness_score'] >= 0.90:
        st.warning("⚠️ MERGE + Monitoring")
    else:
        st.error("🔧 REWORK")

# Страница Audit Trail
elif page == "📝 Audit Trail":
    st.header("📝 Glass Box Audit Trail")
    
    st.info("🚧 В разработке: Glass Box Audit visualization")
    
    # Пример записей
    st.subheader("Recent Audit Entries")
    
    sample_entries = [
        {
            "step_id": 1,
            "timestamp": "2026-03-06 12:00:00",
            "agent": "ChernoffVerifier",
            "decision": "VERIFIED",
            "confidence": 0.97,
        },
        {
            "step_id": 2,
            "timestamp": "2026-03-06 12:01:00",
            "agent": "AuditEngine",
            "decision": "VALID",
            "confidence": 0.99,
        },
    ]
    
    for entry in sample_entries:
        with st.expander(f"Step {entry['step_id']}: {entry['agent']} — {entry['decision']}"):
            st.write(f"**Timestamp:** {entry['timestamp']}")
            st.write(f"**Confidence:** {entry['confidence']:.0%}")
            st.write(f"**Merkle Hash:** `0x...`")

# Страница Settings
elif page == "⚙️ Settings":
    st.header("⚙️ Settings")
    
    st.subheader("Project Info")
    st.write(f"**Version:** 0.7.0")
    st.write(f"**Last Updated:** 2026-03-06")
    st.write(f"**Python:** 3.11+")
    
    st.subheader("Export")
    
    if st.button("📥 Export Metrics (JSON)"):
        metrics = load_metrics()
        st.download_button(
            label="Download JSON",
            data=json.dumps(metrics, indent=2),
            file_name="ccbm_metrics.json",
            mime="application/json",
        )
    
    st.subheader("Links")
    st.markdown("""
    - [GitHub Repository](https://github.com/sergeeey/ContextProof-2026)
    - [Documentation](docs/README.md)
    - [Security Audit](docs/SECURITY_AUDIT_REPORT.md)
    """)

# Footer
st.markdown("---")
st.caption(f"CCBM Dashboard v2.0.0 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
