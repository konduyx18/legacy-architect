"""
Legacy Architect - Streamlit UI
A visual interface for viewing refactoring artifacts.
"""
import streamlit as st
import json
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Legacy Architect",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with eye-catching gradient effects
st.markdown("""
<style>
@keyframes shimmer {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes glow {
    0%, 100% { text-shadow: 0 0 10px rgba(255, 217, 61, 0.5); }
    50% { text-shadow: 0 0 20px rgba(255, 217, 61, 0.8), 0 0 30px rgba(255, 217, 61, 0.6); }
}

.main-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #667eea 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    padding: 20px 0 10px 0;
    animation: shimmer 4s ease-in-out infinite;
    letter-spacing: 1px;
}

.subtitle {
    font-size: 1.3rem;
    color: #e2e8f0;
    text-align: center;
    margin-bottom: 30px;
    font-weight: 500;
}

.gemini-badge {
    background: linear-gradient(135deg, #ffd93d 0%, #f5576c 100%);
    padding: 6px 18px;
    border-radius: 25px;
    color: #1a202c;
    font-weight: 800;
    display: inline-block;
    animation: glow 2s ease-in-out infinite;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.4);
}

.workflow-arrow {
    color: #f093fb;
    font-weight: bold;
    margin: 0 8px;
}

.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 1rem;
    color: #155724;
}
</style>
""", unsafe_allow_html=True)

# Artifact paths
ARTIFACTS_DIR = Path("artifacts")


def load_json(filename):
    """Load a JSON file from artifacts directory."""
    filepath = ARTIFACTS_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_text(filename):
    """Load a text file from artifacts directory."""
    filepath = ARTIFACTS_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## 🏗️ Legacy Architect")
        st.markdown("⚡ AI-Powered Code Refactoring")
        st.markdown("---")
        
        st.markdown("### 🎯 Project Info")
        st.markdown("""
        - **Target:** `billing.py`
        - **Function:** `compute_invoice_total`
        - **Model:** Gemini 3 Flash
        """)
        
        st.markdown("---")
        st.markdown("### 🔗 Links")
        st.markdown("[GitHub Repo](https://github.com/konduyx18/legacy-architect)")
        st.markdown("[Gemini 3 Hackathon](https://gemini3.devpost.com/)")
    
    # Main content - Eye-catching title with gradient effects
    st.markdown("""
    <div class="main-title">
        🤖 Analyze <span class="workflow-arrow">→</span> Refactor <span class="workflow-arrow">→</span> Verify
    </div>
    <div class="subtitle">
        ✨ Transform Legacy Code Safely with <span class="gemini-badge">Gemini 3 AI</span> ✨
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Check if artifacts exist
    if not ARTIFACTS_DIR.exists() or not any(ARTIFACTS_DIR.iterdir()):
        st.warning("⚠️ No artifacts found. Run the agent first: `python -m legacy_architect run`")
        st.code("python -m legacy_architect run", language="bash")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "🗺️ Impact Map",
        "📋 Refactor Plan",
        "📝 Code Diff",
        "🧪 Test Results",
        "📜 Evidence Report"
    ])
    
    # Tab 1: Overview
    with tab1:
        st.markdown("## 📊 Refactoring Overview")
        
        plan = load_json("plan.json")
        impact = load_json("impact.json")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            issues = len(plan.get("issues", [])) if plan else 0
            st.metric("🔍 Issues Found", issues)
        
        with col2:
            improvements = len(plan.get("improvements", [])) if plan else 0
            st.metric("✨ Improvements", improvements)
        
        with col3:
            call_sites = impact.get("summary", {}).get("call_sites", 0) if impact else 0
            st.metric("📍 Call Sites", call_sites)
        
        with col4:
            test_files = impact.get("summary", {}).get("test_files", 0) if impact else 0
            st.metric("🧪 Test Files", test_files)
        
        st.markdown("---")
        
        if plan:
            st.markdown("### 📝 Refactoring Summary")
            st.info(plan.get("summary", "No summary available"))
            
            st.markdown("### 🎯 Key Issues Identified")
            for i, issue in enumerate(plan.get("issues", [])[:5], 1):
                st.markdown(f"**{i}.** {issue}")
    
    # Tab 2: Impact Map
    with tab2:
        st.markdown("## 🗺️ Impact Analysis")
        
        impact = load_json("impact.json")
        if impact:
            summary = impact.get("summary", {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📁 Total Files", summary.get("total_files", 0))
            with col2:
                st.metric("📍 Total Usages", summary.get("total_usages", 0))
            with col3:
                st.metric("🔗 Call Sites", summary.get("call_sites", 0))
            
            st.markdown("---")
            
            st.markdown("### 📍 Call Sites (Production Code)")
            call_sites = impact.get("call_sites", [])
            if call_sites:
                for site in call_sites:
                    with st.expander(f"📄 {site['file']} ({site['usage_count']} usages)"):
                        st.code(f"Lines: {site['lines']}")
            else:
                st.info("No call sites found")
            
            st.markdown("### 🧪 Test Files")
            test_files = impact.get("test_files", [])
            if test_files:
                for tf in test_files:
                    with st.expander(f"🧪 {tf['file']} ({tf['usage_count']} usages)"):
                        st.code(f"Lines: {tf['lines'][:10]}...")
            
            st.download_button(
                "📥 Download impact.json",
                json.dumps(impact, indent=2),
                "impact.json",
                "application/json"
            )
        else:
            st.warning("Impact map not found")
    
    # Tab 3: Refactor Plan
    with tab3:
        st.markdown("## 📋 Refactoring Plan")
        
        plan = load_json("plan.json")
        if plan:
            st.markdown("### 📝 Summary")
            st.info(plan.get("summary", "No summary"))
            
            st.markdown("### 🔍 Issues Identified")
            for i, issue in enumerate(plan.get("issues", []), 1):
                st.markdown(f"**{i}.** {issue}")
            
            st.markdown("### ✨ Planned Improvements")
            for i, imp in enumerate(plan.get("improvements", []), 1):
                st.markdown(f"**{i}.** {imp}")
            
            st.markdown("### 📦 Constants to Extract")
            constants = plan.get("constants", {})
            if constants:
                st.json(constants)
            
            st.markdown("### 🔧 Helper Functions")
            helpers = plan.get("helper_functions", [])
            for h in helpers:
                with st.expander(f"🔧 {h.get('name', 'Unknown')}"):
                    st.markdown(f"**Description:** {h.get('description', 'N/A')}")
                    st.markdown(f"**Parameters:** {h.get('parameters', 'N/A')}")
                    st.markdown(f"**Returns:** {h.get('returns', 'N/A')}")
            
            st.download_button(
                "📥 Download plan.json",
                json.dumps(plan, indent=2),
                "plan.json",
                "application/json"
            )
        else:
            st.warning("Refactoring plan not found")
    
    # Tab 4: Code Diff
    with tab4:
        st.markdown("## 📝 Code Changes")
        
        diff = load_text("diff.patch")
        if diff:
            st.markdown("### 🔄 Unified Diff")
            st.code(diff, language="diff")
            
            additions = diff.count("\n+") - diff.count("\n+++")
            deletions = diff.count("\n-") - diff.count("\n---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("➕ Additions", additions)
            with col2:
                st.metric("➖ Deletions", deletions)
            
            st.download_button(
                "📥 Download diff.patch",
                diff,
                "diff.patch",
                "text/plain"
            )
        else:
            st.warning("Diff file not found")
    
    # Tab 5: Test Results
    with tab5:
        st.markdown("## 🧪 Test Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔵 Default Mode")
            default_log = load_text("test_default.log")
            if default_log:
                if "passed" in default_log.lower():
                    st.success("✅ Tests executed!")
                with st.expander("📄 View Full Log"):
                    st.code(default_log)
            else:
                st.warning("No default test log found")
        
        with col2:
            st.markdown("### 🟢 BILLING_V2 Mode")
            flag_log = load_text("test_flag.log")
            if flag_log:
                if "passed" in flag_log.lower():
                    st.success("✅ Tests executed!")
                with st.expander("📄 View Full Log"):
                    st.code(flag_log)
            else:
                st.warning("No flag test log found")
    
    # Tab 6: Evidence Report
    with tab6:
        st.markdown("## 📜 Evidence Report")
        
        evidence = load_text("EVIDENCE.md")
        if evidence:
            st.markdown(evidence)
            
            st.download_button(
                "📥 Download EVIDENCE.md",
                evidence,
                "EVIDENCE.md",
                "text/markdown"
            )
        else:
            st.warning("Evidence report not found")


if __name__ == "__main__":
    main()
