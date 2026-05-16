"""
COM6003 — Buckinghamshire EPC Energy Performance Dashboard
Premium white UI version for Streamlit Cloud.

Uses the processed notebook outputs in the same folder as app.py.
No st.dataframe is used, so the app remains stable in hosted environments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

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
    "A": "#00a36c", "B": "#43bf6b", "C": "#a7d96d",
    "D": "#f8dd22", "E": "#ff9f1c", "F": "#f25f3a", "G": "#d7263d",
}

BLUE = "#2563eb"
PINK = "#ec4899"
PURPLE = "#7c3aed"
TEAL = "#0d9488"
GREEN = "#16a34a"
AMBER = "#f59e0b"
SLATE = "#0f172a"
MUTED = "#64748b"
BG = "#f8fbff"
CARD = "#ffffff"
BORDER = "#e2e8f0"

# -----------------------------------------------------------------------------
# CSS: white premium theme, no large HTML layout blocks that can leak as text
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  --bg: #f8fbff;
  --card: #ffffff;
  --ink: #0f172a;
  --muted: #64748b;
  --border: #e2e8f0;
  --blue: #2563eb;
  --pink: #ec4899;
  --purple: #7c3aed;
  --teal: #0d9488;
  --shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
  --shadow-soft: 0 10px 28px rgba(15, 23, 42, 0.06);
}

html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 10% 0%, rgba(37, 99, 235, .09), transparent 28%),
    radial-gradient(circle at 92% 4%, rgba(236, 72, 153, .10), transparent 26%),
    radial-gradient(circle at 50% 100%, rgba(13, 148, 136, .08), transparent 30%),
    var(--bg) !important;
  color: var(--ink) !important;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.block-container {
  max-width: 1420px !important;
  padding-top: 1.4rem !important;
  padding-bottom: 2.5rem !important;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff 0%, #f1f7ff 100%) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }
[data-testid="stSidebar"] [data-testid="stMetric"] {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  box-shadow: 0 8px 26px rgba(15, 23, 42, .05) !important;
}

h1, h2, h3 { color: var(--ink) !important; letter-spacing: -0.035em; }
p, li, label, span, div { font-family: Inter, system-ui, sans-serif; }

[data-testid="stTabs"] [role="tablist"] {
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: .35rem;
  box-shadow: var(--shadow-soft);
  gap: .2rem;
}
[data-testid="stTabs"] button[role="tab"] {
  border-radius: 999px !important;
  color: #475569 !important;
  font-weight: 700 !important;
  padding: .65rem 1rem !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  color: white !important;
  background: linear-gradient(135deg, var(--blue), var(--pink)) !important;
}

.hero-box {
  border-radius: 32px;
  padding: 3.2rem 3.4rem;
  margin: .2rem 0 1.2rem;
  background:
    radial-gradient(circle at 85% 10%, rgba(236,72,153,.30), transparent 28%),
    radial-gradient(circle at 5% 10%, rgba(37,99,235,.30), transparent 30%),
    linear-gradient(135deg, #ffffff 0%, #eef6ff 48%, #fff0f8 100%);
  border: 1px solid rgba(148, 163, 184, .25);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.hero-pill {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  padding: .45rem .85rem;
  border-radius: 999px;
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .13em;
  font-weight: 900;
  color: #1d4ed8;
  background: rgba(37,99,235,.08);
  border: 1px solid rgba(37,99,235,.18);
}
.hero-title {
  margin: 1rem 0 .8rem;
  font-size: clamp(2.25rem, 5vw, 4.75rem);
  line-height: .98;
  font-weight: 950;
  color: #0f172a;
}
.hero-gradient {
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 45%, #ec4899 100%);
  -webkit-background-clip: text;
  color: transparent;
}
.hero-copy {
  max-width: 850px;
  color: #475569;
  font-size: 1.1rem;
  line-height: 1.75;
}
.chip-row { display:flex; flex-wrap:wrap; gap:.65rem; margin-top:1.35rem; }
.chip {
  display:inline-flex; align-items:center; gap:.45rem;
  padding:.5rem .78rem; border-radius:999px;
  background: rgba(255,255,255,.78); border: 1px solid rgba(148,163,184,.22);
  color:#1e293b; font-weight:800; font-size:.86rem;
  box-shadow: 0 8px 24px rgba(15,23,42,.05);
}

[data-testid="stMetric"] {
  background: rgba(255,255,255,.92);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 1.1rem 1.2rem;
  box-shadow: var(--shadow-soft);
}
[data-testid="stMetricLabel"] { color: #64748b !important; font-weight: 700 !important; }
[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 900 !important; }
[data-testid="stMetricDelta"] { color: #16a34a !important; }

.info-card {
  background: rgba(255,255,255,.94);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 1.25rem 1.35rem;
  box-shadow: var(--shadow-soft);
  margin-bottom: 1rem;
}
.insight {
  background: linear-gradient(135deg, rgba(37,99,235,.08), rgba(236,72,153,.08));
  border-left: 4px solid var(--blue);
  border-radius: 0 18px 18px 0;
  padding: 1rem 1.15rem;
  color: #334155;
  line-height: 1.65;
  margin: .8rem 0 1rem;
}
.insight b { color: #0f172a; }
.success-note {
  background: linear-gradient(135deg, rgba(22,163,74,.10), rgba(13,148,136,.08));
  border: 1px solid rgba(22,163,74,.16);
  border-radius: 18px;
  padding: .95rem 1.05rem;
  color: #166534;
  line-height: 1.6;
}
.reco-box {
  min-height: 230px;
  background: #ffffff;
  border: 1px solid var(--border);
  border-top: 4px solid var(--blue);
  border-radius: 24px;
  padding: 1.25rem 1.35rem;
  box-shadow: var(--shadow-soft);
}
.reco-icon { font-size: 1.8rem; margin-bottom: .55rem; }
.reco-title { color:#0f172a; font-weight:900; font-size:1.03rem; margin-bottom:.45rem; }
.reco-body { color:#475569; line-height:1.65; font-size:.94rem; }
.footer {
  text-align:center; margin-top:2rem; color:#64748b; border-top:1px solid var(--border); padding-top:1rem;
  font-size:.86rem;
}
.stAlert { border-radius: 18px !important; }
hr { border-color: var(--border) !important; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Loaders
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
    return df


@st.cache_data(show_spinner=False)
def load_image(path: Path) -> Optional[Image.Image]:
    if not path.exists():
        return None
    return Image.open(path)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def safe_col(df: Optional[pd.DataFrame], col: str) -> bool:
    return df is not None and col in df.columns


def clean_categories(values) -> list[str]:
    bad = {"Unknown", "Not Recorded", "NO DATA!", "INVALID!", "nan", "None", "N/A"}
    return [str(v) for v in values if str(v) not in bad]


def show_section(eyebrow: str, title: str, copy: str = "") -> None:
    st.caption(eyebrow.upper())
    st.subheader(title)
    if copy:
        st.write(copy)


def show_image(key: str, caption: str) -> None:
    img = load_image(FILES[key])
    if img is None:
        st.warning(f"Missing image: {FILES[key].name}")
    else:
        st.image(img, caption=caption, width="stretch")


def style_fig(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=72, b=45),
        font=dict(size=13, color=SLATE),
        title_font=dict(size=20, color=SLATE, family="Inter"),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.92)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#e2e8f0", zerolinecolor="#cbd5e1", linecolor="#cbd5e1"),
        yaxis=dict(gridcolor="#e2e8f0", zerolinecolor="#cbd5e1", linecolor="#cbd5e1"),
    )
    return fig

# -----------------------------------------------------------------------------
# Charts
# -----------------------------------------------------------------------------
def rating_distribution_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["CURRENT_ENERGY_RATING"].value_counts().reindex(RATING_ORDER).fillna(0).astype(int)
    total = counts.sum()
    fig = go.Figure(
        data=[go.Bar(
            x=counts.index,
            y=counts.values,
            text=[f"{v:,}<br>{(v / total * 100):.1f}%" if total else "0" for v in counts],
            textposition="outside",
            marker_color=[RATING_COLORS.get(r, "#64748b") for r in counts.index],
            marker_line=dict(color="rgba(15,23,42,.15)", width=1),
            hovertemplate="Rating %{x}<br>%{y:,} certificates<extra></extra>",
        )]
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
        color_continuous_scale=["#dbeafe", "#60a5fa", "#2563eb"],
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
        color_continuous_scale=["#fce7f3", "#bfdbfe", "#2563eb"],
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
            fig.add_bar(x=pct.index.astype(str), y=pct[rating], name=rating, marker_color=RATING_COLORS.get(rating, "#64748b"))
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
        color_discrete_sequence=[BLUE, TEAL, PINK],
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
        color_continuous_scale=["#dbeafe", "#93c5fd", "#2563eb"],
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
        color_continuous_scale=["#fce7f3", "#f472b6", "#7c3aed"],
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
        color_continuous_scale=["#fff7ed", "#fb923c", "#ec4899"],
    )
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(520, 28 * n + 140))

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
def sidebar_summary(df: Optional[pd.DataFrame]) -> None:
    st.sidebar.title("⚡ EPC Dashboard")
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
        <div class='hero-box'>
          <div class='hero-pill'>⚡ COM6003 · DATA SCIENCE · BUCKINGHAMSHIRE</div>
          <div class='hero-title'>Domestic EPC<br><span class='hero-gradient'>Energy Intelligence Dashboard</span></div>
          <div class='hero-copy'>A polished evidence dashboard for analysing domestic Energy Performance Certificates in Buckinghamshire, exploring stock characteristics, diagnostic drivers, model performance, feature importance and retrofit priorities.</div>
          <div class='chip-row'>
            <span class='chip'>🏠 Domestic EPCs</span>
            <span class='chip'>🧠 Predictive analytics</span>
            <span class='chip'>📊 Feature importance</span>
            <span class='chip'>🌿 Energy efficiency</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None:
        st.error("The cleaned EPC dataset was not found. Make sure all files are in the same folder as app.py.")
        for _, path in FILES.items():
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

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total records", f"{total:,}", "Buckinghamshire domestic EPCs")
    k2.metric("Dominant rating", str(common_rating), "Most common EPC band")
    k3.metric("C/D rated", f"{cd_pct:.1f}%", "Mid-efficiency share")
    k4.metric("Best accuracy", f"{best_accuracy:.1%}" if pd.notna(best_accuracy) else "N/A", str(best_acc_model))
    k5.metric("Best Macro F1", f"{best_macro:.3f}" if pd.notna(best_macro) else "N/A", str(best_f1_model))

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
        show_section("Executive view", "Energy performance profile", "The dashboard summarises Buckinghamshire's domestic EPC stock and the predictive modelling outputs used for the coursework analysis.")
        left, right = st.columns([2.15, 1])
        with left:
            st.plotly_chart(rating_distribution_chart(df), width="stretch", key="overview_rating_distribution")
        with right:
            st.markdown(
                f"<div class='insight'>Most domestic EPCs are concentrated in <b>bands C and D</b>, which together account for <b>{cd_pct:.1f}%</b> of certificates. The extreme bands A and G are rare, making balanced classification more difficult.</div>",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            c1.metric("Average floor area", f"{df['TOTAL_FLOOR_AREA'].mean():.0f} m²" if safe_col(df, "TOTAL_FLOOR_AREA") else "N/A")
            c2.metric("A-C rated", f"{ac_pct:.1f}%")
            c3, c4 = st.columns(2)
            c3.metric("Property types", f"{df['PROPERTY_TYPE'].nunique() if safe_col(df, 'PROPERTY_TYPE') else 0}")
            c4.metric("Built forms", f"{df['BUILT_FORM'].nunique() if safe_col(df, 'BUILT_FORM') else 0}")
        with st.expander("Notebook-generated static EPC distribution figure"):
            show_image("fig01", "Notebook output: EPC rating distribution")

    with tabs[1]:
        show_section("Exploratory analysis", "Building energy insights", "Interactive charts reveal how rating patterns differ by property type, built form, age and total floor area.")
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
        show_section("Diagnostic analytics", "Why ratings differ", "The diagnostic layer links lower or higher EPC performance to physical building characteristics such as insulation, fuel, heating efficiency and built form.")
        c1, c2 = st.columns(2)
        with c1:
            if safe_col(df, "BUILT_FORM"):
                st.plotly_chart(average_score_chart(df, "BUILT_FORM", "Mean Rating Score by Built Form"), width="stretch", key="diag_built_form")
        with c2:
            if safe_col(df, "MAIN_FUEL"):
                st.plotly_chart(average_score_chart(df, "MAIN_FUEL", "Mean Rating Score by Main Fuel", top_n=12), width="stretch", key="diag_main_fuel")
        st.markdown("<div class='insight'>Diagnostic interpretation: <b>heating efficiency, hot water efficiency, insulation quality, built form, fuel type and property age</b> show meaningful links with EPC outcomes.</div>", unsafe_allow_html=True)
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
        show_section("Predictive analytics", "Model performance", "Five classifiers were compared using accuracy, Macro F1 and weighted F1 to reflect both overall and balanced class performance.")
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
            c1, c2 = st.columns(2)
            with c1:
                show_image("fig17", "Notebook output: model comparison")
            with c2:
                show_image("fig18", "Notebook output: confusion matrix")

    with tabs[4]:
        show_section("Interpretability", "Feature importance", "Permutation importance measures how much Macro F1 decreases when a feature is shuffled. Larger drops indicate stronger predictive influence.")
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
        show_section("Decision support", "Evidence-based recommendations", "The recommendations translate model interpretation and diagnostic findings into practical energy-efficiency priorities.")
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
                    st.markdown(f"<div class='reco-box'><div class='reco-icon'>{icon}</div><div class='reco-title'>{title}</div><div class='reco-body'>{body}</div></div>", unsafe_allow_html=True)
            st.write("")
        st.warning("Limitations: EPC ratings estimate standardised energy performance rather than actual household consumption. Class imbalance, assessor variation, missing values and local-authority specificity should be considered when interpreting results.")

    with tabs[6]:
        show_section("Quality check", "Input file check", "All dashboard files should be in the same folder as app.py.")
        found_count = sum(1 for path in FILES.values() if path.exists())
        st.metric("Files found", f"{found_count}/{len(FILES)}")
        for _, path in FILES.items():
            status = "✅ Found" if path.exists() else "❌ Missing"
            size = f"{path.stat().st_size / 1024:.1f} KB" if path.exists() else "—"
            st.write(f"{status} — `{path.name}` — {size}")

    st.markdown("<div class='footer'>COM6003 Data Science Coursework · Buckinghamshire EPC Analysis · Dashboard demo built from notebook outputs</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
