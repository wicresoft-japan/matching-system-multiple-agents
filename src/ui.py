"""
Bidirectional Matching UI — Streamlit app.
Usage: streamlit run src/ui.py
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.models import Profile, Project, load_profiles, load_projects
from src.matcher import bidirectional_match

st.set_page_config(page_title="双方向マッチング", page_icon="🔗", layout="wide")
st.title("🔗 経歴 × 案件 双方向マッチング")

# ── Sidebar: Data Source ──────────────────────────────────────────────
with st.sidebar:
    st.header("📂 データソース")
    data_mode = st.radio("データの読み込み方法", ["サンプルデータ", "ファイルアップロード"])

    if data_mode == "サンプルデータ":
        profiles_path = Path("data/profiles.json")
        projects_path = Path("data/projects.json")
    else:
        profiles_file = st.file_uploader("経歴 JSON", type=["json"])
        projects_file = st.file_uploader("案件 JSON", type=["json"])
        profiles_path = None
        projects_path = None

    st.divider()
    st.header("⚙️ フィルタ")
    min_score = st.slider("最低スコア (%)", 0, 100, 0, step=5)

    st.divider()
    st.caption("スコア = 共通スキル数 / 案件必須スキル数")
    st.caption("経験年数不足 → スコア 0（非表示）")


# ── Load Data ──────────────────────────────────────────────────────────
@st.cache_data
def load_data(profiles_path, projects_path):
    """Load profiles and projects from paths."""
    return load_profiles(str(profiles_path)), load_projects(str(projects_path))


def parse_uploaded(uploaded_file):
    """Parse an uploaded JSON file into a list of dicts."""
    return json.loads(uploaded_file.read())


try:
    if data_mode == "サンプルデータ":
        profiles, projects = load_data(profiles_path, projects_path)
    else:
        if profiles_file is None or projects_file is None:
            st.info("👈 サイドバーから経歴と案件のJSONファイルをアップロードしてください")
            st.stop()
        profiles_data = parse_uploaded(profiles_file)
        projects_data = parse_uploaded(projects_file)
        profiles = [Profile(**p) for p in profiles_data]
        projects = [Project(**p) for p in projects_data]

    # Run matching
    results = bidirectional_match(profiles, projects)
except FileNotFoundError as e:
    st.error(f"ファイルが見つかりません: {e}")
    st.stop()
except Exception as e:
    st.error(f"データ読み込みエラー: {e}")
    st.stop()


# ── Apply score filter ─────────────────────────────────────────────────
def apply_filter(matches_dict: dict, min_score: float) -> dict:
    """Filter out matches below the minimum score threshold."""
    threshold = min_score / 100.0
    return {
        key: [m for m in matches if m.score >= threshold]
        for key, matches in matches_dict.items()
    }


profile_matches = apply_filter(results["profile_matches"], min_score)
project_matches = apply_filter(results["project_matches"], min_score)


# ── Metrics ────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("経歴数", len(profiles))
with col2:
    st.metric("案件数", len(projects))
with col3:
    total_pm = sum(len(v) for v in profile_matches.values())
    st.metric("経歴→案件 マッチ数", total_pm)
with col4:
    total_pj = sum(len(v) for v in project_matches.values())
    st.metric("案件→経歴 マッチ数", total_pj)


# ── Tabs ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 経歴 → 案件", "📊 案件 → 経歴", "📋 生データ"])


def render_match_card(match, index: int):
    """Render a single match result as a card."""
    pct = round(match.score * 100)
    color = "🟢" if pct >= 80 else "🟡" if pct >= 50 else "🟠"
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(
            f"**{index}. {match.target_name}** `({match.target_id})`  "
            f" — スキル: {', '.join(match.matched_skills)}"
        )
    with col_b:
        st.markdown(f"{color} **{pct}%**")
    st.progress(match.score)


with tab1:
    st.subheader("経歴ごとにマッチする案件を表示")
    if not profile_matches:
        st.info("マッチする案件がありません")
    else:
        for pid, matches in profile_matches.items():
            if not matches:
                continue
            name = matches[0].source_name
            with st.expander(f"👤 {name} ({pid}) — {len(matches)}件マッチ", expanded=True):
                for i, m in enumerate(matches, 1):
                    render_match_card(m, i)

with tab2:
    st.subheader("案件ごとにマッチする経歴を表示")
    if not project_matches:
        st.info("マッチする経歴がありません")
    else:
        for pid, matches in project_matches.items():
            if not matches:
                continue
            name = matches[0].source_name
            with st.expander(f"📁 {name} ({pid}) — {len(matches)}件マッチ", expanded=True):
                for i, m in enumerate(matches, 1):
                    render_match_card(m, i)

with tab3:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("経歴データ")
        st.dataframe(
            [
                {"ID": p.id, "名前": p.name, "スキル": ", ".join(p.skills), "経験年数": p.experience_years}
                for p in profiles
            ],
            use_container_width=True,
            hide_index=True,
        )
    with col_right:
        st.subheader("案件データ")
        st.dataframe(
            [
                {"ID": p.id, "案件名": p.name, "必須スキル": ", ".join(p.required_skills), "最低経験年数": p.min_experience_years}
                for p in projects
            ],
            use_container_width=True,
            hide_index=True,
        )
