"""
COM6003 — Buckinghamshire EPC Energy Performance Dashboard
Premium Streamlit Cloud version.

Uses the processed notebook outputs in the same folder as app.py.
No st.dataframe is used, so the app remains stable in hosted/tunnelled environments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Buckinghamshire EPC Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
FILES = {
    "epc": BASE_DIR / "cleaned_buckinghamshire_epc.csv",
    "models": BASE_DIR / "model_results.csv",
    "perm": BASE_DIR / "permutation_feature_importance.csv",
    "rf": BASE_DIR / "random_forest_feature_importance.csv",
    "fig01": BASE_DIR / "fig01_rating_distribution.png",
    "fig17": BASE_DIR / "fig17_model_comparison.png",
    "fig18": BASE_DIR / "fig18_confusion_matrix.png",
    "fig19": BASE_DIR / "fig19_permutation_importance.png",
    "fig20": BASE_DIR / "fig20_grouped_permutation_importance.png",
    "fig21": BASE_DIR / "fig21_rf_mdi_importance.png",
}

RATING_ORDER = ["A", "B", "C", "D", "E", "F", "G"]
RATING_SCORE_MAP = {"A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1}
RATING_COLORS = {
    "A": "#20d083",
    "B": "#63d471",
    "C": "#b4e769",
    "D": "#ffe84a",
    "E": "#ff9f1c",
    "F": "#ff5a2e",
    "G": "#ef233c",
}

ACCENT = "#2dd4bf"
BLUE = "#60a5fa"
PURPLE = "#a78bfa"
PINK = "#fb7185"
AMBER = "#fbbf24"
GREEN = "#4ade80"
DARK = "#0b1020"
CARD = "rgba(18, 27, 49, 0.84)"
BORDER = "rgba(148, 163, 184, 0.18)"
TEXT = "#e5eefb"
MUTED = "#94a3b8"

# -----------------------------------------------------------------------------
# CSS
# -----------------------------------------------------------------------------
st.markdown(
    f"""
<style>
:root {{
    --bg: #070b16;
    --panel: rgba(15, 23, 42, .82);
    --panel2: rgba(18, 27, 49, .88);
    --text: {TEXT};
    --muted: {MUTED};
    --line: {BORDER};
    --teal: {ACCENT};
    --blue: {BLUE};
    --purple: {PURPLE};
    --pink: {PINK};
    --amber: {AMBER};
    --green: {GREEN};
}}
html, body, [data-testid="stAppViewContainer"] {{
    background:
      radial-gradient(circle at 18% 8%, rgba(45, 212, 191, .16), transparent 30%),
      radial-gradient(circle at 88% 0%, rgba(96, 165, 250, .14), transparent 28%),
      radial-gradient(circle at 62% 80%, rgba(167, 139, 250, .12), transparent 30%),
      var(--bg) !important;
    color: var(--text) !important;
}}
.block-container {{ padding-top: 1.2rem !important; max-width: 1440px !important; }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, rgba(10,15,30,.98), rgba(13,20,38,.96)) !important;
    border-right: 1px solid rgba(148,163,184,.14);
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {{ color: white !important; }}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] {{ color: var(--muted) !important; }}
[data-testid="stSidebar"] .stAlert {{ background: rgba(45,212,191,.12) !important; border: 1px solid rgba(45,212,191,.25) !important; }}

/* Header + tabs */
h1, h2, h3, h4 {{ letter-spacing: -.025em; color: var(--text) !important; }}
p, li, span, label, div {{ color: inherit; }}
[data-testid="stTabs"] [role="tablist"] {{
    background: rgba(15,23,42,.64);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(148,163,184,.16);
    border-radius: 999px;
    padding: .35rem;
    gap: .15rem;
    box-shadow: 0 20px 60px rgba(0,0,0,.18);
}}
[data-testid="stTabs"] button[role="tab"] {{
    border-radius: 999px !important;
    color: #cbd5e1 !important;
    font-weight: 700 !important;
    padding: .65rem 1rem !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: #06121d !important;
    background: linear-gradient(135deg, var(--teal), #93c5fd) !important;
}}

/* Custom cards */
.hero-card {{
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    padding: 3rem 3.2rem;
    margin: .25rem 0 1.25rem 0;
    background:
      linear-gradient(135deg, rgba(11,16,32,.98) 0%, rgba(18,47,74,.92) 52%, rgba(13,148,136,.88) 100%);
    border: 1px solid rgba(148,163,184,.20);
    box-shadow: 0 30px 90px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.07);
}}
.hero-card:before {{
    content: "";
    position: absolute; inset: -20% -10% auto auto;
    width: 520px; height: 520px;
    background: radial-gradient(circle, rgba(45,212,191,.34), transparent 62%);
    filter: blur(4px);
}}
.hero-card:after {{
    content: "";
    position: absolute; inset: auto auto -40% -8%;
    width: 360px; height: 360px;
    background: radial-gradient(circle, rgba(96,165,250,.25), transparent 62%);
}}
.hero-inner {{ position: relative; z-index: 1; max-width: 920px; }}
.hero-tag {{
    display: inline-flex; gap: .45rem; align-items: center;
    padding: .42rem .78rem;
    border-radius: 999px;
    background: rgba(45,212,191,.15);
    border: 1px solid rgba(45,212,191,.36);
    color: #99f6e4;
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
}}
.hero-title {{
    margin: 1rem 0 .8rem 0;
    font-size: clamp(2.2rem, 5vw, 4.6rem);
    line-height: .98;
    font-weight: 900;
    color: #fff;
}}
.hero-title .gradient {{
    background: linear-gradient(135deg, #fff, #9ee7ff 40%, #8ff7d6 100%);
    -webkit-background-clip: text;
    color: transparent;
}}
.hero-copy {{ max-width: 760px; color: #c9d7ea; font-size: 1.08rem; line-height: 1.75; }}
.hero-meta {{ display:flex; flex-wrap:wrap; gap:.65rem; margin-top:1.35rem; }}
.chip {{
    display:inline-flex; align-items:center; gap:.45rem;
    padding:.45rem .75rem; border-radius:999px;
    background: rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12);
    color:#dbeafe; font-weight:700; font-size:.85rem;
}}
.kpi-grid {{ display:grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap:1rem; margin: 1.1rem 0 1.5rem; }}
.kpi {{
    background: linear-gradient(180deg, rgba(255,255,255,.075), rgba(255,255,255,.045));
    border:1px solid rgba(148,163,184,.16);
    border-radius: 22px;
    padding:1.15rem 1.2rem;
    box-shadow: 0 18px 50px rgba(0,0,0,.24);
    position:relative; overflow:hidden;
}}
.kpi:before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px; background: var(--accent, var(--teal)); }}
.kpi-label {{ color: var(--muted); text-transform: uppercase; font-weight:800; letter-spacing:.08em; font-size:.72rem; }}
.kpi-value {{ color:white; font-size:2.15rem; font-weight:900; line-height:1.1; margin:.38rem 0 .2rem; }}
.kpi-sub {{ color:#b6c5d8; font-size:.86rem; line-height:1.4; }}
.card {{
    background: var(--panel);
    border: 1px solid rgba(148,163,184,.16);
    border-radius: 24px;
    padding: 1.3rem 1.35rem;
    box-shadow: 0 24px 65px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.04);
}}
.glow-card {{
    background: linear-gradient(135deg, rgba(13,148,136,.18), rgba(96,165,250,.12));
    border: 1px solid rgba(45,212,191,.25);
    border-radius: 24px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 20px 50px rgba(45,212,191,.08);
}}
.section-eyebrow {{ color: var(--teal); text-transform: uppercase; font-size:.78rem; letter-spacing:.14em; font-weight:900; margin-bottom:.35rem; }}
.section-title {{ font-size:2rem; font-weight:900; margin: 0 0 .4rem; color:white; }}
.section-copy {{ color: #b7c6d9; line-height:1.65; font-size:1rem; margin-bottom: 1rem; }}
.insight {{
    border-left: 4px solid var(--teal);
    background: linear-gradient(135deg, rgba(45,212,191,.12), rgba(96,165,250,.08));
    border-radius: 0 18px 18px 0;
    padding: 1rem 1.1rem;
    color: #dbeafe;
}}
.insight b {{ color: #fff; }}
.reco {{
    border-radius: 24px;
    padding: 1.25rem 1.35rem;
    background: linear-gradient(135deg, rgba(18,27,49,.96), rgba(15,23,42,.86));
    border: 1px solid rgba(148,163,184,.17);
    box-shadow: 0 18px 55px rgba(0,0,0,.18);
    height: 100%;
}}
.reco-icon {{ font-size:1.7rem; margin-bottom:.5rem; }}
.reco-title {{ font-size:1.05rem; font-weight:900; color:white; margin-bottom:.35rem; }}
.reco-body {{ color:#b8c7da; line-height:1.65; font-size:.95rem; }}
.footer {{
    text-align:center; color:#8ea1ba; font-size:.86rem; margin: 2rem 0 1rem;
    padding:1.1rem; border-top:1px solid rgba(148,163,184,.15);
}}

/* Native Streamlit elements */
.stAlert {{ border-radius: 18px !important; }}
[data-testid="stMetric"] {{
    background: rgba(255,255,255,.045);
    border: 1px solid rgba(148,163,184,.14);
    padding: 1rem;
    border-radius: 18px;
}}
[data-testid="stMetricValue"] {{ color: white !important; }}
[data-testid="stMetricLabel"] {{ color: #b7c6d9 !important; }}
button, [data-testid="stBaseButton-secondary"] {{ border-radius: 999px !important; }}
hr {{ border-color: rgba(148,163,184,.18) !important; }}
@media (max-width: 1100px) {{ .kpi-grid {{ grid-template-columns: repeat(2, minmax(0,1fr)); }} }}
@media (max-width: 680px) {{ .hero-card {{ padding:2rem; }} .kpi-grid {{ grid-template-columns: 1fr; }} }}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False)


@st.cache_data(show_spinner=False)
def load_epc(path: Path) -> Optional[pd.DataFrame]:
    df = load_csv(path)
    if df is None:
        return None
    if "CURRENT_ENERGY_RATING" in df.columns:
        df["CURRENT_ENERGY_RATING"] = df["CURRENT_ENERGY_RATING"].astype(str).str.upper().str.strip()
        df["RATING_SCORE"] = df["CURRENT_ENERGY_RATING"].map(RATING_SCORE_MAP)
    for col in ["PROPERTY_TYPE", "BUILT_FORM", "CONSTRUCTION_AGE_BAND", "PROPERTY_AGE_GROUP", "TENURE", "MAIN_FUEL"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)
    if "TOTAL_FLOOR_AREA" in df.columns:
        df["TOTAL_FLOOR_AREA"] = pd.to_numeric(df["TOTAL_FLOOR_AREA"], errors="coerce")
    if "TENURE" in df.columns:
        df["TENURE"] = df["TENURE"].replace(
            {
                "owner-occupied": "Owner-occupied",
                "rental (private)": "Rented (private)",
                "rental (social)": "Rented (social)",
                "unknown": "Unknown",
                "Not defined - use in the case of a new dwelling for which the intended tenure in not known. It is not to be used for an existing dwelling": "New dwelling (tenure TBD)",
            }
        )
    return df


@st.cache_data(show_spinner=False)
def load_image(path: Path) -> Optional[Image.Image]:
    if not path.exists():
        return None
    return Image.open(path)

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------
def safe_col(df: Optional[pd.DataFrame], col: str) -> bool:
    return df is not None and col in df.columns


def clean_categories(values: Iterable[str]) -> list[str]:
    bad = {"Unknown", "Not Recorded", "NO DATA!", "INVALID!", "nan", "None", "N/A"}
    return [str(v) for v in values if str(v) not in bad]


def html_kpi(label: str, value: str, sub: str, color: str) -> str:
    return f"""
    <div class='kpi' style='--accent:{color}'>
      <div class='kpi-label'>{label}</div>
      <div class='kpi-value'>{value}</div>
      <div class='kpi-sub'>{sub}</div>
    </div>
    """


def html_section(eyebrow: str, title: str, copy: str = "") -> None:
    st.markdown(
        f"<div class='section-eyebrow'>{eyebrow}</div><div class='section-title'>{title}</div>"
        + (f"<div class='section-copy'>{copy}</div>" if copy else ""),
        unsafe_allow_html=True,
    )


def show_image(key: str, caption: str):
    img = load_image(FILES[key])
    if img is None:
        st.warning(f"Missing image: {FILES[key].name}")
    else:
        st.image(img, caption=caption, width="stretch")


def style_fig(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=20, r=20, t=70, b=45),
        font=dict(size=13, color=TEXT),
        title_font=dict(size=20, color="#ffffff"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,.42)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="rgba(148,163,184,.18)", zerolinecolor="rgba(148,163,184,.22)"),
        yaxis=dict(gridcolor="rgba(148,163,184,.18)", zerolinecolor="rgba(148,163,184,.22)"),
    )
    return fig

# -----------------------------------------------------------------------------
# Charts
# -----------------------------------------------------------------------------
def rating_distribution_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["CURRENT_ENERGY_RATING"].value_counts().reindex(RATING_ORDER).fillna(0).astype(int)
    total = counts.sum()
    fig = go.Figure(
        data=[
            go.Bar(
                x=counts.index,
                y=counts.values,
                text=[f"{v:,}<br>{(v / total * 100):.1f}%" if total else "0" for v in counts],
                textposition="outside",
                marker_color=[RATING_COLORS.get(r, "#64748b") for r in counts.index],
                marker_line=dict(color="rgba(255,255,255,.22)", width=1),
                hovertemplate="Rating %{x}<br>%{y:,} certificates<extra></extra>",
            )
        ]
    )
    fig.update_layout(title="Distribution of Current EPC Ratings", xaxis_title="Energy Rating", yaxis_title="Number of certificates")
    return style_fig(fig, 430)


def count_bar_chart(df: pd.DataFrame, col: str, title: str, top_n: int = 15) -> go.Figure:
    vc = df[col].fillna("Unknown").value_counts().head(top_n).sort_values()
    fig = px.bar(
        x=vc.values,
        y=vc.index,
        orientation="h",
        text=vc.values,
        title=title,
        labels={"x": "Number of certificates", "y": col.replace("_", " ").title()},
        color=vc.values,
        color_continuous_scale=["#0f172a", "#0ea5e9", "#2dd4bf"],
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", hovertemplate="%{y}<br>%{x:,}<extra></extra>")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return style_fig(fig, max(370, 30 * len(vc) + 120))


def average_score_chart(df: pd.DataFrame, col: str, title: str, top_n: Optional[int] = None) -> go.Figure:
    tmp = df[[col, "RATING_SCORE"]].dropna()
    tmp = tmp[~tmp[col].isin(["Unknown", "Not Recorded", "NO DATA!", "INVALID!", "N/A"])]
    grp = tmp.groupby(col)["RATING_SCORE"].mean().sort_values(ascending=True)
    if top_n:
        grp = grp.tail(top_n)
    fig = px.bar(
        x=grp.values,
        y=grp.index.astype(str),
        orientation="h",
        text=[f"{v:.2f}" for v in grp.values],
        title=title,
        labels={"x": "Average rating score (A=7, G=1)", "y": col.replace("_", " ").title()},
        color=grp.values,
        color_continuous_scale=["#ef4444", "#fbbf24", "#2dd4bf"],
    )
    fig.update_traces(textposition="outside", hovertemplate="%{y}<br>Average score: %{x:.2f}<extra></extra>")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_range=[0, 7.5])
    return style_fig(fig, max(370, 32 * len(grp) + 120))


def floor_area_box(df: pd.DataFrame) -> go.Figure:
    plot_df = df[["CURRENT_ENERGY_RATING", "TOTAL_FLOOR_AREA"]].dropna().copy()
    plot_df = plot_df[plot_df["CURRENT_ENERGY_RATING"].isin(RATING_ORDER)]
    if not plot_df.empty:
        upper = plot_df["TOTAL_FLOOR_AREA"].quantile(0.99)
        plot_df = plot_df[plot_df["TOTAL_FLOOR_AREA"] <= upper]
    fig = px.box(
        plot_df,
        x="CURRENT_ENERGY_RATING",
        y="TOTAL_FLOOR_AREA",
        category_orders={"CURRENT_ENERGY_RATING": RATING_ORDER},
        color="CURRENT_ENERGY_RATING",
        color_discrete_map=RATING_COLORS,
        title="Total Floor Area by EPC Rating",
        labels={"CURRENT_ENERGY_RATING": "Energy rating", "TOTAL_FLOOR_AREA": "Total floor area (m²)"},
    )
    fig.update_layout(showlegend=False)
    return style_fig(fig, 450)


def stacked_rating_chart(df: pd.DataFrame, group_col: str, title: str) -> go.Figure:
    ct = pd.crosstab(df[group_col], df["CURRENT_ENERGY_RATING"])
    ct = ct.loc[clean_categories(ct.index.astype(str))]
    ct = ct[ct.sum(axis=1) > 0]
    if len(ct) > 12:
        keep = ct.sum(axis=1).sort_values(ascending=False).head(12).index
        ct = ct.loc[keep]
    pct = ct.div(ct.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for rating in RATING_ORDER:
        if rating in pct.columns:
            fig.add_bar(
                x=pct.index.astype(str),
                y=pct[rating],
                name=rating,
                marker_color=RATING_COLORS.get(rating, "#64748b"),
                hovertemplate=f"Rating {rating}: %{{y:.1f}}%<extra></extra>",
            )
    fig.update_layout(title=title, barmode="stack", xaxis_title=group_col.replace("_", " ").title(), yaxis_title="Percentage of certificates")
    return style_fig(fig, 470)


def model_comparison_chart(model_df: pd.DataFrame) -> go.Figure:
    metrics = ["Accuracy", "Macro F1", "Weighted F1"]
    long_df = model_df.melt(id_vars="Model", value_vars=metrics, var_name="Metric", value_name="Score")
    fig = px.bar(
        long_df,
        x="Model",
        y="Score",
        color="Metric",
        barmode="group",
        text="Score",
        title="Model Performance Comparison",
        color_discrete_sequence=["#60a5fa", "#2dd4bf", "#a78bfa"],
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(yaxis_range=[0, 1.05], xaxis_title="", yaxis_title="Score")
    return style_fig(fig, 440)


def feature_importance_chart(perm_df: pd.DataFrame, n: int = 20) -> go.Figure:
    top = perm_df.head(n).copy().iloc[::-1]
    fig = px.bar(
        top,
        x="Perm_Mean",
        y="Feature",
        orientation="h",
        error_x="Perm_Std" if "Perm_Std" in top.columns else None,
        title=f"Top {n} Permutation Feature Importances",
        labels={"Perm_Mean": "Mean decrease in Macro F1", "Feature": "Feature"},
        color="Perm_Mean",
        color_continuous_scale=["#13223e", "#22c55e", "#b9fbc0"],
    )
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(520, 28 * n + 140))


def grouped_importance_chart(perm_df: pd.DataFrame, n: int = 20) -> go.Figure:
    known = [
        "HOT_WATER_ENERGY_EFF", "IS_LOW_EFFICIENCY_HEATING", "INSULATION_QUALITY_SCORE",
        "MAINHEAT_ENERGY_EFF", "FLOOR_DESCRIPTION", "BUILT_FORM", "ROOF_ENERGY_EFF",
        "WALLS_ENERGY_EFF", "MAINHEAT_DESCRIPTION", "MAIN_FUEL", "MECHANICAL_VENTILATION",
        "CONSTRUCTION_AGE_BAND", "ROOF_DESCRIPTION", "NUMBER_HEATED_ROOMS",
        "LIGHTING_DESCRIPTION", "NUMBER_HABITABLE_ROOMS", "WINDOWS_ENERGY_EFF",
        "FLOOR_AREA_BAND", "PROPERTY_AGE_GROUP", "TRANSACTION_TYPE", "TOTAL_FLOOR_AREA",
        "MULTI_GLAZE_PROPORTION", "HEATED_ROOM_RATIO", "EXTENSION_COUNT",
        "NUMBER_OPEN_FIREPLACES", "FLOOR_HEIGHT", "FIXED_LIGHTING_OUTLETS_COUNT",
        "LOW_ENERGY_LIGHTING", "HAS_SOLAR_WATER_HEATING", "SOLAR_WATER_HEATING_FLAG",
        "MAINS_GAS_FLAG", "ENERGY_TARIFF", "GLAZED_TYPE", "GLAZED_AREA",
        "WINDOWS_DESCRIPTION", "TENURE", "PROPERTY_TYPE", "MAINHEATCONT_DESCRIPTION",
        "MAINHEATC_ENERGY_EFF", "LOW_LIGHTING_BAND", "HOTWATER_DESCRIPTION",
        "LIGHTING_ENERGY_EFF", "WALLS_DESCRIPTION",
    ]

    def original_feature(feature: str) -> str:
        for base in sorted(known, key=len, reverse=True):
            if str(feature).startswith(base):
                return base
        return str(feature)

    tmp = perm_df.copy()
    tmp["Original_Feature"] = tmp["Feature"].apply(original_feature)
    grouped = tmp.groupby("Original_Feature", as_index=False)["Perm_Mean"].sum().sort_values("Perm_Mean", ascending=False).head(n).iloc[::-1]
    fig = px.bar(
        grouped,
        x="Perm_Mean",
        y="Original_Feature",
        orientation="h",
        title=f"Grouped Feature Importance - Top {n}",
        labels={"Perm_Mean": "Summed permutation importance", "Original_Feature": "Original feature"},
        color="Perm_Mean",
        color_continuous_scale=["#10213d", "#60a5fa", "#dbeafe"],
    )
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(520, 28 * n + 140))


def rf_importance_chart(rf_df: pd.DataFrame, n: int = 20) -> go.Figure:
    top = rf_df.head(n).copy().iloc[::-1]
    fig = px.bar(
        top,
        x="MDI_Importance",
        y="Feature",
        orientation="h",
        title=f"Random Forest MDI Feature Importance - Top {n}",
        labels={"MDI_Importance": "Mean decrease in impurity", "Feature": "Feature"},
        color="MDI_Importance",
        color_continuous_scale=["#211827", "#fb7185", "#fed7aa"],
    )
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(520, 28 * n + 140))

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
def sidebar_summary(df: Optional[pd.DataFrame]) -> None:
    st.sidebar.markdown("### ⚡ EPC Dashboard")
    st.sidebar.caption("COM6003 Data Science · Buckinghamshire")
    st.sidebar.divider()
    if df is None:
        st.sidebar.error("Dataset not found")
        return
    st.sidebar.metric("Total certificates", f"{len(df):,}")
    st.sidebar.metric("Property types", f"{df['PROPERTY_TYPE'].nunique() if 'PROPERTY_TYPE' in df.columns else 0}")
    st.sidebar.metric("Ratings available", f"{df['CURRENT_ENERGY_RATING'].nunique() if 'CURRENT_ENERGY_RATING' in df.columns else 0}")
    st.sidebar.divider()
    st.sidebar.success("Live dashboard mode. Full Buckinghamshire EPC dataset loaded.")
    st.sidebar.caption("For formal marking, the notebook remains the primary reproducible evidence.")

# -----------------------------------------------------------------------------
# Main app
# -----------------------------------------------------------------------------
def main() -> None:
    df = load_epc(FILES["epc"])
    model_df = load_csv(FILES["models"])
    perm_df = load_csv(FILES["perm"])
    rf_df = load_csv(FILES["rf"])

    sidebar_summary(df)

    st.markdown(
        """
        <div class='hero-card'>
          <div class='hero-inner'>
            <div class='hero-tag'>⚡ COM6003 · Data Science · Buckinghamshire</div>
            <div class='hero-title'>Domestic EPC<br><span class='gradient'>Energy Intelligence Dashboard</span></div>
            <div class='hero-copy'>A polished evidence dashboard for analysing domestic Energy Performance Certificates in Buckinghamshire, exploring stock characteristics, diagnostic drivers, model performance, feature importance and retrofit priorities.</div>
            <div class='hero-meta'>
              <span class='chip'>🏠 Domestic EPCs</span>
              <span class='chip'>🧠 Predictive analytics</span>
              <span class='chip'>📊 Feature importance</span>
              <span class='chip'>🌿 Energy efficiency</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None:
        st.error("The cleaned EPC dataset was not found. Make sure all files are in the same folder as app.py.")
        for key, path in FILES.items():
            st.write(f"{'✅' if path.exists() else '❌'} `{path.name}`")
        return

    total = len(df)
    common_rating = df["CURRENT_ENERGY_RATING"].mode()[0]
    cd_pct = df["CURRENT_ENERGY_RATING"].isin(["C", "D"]).mean() * 100
    ac_pct = df["CURRENT_ENERGY_RATING"].isin(["A", "B", "C"]).mean() * 100
    best_accuracy = model_df["Accuracy"].max() if model_df is not None else np.nan
    best_macro = model_df["Macro F1"].max() if model_df is not None else np.nan
    best_acc_model = model_df.loc[model_df["Accuracy"].idxmax(), "Model"] if model_df is not None else "N/A"
    best_f1_model = model_df.loc[model_df["Macro F1"].idxmax(), "Model"] if model_df is not None else "N/A"

    st.markdown(
        "<div class='kpi-grid'>"
        + html_kpi("Total records", f"{total:,}", "Buckinghamshire domestic EPC certificates", ACCENT)
        + html_kpi("Dominant rating", str(common_rating), "Most common EPC band", RATING_COLORS.get(common_rating, BLUE))
        + html_kpi("C/D rated", f"{cd_pct:.1f}%", "Mid-efficiency certificate share", BLUE)
        + html_kpi("Best accuracy", f"{best_accuracy:.1%}" if pd.notna(best_accuracy) else "N/A", str(best_acc_model), PURPLE)
        + html_kpi("Best Macro F1", f"{best_macro:.3f}" if pd.notna(best_macro) else "N/A", str(best_f1_model), AMBER)
        + "</div>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "Executive Overview",
        "Building Insights",
        "Diagnostic Analysis",
        "Model Performance",
        "Feature Importance",
        "Recommendations",
        "Files",
    ])

    with tabs[0]:
        html_section("Executive view", "Energy performance profile", "The dashboard summarises Buckinghamshire's domestic EPC stock and the predictive modelling outputs used for the coursework analysis.")
        left, right = st.columns([2.15, 1])
        with left:
            st.plotly_chart(rating_distribution_chart(df), width="stretch", key="overview_rating_distribution")
        with right:
            st.markdown(
                f"""
                <div class='glow-card'>
                  <div class='section-eyebrow'>Key Insight</div>
                  <div style='font-size:1.05rem; line-height:1.65; color:#dbeafe;'>Most domestic EPCs are concentrated in <b>bands C and D</b>, which together account for <b>{cd_pct:.1f}%</b> of certificates. The extreme bands A and G are rare, making balanced classification more difficult.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            c1, c2 = st.columns(2)
            c1.metric("Average floor area", f"{df['TOTAL_FLOOR_AREA'].mean():.0f} m²" if safe_col(df, "TOTAL_FLOOR_AREA") else "N/A")
            c2.metric("A-C rated", f"{ac_pct:.1f}%")
            c3, c4 = st.columns(2)
            c3.metric("Property types", f"{df['PROPERTY_TYPE'].nunique() if safe_col(df, 'PROPERTY_TYPE') else 0}")
            c4.metric("Built forms", f"{df['BUILT_FORM'].nunique() if safe_col(df, 'BUILT_FORM') else 0}")
        with st.expander("Notebook-generated static EPC distribution figure"):
            show_image("fig01", "Notebook output: EPC rating distribution")

    with tabs[1]:
        html_section("Exploratory analysis", "Building energy insights", "Interactive charts reveal how rating patterns differ by property type, built form, age and total floor area.")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(rating_distribution_chart(df), width="stretch", key="insights_rating_distribution")
        with c2:
            if safe_col(df, "PROPERTY_TYPE"):
                st.plotly_chart(count_bar_chart(df, "PROPERTY_TYPE", "Property Type Distribution"), width="stretch", key="insights_property_type")
        c3, c4 = st.columns(2)
        with c3:
            if safe_col(df, "BUILT_FORM"):
                st.plotly_chart(count_bar_chart(df, "BUILT_FORM", "Built Form Distribution"), width="stretch", key="insights_built_form")
        with c4:
            if safe_col(df, "PROPERTY_TYPE"):
                st.plotly_chart(average_score_chart(df, "PROPERTY_TYPE", "Average Rating Score by Property Type"), width="stretch", key="insights_property_type_score")
        age_col = "PROPERTY_AGE_GROUP" if "PROPERTY_AGE_GROUP" in df.columns else "CONSTRUCTION_AGE_BAND"
        if safe_col(df, age_col):
            st.plotly_chart(average_score_chart(df, age_col, "Average Rating Score by Construction Age"), width="stretch", key="insights_age_score")
        if safe_col(df, "TOTAL_FLOOR_AREA"):
            st.plotly_chart(floor_area_box(df), width="stretch", key="insights_floor_area_box")

    with tabs[2]:
        html_section("Diagnostic analytics", "Why ratings differ", "The diagnostic layer links lower or higher EPC performance to physical building characteristics such as insulation, fuel, heating efficiency and built form.")
        c1, c2 = st.columns(2)
        with c1:
            if safe_col(df, "BUILT_FORM"):
                st.plotly_chart(average_score_chart(df, "BUILT_FORM", "Mean Rating Score by Built Form"), width="stretch", key="diag_built_form")
        with c2:
            if safe_col(df, "MAIN_FUEL"):
                st.plotly_chart(average_score_chart(df, "MAIN_FUEL", "Mean Rating Score by Main Fuel", top_n=12), width="stretch", key="diag_main_fuel")
        st.markdown("<div class='insight'>Diagnostic interpretation: <b>heating efficiency, hot water efficiency, insulation quality, built form, fuel type and property age</b> show meaningful links with EPC outcomes.</div>", unsafe_allow_html=True)
        st.write("")
        for left_col, right_col, left_title, right_title in [
            ("WALLS_ENERGY_EFF", "ROOF_ENERGY_EFF", "Mean Score by Wall Efficiency", "Mean Score by Roof Efficiency"),
            ("WINDOWS_ENERGY_EFF", "MAINHEAT_ENERGY_EFF", "Mean Score by Window Efficiency", "Mean Score by Main Heating Efficiency"),
        ]:
            c1, c2 = st.columns(2)
            with c1:
                if safe_col(df, left_col):
                    st.plotly_chart(average_score_chart(df, left_col, left_title), width="stretch", key=f"diag_{left_col}")
            with c2:
                if safe_col(df, right_col):
                    st.plotly_chart(average_score_chart(df, right_col, right_title), width="stretch", key=f"diag_{right_col}")
        if safe_col(df, "PROPERTY_TYPE"):
            st.plotly_chart(stacked_rating_chart(df, "PROPERTY_TYPE", "EPC Rating Distribution by Property Type (%)"), width="stretch", key="diag_stacked_property")

    with tabs[3]:
        html_section("Predictive analytics", "Model performance", "Five classifiers were compared using accuracy, Macro F1 and weighted F1 to reflect both overall and balanced class performance.")
        if model_df is None:
            st.error("model_results.csv was not found.")
        else:
            st.plotly_chart(model_comparison_chart(model_df), width="stretch", key="model_comparison_chart")
            best_acc_row = model_df.loc[model_df["Accuracy"].idxmax()]
            best_f1_row = model_df.loc[model_df["Macro F1"].idxmax()]
            baseline = model_df[model_df["Model"].astype(str).str.contains("Dummy", case=False, na=False)]
            c1, c2, c3 = st.columns(3)
            c1.metric("Highest accuracy", f"{best_acc_row['Accuracy']:.1%}", best_acc_row["Model"])
            c2.metric("Best Macro F1", f"{best_f1_row['Macro F1']:.3f}", best_f1_row["Model"])
            if not baseline.empty:
                c3.metric("Dummy baseline accuracy", f"{baseline.iloc[0]['Accuracy']:.1%}")
            st.markdown("<div class='insight'><b>HistGradientBoosting</b> achieved the highest accuracy, while <b>Logistic Regression</b> achieved the best Macro F1. Macro F1 is important because EPC classes are imbalanced, especially for A, F and G.</div>", unsafe_allow_html=True)
            st.write("")
            cols = st.columns(min(5, len(model_df)))
            for i, (_, row) in enumerate(model_df.iterrows()):
                with cols[i % len(cols)]:
                    st.metric(row["Model"], f"{row['Accuracy']:.3f}", f"Macro F1 {row['Macro F1']:.3f}")
            c1, c2 = st.columns(2)
            with c1:
                show_image("fig17", "Notebook output: model comparison")
            with c2:
                show_image("fig18", "Notebook output: confusion matrix")

    with tabs[4]:
        html_section("Interpretability", "Feature importance", "Permutation importance measures how much Macro F1 decreases when a feature is shuffled. Larger drops indicate stronger predictive influence.")
        if perm_df is None:
            st.error("permutation_feature_importance.csv was not found.")
        else:
            top_n = st.slider("Top features to display", min_value=10, max_value=30, value=20, step=1)
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(feature_importance_chart(perm_df, n=top_n), width="stretch", key="perm_importance_chart")
            with c2:
                st.plotly_chart(grouped_importance_chart(perm_df, n=top_n), width="stretch", key="grouped_importance_chart")
            st.markdown("<div class='insight'>The strongest factors include <b>hot water efficiency, low-efficiency heating, insulation quality, main heating efficiency, built form, roof efficiency, fuel type and number of rooms</b>.</div>", unsafe_allow_html=True)
            st.write("")
            with st.expander("Top permutation importance values"):
                for _, row in perm_df.head(top_n).iterrows():
                    std_text = f" ± {row['Perm_Std']:.4f}" if "Perm_Std" in perm_df.columns else ""
                    st.write(f"**{row['Feature']}** — `{row['Perm_Mean']:.4f}{std_text}`")
            c1, c2 = st.columns(2)
            with c1:
                show_image("fig19", "Notebook output: permutation importance")
            with c2:
                show_image("fig20", "Notebook output: grouped permutation importance")
        with st.expander("Supplementary Random Forest MDI importance"):
            if rf_df is not None:
                st.plotly_chart(rf_importance_chart(rf_df, n=20), width="stretch", key="rf_mdi_importance_chart")
                show_image("fig21", "Notebook output: Random Forest MDI importance")
                st.caption("MDI is used only as a supplementary cross-check because it can favour high-cardinality features.")
            else:
                st.warning("random_forest_feature_importance.csv was not found.")

    with tabs[5]:
        html_section("Decision support", "Evidence-based recommendations", "The recommendations translate model interpretation and diagnostic findings into practical energy-efficiency priorities.")
        recommendations = [
            ("🔥", "Prioritise heating and hot water efficiency", "Hot water energy efficiency and low-efficiency heating were among the strongest predictors. Upgrading inefficient heating and hot water systems should be a priority intervention."),
            ("🧱", "Target insulation upgrades", "Insulation quality, wall efficiency, roof efficiency and floor-related features were influential. Retrofit programmes should prioritise fabric improvements before or alongside system upgrades."),
            ("🏘️", "Focus on older and detached properties", "Built form and construction age influence rating differences. Detached and older properties are useful candidates for targeted support because they often have greater heat-loss risk."),
            ("📊", "Use prediction to support targeting", "The trained model can help identify property profiles likely to fall into lower EPC bands. This could support future prioritisation, subject to governance and validation."),
            ("📋", "Improve EPC data quality", "Unknown or missing fields reduce certainty. Better completeness in future EPC records would improve analysis, interpretation and predictive modelling."),
            ("🌿", "Prioritise high-impact retrofit packages", "The strongest predictors point toward combined heating, hot water and insulation interventions rather than isolated cosmetic changes."),
        ]
        for row_start in range(0, len(recommendations), 3):
            cols = st.columns(3)
            for col, (icon, title, body) in zip(cols, recommendations[row_start:row_start + 3]):
                with col:
                    st.markdown(f"<div class='reco'><div class='reco-icon'>{icon}</div><div class='reco-title'>{title}</div><div class='reco-body'>{body}</div></div>", unsafe_allow_html=True)
            st.write("")
        st.warning("Limitations: EPC ratings estimate standardised energy performance rather than actual household consumption. Class imbalance, assessor variation, missing values and local-authority specificity should be considered when interpreting results.")

    with tabs[6]:
        html_section("Quality check", "Input file check", "All dashboard files should be in the same folder as app.py.")
        found_count = sum(1 for path in FILES.values() if path.exists())
        st.metric("Files found", f"{found_count}/{len(FILES)}")
        for key, path in FILES.items():
            status = "✅ Found" if path.exists() else "❌ Missing"
            size = f"{path.stat().st_size / 1024:.1f} KB" if path.exists() else "—"
            st.write(f"{status} — `{path.name}` — {size}")

    st.markdown("<div class='footer'>COM6003 Data Science Coursework · Buckinghamshire EPC Analysis · Dashboard demo built from notebook outputs</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
