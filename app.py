"""
COM6003 — Buckinghamshire EPC Energy Performance Dashboard
Professional Streamlit dashboard for a bachelor's Data Science assignment.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Buckinghamshire EPC Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# FILE PATHS
# ============================================================

BASE = Path(__file__).parent

FILES = {
    "epc": BASE / "cleaned_buckinghamshire_epc.csv",
    "models": BASE / "model_results.csv",
    "perm": BASE / "permutation_feature_importance.csv",
    "rf_mdi": BASE / "random_forest_feature_importance.csv",
    "fig01": BASE / "fig01_rating_distribution.png",
    "fig17": BASE / "fig17_model_comparison.png",
    "fig18": BASE / "fig18_confusion_matrix.png",
    "fig18b": BASE / "fig18b_classification_report_heatmap.png",
    "fig19": BASE / "fig19_permutation_importance.png",
    "fig20": BASE / "fig20_grouped_permutation_importance.png",
    "fig21": BASE / "fig21_rf_mdi_importance.png",
}


# ============================================================
# CONSTANTS
# ============================================================

RATING_ORDER = ["A", "B", "C", "D", "E", "F", "G"]

RATING_COLORS = {
    "A": "#16A34A",
    "B": "#22C55E",
    "C": "#A3E635",
    "D": "#FACC15",
    "E": "#FB923C",
    "F": "#EF4444",
    "G": "#B91C1C",
}

RATING_SCORE_MAP = {
    "A": 7,
    "B": 6,
    "C": 5,
    "D": 4,
    "E": 3,
    "F": 2,
    "G": 1,
}

BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
BLUE_SOFT = "#EFF6FF"
BLACK = "#0F172A"
GRAY = "#64748B"
BORDER = "#E2E8F0"
BG = "#F8FAFC"


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --blue: #2563EB;
    --blue-dark: #1D4ED8;
    --navy: #0F172A;
    --slate: #475569;
    --muted: #64748B;
    --border: #E2E8F0;
    --soft: #EFF6FF;
    --bg: #F8FAFC;
    --card: #FFFFFF;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer, header {
    visibility: hidden;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 8% 8%, rgba(37,99,235,0.08), transparent 28%),
        radial-gradient(circle at 92% 0%, rgba(15,23,42,0.045), transparent 26%),
        linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%) !important;
}

.block-container {
    padding-top: 1.4rem !important;
    padding-left: 2.4rem !important;
    padding-right: 2.4rem !important;
    max-width: 1560px !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 8px 0 28px rgba(15,23,42,0.045);
}

[data-testid="stSidebar"] * {
    color: var(--navy) !important;
}

[data-testid="stSidebar"] [data-testid="stMetric"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%) !important;
    border: 1px solid var(--border) !important;
    border-left: 4px solid var(--blue) !important;
    border-radius: 18px !important;
    padding: 0.95rem 1rem !important;
    box-shadow: 0 10px 24px rgba(15,23,42,0.055) !important;
    margin-bottom: 0.7rem !important;
}

[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: var(--navy) !important;
    font-weight: 900 !important;
    letter-spacing: -0.04em !important;
}

[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: var(--soft) !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 18px !important;
    color: #1E3A8A !important;
}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    min-height: 380px;
    border-radius: 30px;
    padding: 3.3rem 32rem 3.3rem 3.4rem;
    margin-bottom: 1.45rem;
    background:
        radial-gradient(circle at 12% 16%, rgba(37,99,235,0.14), transparent 32%),
        radial-gradient(circle at 88% 14%, rgba(37,99,235,0.10), transparent 30%),
        linear-gradient(135deg, #FFFFFF 0%, #F8FBFF 48%, #EAF3FF 100%);
    border: 1px solid rgba(148,163,184,0.25);
    box-shadow: 0 30px 85px rgba(15,23,42,0.11);
}

.hero::before {
    content: "";
    position: absolute;
    right: 5rem;
    top: 3rem;
    width: 285px;
    height: 285px;
    border-radius: 50%;
    background: conic-gradient(from 220deg, #2563EB, #1D4ED8, #0F172A, #60A5FA, #2563EB);
    box-shadow: 0 30px 75px rgba(37,99,235,0.23);
}

.hero::after {
    content: "85,011\\A EPC records";
    white-space: pre;
    position: absolute;
    right: 8.45rem;
    top: 6.35rem;
    width: 175px;
    height: 175px;
    border-radius: 50%;
    background: rgba(255,255,255,0.98);
    border: 1px solid #DBEAFE;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: var(--navy);
    font-size: 1.35rem;
    line-height: 1.32;
    font-weight: 900;
    letter-spacing: -0.04em;
}

.hero-pill {
    display: inline-block;
    padding: .5rem .9rem;
    border-radius: 999px;
    background: var(--soft);
    border: 1px solid #BFDBFE;
    color: var(--blue-dark);
    font-size: .72rem;
    font-weight: 900;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin-bottom: 1.1rem;
}

.hero-title {
    font-size: clamp(3rem, 5vw, 5.25rem);
    line-height: .95;
    font-weight: 900;
    letter-spacing: -0.075em;
    color: var(--navy);
    margin: 0;
}

.gradient-text {
    background: linear-gradient(90deg, #1D4ED8, #2563EB, #60A5FA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 1.2rem;
    max-width: 780px;
    color: #334155;
    line-height: 1.75;
    font-size: 1.05rem;
}

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: .65rem;
    margin-top: 1.25rem;
}

.chip {
    display: inline-block;
    padding: .5rem .85rem;
    border-radius: 999px;
    background: #FFFFFF;
    border: 1px solid #BFDBFE;
    color: #1E3A8A;
    font-size: .78rem;
    font-weight: 800;
    box-shadow: 0 8px 18px rgba(37,99,235,0.06);
}

/* KPI cards */
.metric-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
    border: 1px solid var(--border);
    border-left: 5px solid var(--blue);
    border-radius: 22px;
    padding: 1.2rem 1.25rem;
    min-height: 124px;
    box-shadow: 0 16px 38px rgba(15,23,42,0.075);
    transition: transform .18s ease, box-shadow .18s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 22px 48px rgba(15,23,42,0.11);
}

.metric-label {
    color: var(--muted);
    font-size: .73rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: .11em;
}

.metric-value {
    margin-top: .55rem;
    color: var(--navy);
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -0.055em;
}

.metric-sub {
    margin-top: .42rem;
    display: inline-block;
    padding: .28rem .6rem;
    border-radius: 999px;
    background: var(--soft);
    border: 1px solid #BFDBFE;
    color: var(--blue-dark);
    font-size: .72rem;
    font-weight: 800;
}

/* Tabs */
div[data-testid="stTabs"] {
    background: rgba(255,255,255,.9);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: .25rem .45rem .18rem;
    box-shadow: 0 14px 34px rgba(15,23,42,0.06);
}

div[data-testid="stTabs"] button {
    font-weight: 800 !important;
    color: #334155 !important;
    padding: .65rem .9rem !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--blue) !important;
    background: var(--soft) !important;
    border-radius: 14px !important;
}

/* Section headings */
.section-kicker {
    color: var(--blue);
    font-weight: 900;
    letter-spacing: .14em;
    text-transform: uppercase;
    font-size: .72rem;
    margin-top: .35rem;
    margin-bottom: .35rem;
}

.section-title {
    color: var(--navy);
    font-size: 2.05rem;
    font-weight: 900;
    letter-spacing: -0.045em;
    margin-bottom: .2rem;
}

.section-subtitle {
    color: var(--muted);
    font-size: 1rem;
    margin-bottom: 1.15rem;
}

/* Cards and visual containers */
.insight,
.success-box,
.warn-box,
.rec-card,
[data-testid="stPlotlyChart"],
[data-testid="stImage"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    box-shadow: 0 16px 38px rgba(15,23,42,0.06) !important;
}

.insight {
    border-left: 5px solid var(--blue) !important;
    padding: 1.05rem 1.15rem;
    color: #334155;
    line-height: 1.68;
}

.success-box {
    border-left: 5px solid var(--blue) !important;
    padding: 1.05rem 1.15rem;
    color: #1E3A8A;
    line-height: 1.68;
}

.warn-box {
    border-left: 5px solid #F97316 !important;
    padding: 1.05rem 1.15rem;
    color: #9A3412;
    line-height: 1.68;
}

.rec-card {
    border-left: 5px solid var(--blue) !important;
    padding: 1.15rem 1.25rem;
    margin-bottom: 1rem;
}

.rec-title {
    color: var(--navy);
    font-size: 1.08rem;
    font-weight: 900;
    margin-bottom: .35rem;
}

.rec-body {
    color: var(--slate);
    line-height: 1.68;
    font-size: .95rem;
}

.rec-tag {
    margin-top: .75rem;
    display: inline-block;
    padding: .35rem .7rem;
    border-radius: 999px;
    background: var(--soft);
    border: 1px solid #BFDBFE;
    color: var(--blue-dark);
    font-size: .74rem;
    font-weight: 900;
}

[data-testid="stPlotlyChart"] {
    padding: .85rem 1rem .35rem !important;
}

[data-testid="stImage"] {
    padding: .7rem !important;
}

[data-testid="stImageCaption"] {
    color: #334155 !important;
    font-weight: 700 !important;
    text-align: center !important;
}

[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #DBEAFE !important;
    border-left: 4px solid var(--blue) !important;
    border-radius: 18px !important;
    padding: .9rem 1rem !important;
    box-shadow: 0 10px 26px rgba(15,23,42,0.05) !important;
}

[data-testid="stMetricValue"] {
    color: var(--navy) !important;
    font-weight: 900 !important;
    letter-spacing: -0.04em !important;
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-weight: 700 !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #334155;
    line-height: 1.7;
}

h1, h2, h3 {
    color: var(--navy) !important;
}

.file-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: .8rem .9rem;
    border-bottom: 1px solid var(--border);
    color: #334155;
    font-size: .92rem;
    background: #ffffff;
}

.file-ok {
    color: #16a34a;
    font-weight: 900;
}

.file-miss {
    color: #dc2626;
    font-weight: 900;
}

@media (max-width: 1050px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .hero {
        padding: 2.2rem 1.5rem !important;
        min-height: auto !important;
    }

    .hero::before,
    .hero::after {
        display: none !important;
    }

    .hero-title {
        font-size: 2.65rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(show_spinner=False)
def load_csv(path: Path):
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False)


@st.cache_data(show_spinner=False)
def load_epc():
    df = load_csv(FILES["epc"])
    if df is None:
        return None

    if "RATING_SCORE" not in df.columns and "CURRENT_ENERGY_RATING" in df.columns:
        df["RATING_SCORE"] = df["CURRENT_ENERGY_RATING"].map(RATING_SCORE_MAP)

    if "TOTAL_FLOOR_AREA" in df.columns:
        df["TOTAL_FLOOR_AREA"] = pd.to_numeric(df["TOTAL_FLOOR_AREA"], errors="coerce")

    return df


def load_img(key):
    p = FILES.get(key)
    if p and p.exists():
        return Image.open(p)
    return None


# ============================================================
# HELPERS
# ============================================================

def metric_card(label, value, sub=""):
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
    <div class="metric-sub">{sub}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def section(kicker, title, subtitle=""):
    st.markdown(f"<div class='section-kicker'>{kicker}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def insight_box(text):
    st.markdown(f"<div class='insight'>{text}</div>", unsafe_allow_html=True)


def success_box(text):
    st.markdown(f"<div class='success-box'>{text}</div>", unsafe_allow_html=True)


def warn_box(text):
    st.markdown(f"<div class='warn-box'>{text}</div>", unsafe_allow_html=True)


def rec_card(title, body, tag):
    st.markdown(
        f"""
<div class="rec-card">
    <div class="rec-title">{title}</div>
    <div class="rec-body">{body}</div>
    <div class="rec-tag">{tag}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_file_row(name, path):
    exists = path.exists()
    size = f"{path.stat().st_size / 1024 / 1024:.2f} MB" if exists else "Missing"
    status = "Available" if exists else "Missing"
    cls = "file-ok" if exists else "file-miss"

    st.markdown(
        f"""
<div class="file-row">
    <div><strong>{name}</strong></div>
    <div>{size}</div>
    <div class="{cls}">{status}</div>
</div>
""",
        unsafe_allow_html=True,
    )



# ============================================================
# LABEL CLEANING HELPERS
# ============================================================

def clean_label(value, max_len=42):
    """Shorten long EPC category labels for dashboard readability."""
    value = str(value)
    replacements = {
        " - this is for backwards compatibility only and should not be used": "",
        "mains gas (not community)": "Mains gas",
        "Gas: mains gas": "Mains gas",
        "Electricity: electricity, unspecified tariff": "Electricity, unspecified tariff",
        "Solid fuel: wood logs": "Wood logs",
        "appliances able to use mineral oil or liquid biofuel": "Mineral oil / biofuel",
        "solid, no insulation (assumed)": "Solid, no insulation",
        "suspended, no insulation (assumed)": "Suspended, no insulation",
        "Boiler and radiators, mains gas": "Boiler + radiators, mains gas",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = value.strip()
    if len(value) > max_len:
        return value[:max_len - 1].rstrip() + "…"
    return value


# ============================================================
# PLOTLY THEME
# ============================================================

def theme_fig(fig, title=None, height=560):
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter", color="#1f2937", size=14),
        margin=dict(l=190, r=70, t=82 if title else 52, b=78),
        title=dict(
            text=title,
            font=dict(size=22, color="#0f172a", family="Inter"),
            x=0.01,
            xanchor="left",
        ) if title else None,
        xaxis=dict(
            gridcolor="#e5e7eb",
            zerolinecolor="#e5e7eb",
            title_font=dict(color="#334155", size=15),
            tickfont=dict(color="#334155", size=13),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor="#f1f5f9",
            zerolinecolor="#e5e7eb",
            title_font=dict(color="#334155", size=15),
            tickfont=dict(color="#334155", size=13),
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=13, color="#334155"),
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=13,
            font_family="Inter",
            font_color="#ffffff",
        ),
    )
    return fig



# ============================================================
# CHARTS
# ============================================================

def chart_rating_distribution(df):
    counts = df["CURRENT_ENERGY_RATING"].value_counts().reindex(RATING_ORDER).fillna(0)
    total = counts.sum()

    fig = go.Figure(
        go.Bar(
            x=counts.index,
            y=counts.values,
            marker=dict(
                color=[RATING_COLORS[r] for r in counts.index],
                line=dict(color="rgba(255,255,255,.9)", width=1),
            ),
            text=[f"{int(v):,}<br>{v/total*100:.1f}%" for v in counts.values],
            textposition="outside",
            hovertemplate="<b>Rating %{x}</b><br>%{y:,} certificates<extra></extra>",
        )
    )

    fig = theme_fig(fig, "Distribution of Current EPC Ratings", 420)
    fig.update_layout(
        showlegend=False,
        xaxis_title="Current energy rating",
        yaxis_title="Number of certificates",
        bargap=0.25,
    )
    return fig


def chart_property_type(df):
    counts = df["PROPERTY_TYPE"].value_counts().sort_values()

    fig = go.Figure(
        go.Bar(
            x=counts.values,
            y=[clean_label(v) for v in counts.index],
            orientation="h",
            marker=dict(color=BLUE),
            text=[f"{v:,}" for v in counts.values],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:,} certificates<extra></extra>",
        )
    )

    fig = theme_fig(fig, "Property Type Distribution", 360)
    fig.update_layout(showlegend=False, xaxis_title="Number of certificates", yaxis_title="")
    return fig


def chart_built_form(df):
    if "BUILT_FORM" not in df.columns:
        return go.Figure()

    counts = (
        df["BUILT_FORM"]
        .replace(["NO DATA!", "Not Recorded"], np.nan)
        .dropna()
        .value_counts()
        .sort_values()
    )

    fig = go.Figure(
        go.Bar(
            x=counts.values,
            y=[clean_label(v) for v in counts.index],
            orientation="h",
            marker=dict(color="#1E40AF"),
            text=[f"{v:,}" for v in counts.values],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:,} certificates<extra></extra>",
        )
    )

    fig = theme_fig(fig, "Built Form Distribution", 360)
    fig.update_layout(showlegend=False, xaxis_title="Number of certificates", yaxis_title="")
    return fig


def chart_average_score(df, column, title, top_n=None):
    if column not in df.columns or "RATING_SCORE" not in df.columns:
        return go.Figure()

    grp = df.groupby(column)["RATING_SCORE"].mean().dropna().sort_values(ascending=True)

    remove_values = ["Unknown", "NO DATA!", "Not Recorded", "N/A", "INVALID!"]
    grp = grp[~grp.index.astype(str).isin(remove_values)]

    if top_n:
        grp = grp.tail(top_n)

    colors = px.colors.sample_colorscale("Blues", np.linspace(0.35, 0.9, len(grp)))

    fig = go.Figure(
        go.Bar(
            x=grp.values,
            y=[clean_label(v) for v in grp.index.astype(str)],
            orientation="h",
            marker=dict(color=colors),
            text=[f"{v:.2f}" for v in grp.values],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Mean rating score: %{x:.2f}<extra></extra>",
        )
    )

    overall = df["RATING_SCORE"].mean()
    fig.add_vline(
        x=overall,
        line_dash="dash",
        line_width=2,
        line_color="#64748b",
        annotation_text=f"Mean {overall:.2f}",
        annotation_position="top right",
    )

    fig = theme_fig(fig, title, max(360, 42 * len(grp) + 100))
    fig.update_layout(
        showlegend=False,
        xaxis_title="Mean rating score, A=7 and G=1",
        yaxis_title="",
        xaxis=dict(range=[0, 7.5], gridcolor="#e5e7eb"),
    )
    return fig


def chart_floor_area_box(df):
    if "TOTAL_FLOOR_AREA" not in df.columns:
        return go.Figure()

    fig = go.Figure()

    for rating in RATING_ORDER:
        values = df.loc[df["CURRENT_ENERGY_RATING"] == rating, "TOTAL_FLOOR_AREA"].dropna()
        if len(values) == 0:
            continue

        fig.add_trace(
            go.Box(
                y=values,
                name=rating,
                marker_color=RATING_COLORS[rating],
                line_color=RATING_COLORS[rating],
                boxpoints=False,
                hovertemplate=f"<b>Rating {rating}</b><br>%{{y:.0f}} m²<extra></extra>",
            )
        )

    fig = theme_fig(fig, "Total Floor Area by EPC Rating", 420)
    fig.update_layout(
        showlegend=False,
        xaxis_title="Current energy rating",
        yaxis_title="Total floor area, m²",
    )
    return fig


def chart_model_comparison(model_df):
    fig = go.Figure()

    metrics = [
        ("Accuracy", BLUE),
        ("Macro F1", "#0F766E"),
        ("Weighted F1", "#1E40AF"),
    ]

    for metric, color in metrics:
        fig.add_trace(
            go.Bar(
                x=model_df["Model"],
                y=model_df[metric],
                name=metric,
                marker=dict(color=color),
                text=[f"{v:.3f}" for v in model_df[metric]],
                textposition="outside",
                hovertemplate=f"<b>%{{x}}</b><br>{metric}: %{{y:.4f}}<extra></extra>",
            )
        )

    fig = theme_fig(fig, "Model Performance Comparison", 450)
    fig.update_layout(
        barmode="group",
        yaxis=dict(range=[0, 1.05], gridcolor="#e5e7eb"),
        xaxis_title="",
        yaxis_title="Score",
    )
    return fig


def chart_perm_importance(perm_df, top_n=20):
    top = perm_df.head(top_n).copy()

    fig = go.Figure(
        go.Bar(
            x=top["Perm_Mean"],
            y=[clean_label(v, 52) for v in top["Feature"]],
            orientation="h",
            marker=dict(color=BLUE),
            error_x=dict(
                type="data",
                array=top["Perm_Std"] if "Perm_Std" in top.columns else None,
                color="#94a3b8",
                thickness=1.2,
            ),
            text=[f"{v:.3f}" for v in top["Perm_Mean"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Mean decrease: %{x:.4f}<extra></extra>",
        )
    )

    fig = theme_fig(fig, f"Top {top_n} Permutation Feature Importances", max(820, 46 * top_n + 190))
    fig.update_layout(
        showlegend=False,
        yaxis=dict(autorange="reversed", gridcolor="#ffffff"),
        xaxis_title="Mean decrease in Macro F1",
        yaxis_title="Feature",
    )
    return fig


def grouped_perm_importance(perm_df, top_n=20):
    known_features = [
        "HOT_WATER_ENERGY_EFF",
        "IS_LOW_EFFICIENCY_HEATING",
        "INSULATION_QUALITY_SCORE",
        "MAINHEAT_ENERGY_EFF",
        "FLOOR_DESCRIPTION",
        "BUILT_FORM",
        "ROOF_ENERGY_EFF",
        "WALLS_ENERGY_EFF",
        "MAINHEAT_DESCRIPTION",
        "MAIN_FUEL",
        "MECHANICAL_VENTILATION",
        "CONSTRUCTION_AGE_BAND",
        "ROOF_DESCRIPTION",
        "NUMBER_HEATED_ROOMS",
        "LIGHTING_DESCRIPTION",
        "NUMBER_HABITABLE_ROOMS",
        "WINDOWS_ENERGY_EFF",
        "FLOOR_AREA_BAND",
        "PROPERTY_AGE_GROUP",
        "TRANSACTION_TYPE",
        "TOTAL_FLOOR_AREA",
        "PROPERTY_TYPE",
        "TENURE",
        "WINDOWS_DESCRIPTION",
        "WALLS_DESCRIPTION",
        "HOTWATER_DESCRIPTION",
    ]

    def original_name(feature):
        for k in sorted(known_features, key=len, reverse=True):
            if str(feature).startswith(k):
                return k
        return feature

    tmp = perm_df.copy()
    tmp["Original_Feature"] = tmp["Feature"].apply(original_name)

    grp = (
        tmp.groupby("Original_Feature")["Perm_Mean"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .sort_values(ascending=True)
    )

    fig = go.Figure(
        go.Bar(
            x=grp.values,
            y=[clean_label(v, 52) for v in grp.index],
            orientation="h",
            marker=dict(color="#1E40AF"),
            text=[f"{v:.3f}" for v in grp.values],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Summed importance: %{x:.4f}<extra></extra>",
        )
    )

    fig = theme_fig(fig, f"Grouped Feature Importance, Top {top_n}", max(820, 46 * len(grp) + 190))
    fig.update_layout(
        showlegend=False,
        yaxis=dict(gridcolor="#ffffff"),
        xaxis_title="Summed permutation importance",
        yaxis_title="Original feature",
    )
    return fig


def chart_rf_importance(rf_df, top_n=20):
    top = rf_df.head(top_n).copy()

    fig = go.Figure(
        go.Bar(
            x=top["MDI_Importance"],
            y=[clean_label(v, 52) for v in top["Feature"]],
            orientation="h",
            marker=dict(color="#0F766E"),
            text=[f"{v:.3f}" for v in top["MDI_Importance"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>MDI: %{x:.4f}<extra></extra>",
        )
    )

    fig = theme_fig(fig, f"Random Forest MDI Importance, Top {top_n}", max(820, 46 * len(top) + 190))
    fig.update_layout(
        showlegend=False,
        yaxis=dict(autorange="reversed", gridcolor="#ffffff"),
        xaxis_title="Mean decrease in impurity",
        yaxis_title="Feature",
    )
    return fig


# ============================================================
# SIDEBAR
# ============================================================

def sidebar(df):
    with st.sidebar:
        st.markdown("### ⚡ Buckinghamshire EPC Dashboard")
        st.caption("COM6003 Data Science")
        st.divider()

        if df is not None:
            st.markdown("#### Dataset Summary")
            st.metric("Total certificates", f"{len(df):,}")
            st.metric("Property types", f"{df['PROPERTY_TYPE'].nunique()}")
            st.metric("EPC bands", f"{df['CURRENT_ENERGY_RATING'].nunique()}")

            st.divider()

            st.info(
                "Live dashboard mode is enabled. The full Buckinghamshire EPC dataset is loaded.",
                icon="✅",
            )

            st.caption(
                "For formal marking, the Jupyter notebook remains the primary reproducible evidence."
            )
        else:
            st.error("Dataset not loaded. Check the Files tab.")


# ============================================================
# MAIN APP
# ============================================================

def main():
    df = load_epc()
    model_df = load_csv(FILES["models"])
    perm_df = load_csv(FILES["perm"])
    rf_df = load_csv(FILES["rf_mdi"])

    sidebar(df)

    st.markdown(
        """
<div class="hero">
    <div class="hero-pill">⚡ COM6003 · Data Science · Buckinghamshire</div>
    <div class="hero-title">
        Domestic EPC<br>
        <span class="gradient-text">Energy Intelligence</span><br>
        Dashboard
    </div>
    <div class="hero-subtitle">
        A polished evidence dashboard for analysing domestic Energy Performance Certificates in
        Buckinghamshire, exploring stock characteristics, diagnostic drivers, model performance,
        feature importance and retrofit priorities.
    </div>
    <div class="chip-row">
        <span class="chip">🏠 Domestic EPCs</span>
        <span class="chip">📊 Descriptive analytics</span>
        <span class="chip">🧠 Predictive modelling</span>
        <span class="chip">⚙️ Feature importance</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if df is None:
        st.error("The main EPC dataset could not be loaded. Open the Files tab to check filenames.")
        return

    total_records = len(df)
    dominant_rating = df["CURRENT_ENERGY_RATING"].mode()[0]
    cd_pct = df["CURRENT_ENERGY_RATING"].isin(["C", "D"]).mean() * 100
    ac_pct = df["CURRENT_ENERGY_RATING"].isin(["A", "B", "C"]).mean() * 100

    if model_df is not None:
        best_acc = model_df["Accuracy"].max()
        best_acc_model = model_df.loc[model_df["Accuracy"].idxmax(), "Model"]
        best_f1 = model_df["Macro F1"].max()
        best_f1_model = model_df.loc[model_df["Macro F1"].idxmax(), "Model"]
    else:
        best_acc = 0
        best_acc_model = "Unavailable"
        best_f1 = 0
        best_f1_model = "Unavailable"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        metric_card("Total records", f"{total_records:,}", "Buckinghamshire domestic EPCs")
    with k2:
        metric_card("Dominant rating", dominant_rating, "Most common EPC band")
    with k3:
        metric_card("C/D rated", f"{cd_pct:.1f}%", "Mid-efficiency share")
    with k4:
        metric_card("Best accuracy", f"{best_acc:.1%}", best_acc_model)
    with k5:
        metric_card("Best Macro F1", f"{best_f1:.3f}", best_f1_model)

    tabs = st.tabs(
        [
            "Executive Overview",
            "Building Insights",
            "Diagnostic Analysis",
            "Model Performance",
            "Feature Importance",
            "Recommendations",
            "Files",
        ]
    )

    # TAB 1
    with tabs[0]:
        section(
            "Executive View",
            "Energy performance profile",
            "The dashboard summarises Buckinghamshire's domestic EPC stock and predictive modelling outputs.",
        )

        c1, c2 = st.columns([1.7, 1])

        with c1:
            st.plotly_chart(
                chart_rating_distribution(df),
                width="stretch",
                key="overview_rating_distribution",
                config={"displayModeBar": False},
            )

        with c2:
            insight_box(
                f"Most domestic EPCs are concentrated in <strong>bands C and D</strong>, "
                f"which together account for <strong>{cd_pct:.1f}%</strong> of certificates. "
                "The extreme bands A and G are much rarer, making balanced classification more difficult."
            )

            st.markdown("")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Average floor area", f"{df['TOTAL_FLOOR_AREA'].mean():.0f} m²")
                st.metric("Property types", df["PROPERTY_TYPE"].nunique())
            with m2:
                st.metric("A-C rated", f"{ac_pct:.1f}%")
                st.metric("Built forms", df["BUILT_FORM"].nunique())

        fig = load_img("fig01")
        if fig:
            with st.expander("Notebook output: EPC rating distribution"):
                st.image(fig, width="stretch")

    # TAB 2
    with tabs[1]:
        section(
            "Stock Characteristics",
            "Building insights",
            "Descriptive analytics showing what has occurred across the local EPC stock.",
        )

        st.plotly_chart(
            chart_property_type(df),
            width="stretch",
            key="building_property_type",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_built_form(df),
            width="stretch",
            key="building_built_form",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_average_score(df, "PROPERTY_TYPE", "Average Rating Score by Property Type"),
            width="stretch",
            key="building_avg_property",
            config={"displayModeBar": False},
        )

        age_col = "PROPERTY_AGE_GROUP" if "PROPERTY_AGE_GROUP" in df.columns else "CONSTRUCTION_AGE_BAND"
        st.plotly_chart(
            chart_average_score(df, age_col, "Average Rating Score by Construction Age"),
            width="stretch",
            key="building_avg_age",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_floor_area_box(df),
            width="stretch",
            key="building_floor_area_box",
            config={"displayModeBar": False},
        )

        insight_box(
            "The descriptive analysis shows that building form, property type and construction age are important contextual variables. "
            "These do not act alone, but they help explain why the EPC stock is concentrated around mid-efficiency bands."
        )

    # TAB 3
    with tabs[2]:
        section(
            "Diagnostic View",
            "Why do ratings differ?",
            "Diagnostic analytics examining the relationship between building characteristics and energy ratings.",
        )

        st.plotly_chart(
            chart_average_score(df, "BUILT_FORM", "Mean Rating Score by Built Form"),
            width="stretch",
            key="diag_built_form",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_average_score(df, "MAIN_FUEL", "Mean Rating Score by Main Fuel", top_n=12),
            width="stretch",
            key="diag_main_fuel",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_average_score(df, "WALLS_ENERGY_EFF", "Mean Rating Score by Wall Efficiency"),
            width="stretch",
            key="diag_walls",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_average_score(df, "ROOF_ENERGY_EFF", "Mean Rating Score by Roof Efficiency"),
            width="stretch",
            key="diag_roof",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_average_score(df, "WINDOWS_ENERGY_EFF", "Mean Rating Score by Window Efficiency"),
            width="stretch",
            key="diag_windows",
            config={"displayModeBar": False},
        )

        st.plotly_chart(
            chart_average_score(df, "MAINHEAT_ENERGY_EFF", "Mean Rating Score by Main Heating Efficiency"),
            width="stretch",
            key="diag_heating",
            config={"displayModeBar": False},
        )

        success_box(
            "Diagnostic patterns support the modelling results: heating efficiency, hot water efficiency, insulation quality, "
            "roof and wall efficiency, fuel type and built form all help explain EPC rating differences."
        )

    # TAB 4
    with tabs[3]:
        section(
            "Predictive Modelling",
            "Model performance",
            "Comparison of classification models trained to predict CURRENT_ENERGY_RATING.",
        )

        if model_df is None:
            warn_box("model_results.csv is missing.")
        else:
            st.plotly_chart(
                chart_model_comparison(model_df),
                width="stretch",
                key="model_comparison",
                config={"displayModeBar": False},
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Highest accuracy", f"{best_acc:.1%}", best_acc_model)
            with c2:
                st.metric("Best Macro F1", f"{best_f1:.3f}", best_f1_model)
            with c3:
                dummy_row = model_df[model_df["Model"].str.contains("Dummy", case=False, na=False)]
                if len(dummy_row):
                    st.metric("Dummy baseline accuracy", f"{dummy_row.iloc[0]['Accuracy']:.1%}")
                else:
                    st.metric("Dummy baseline accuracy", "N/A")

            insight_box(
                "HistGradientBoosting achieved the highest overall accuracy, while Logistic Regression achieved the best Macro F1. "
                "Macro F1 is important because the EPC classes are imbalanced, especially for A, F and G ratings."
            )

            img = load_img("fig17")
            if img:
                st.image(img, caption="Notebook model comparison chart", width="stretch")

            img = load_img("fig18")
            if img:
                st.image(img, caption="Confusion matrix output", width="stretch")

            img = load_img("fig18b")
            if img:
                st.image(
                    img,
                    caption="Classification report heatmap for the selected Logistic Regression model",
                    width="stretch",
                )
                insight_box(
                    "The classification report heatmap shows class-wise precision, recall and F1-score. "
                    "It confirms stronger performance on common middle bands such as B, C and D, "
                    "while rarer classes such as A remain more difficult to classify."
                )

    # TAB 5
    with tabs[4]:
        section(
            "Interpretability",
            "Feature importance",
            "Identifying which building characteristics have the strongest influence on EPC rating prediction.",
        )

        if perm_df is None:
            warn_box("permutation_feature_importance.csv is missing.")
        else:
            n = st.slider("Top features to display", 10, 30, 20)

            st.plotly_chart(
                chart_perm_importance(perm_df, n),
                width="stretch",
                key="feature_perm",
                config={"displayModeBar": False},
            )

            st.markdown("")

            st.plotly_chart(
                grouped_perm_importance(perm_df, n),
                width="stretch",
                key="feature_grouped",
                config={"displayModeBar": False},
            )

            success_box(
                "The strongest factors include hot water efficiency, low-efficiency heating, insulation quality, "
                "main heating efficiency, built form, roof efficiency, fuel type and number of rooms."
            )

            img = load_img("fig19")
            if img:
                st.image(img, caption="Notebook output: permutation importance", width="stretch")

            img = load_img("fig20")
            if img:
                st.image(img, caption="Notebook output: grouped permutation importance", width="stretch")

        with st.expander("Supplementary Random Forest MDI importance"):
            if rf_df is not None:
                st.plotly_chart(
                    chart_rf_importance(rf_df, 20),
                    width="stretch",
                    key="rf_mdi",
                    config={"displayModeBar": False},
                )

                img = load_img("fig21")
                if img:
                    st.image(img, caption="Notebook output: Random Forest MDI importance", width="stretch")
            else:
                warn_box("random_forest_feature_importance.csv is missing.")

    # TAB 6
    with tabs[5]:
        section(
            "Decision Support",
            "Evidence-based recommendations",
            "Practical recommendations derived from the descriptive, diagnostic and predictive analysis.",
        )

        rec_card(
            "1. Prioritise heating and hot water efficiency improvements",
            "Hot water energy efficiency, low-efficiency heating and main heating efficiency were among the strongest predictive factors. "
            "This suggests that inefficient heating and hot water systems should be prioritised for targeted improvement programmes.",
            "High impact",
        )

        rec_card(
            "2. Target insulation upgrades across walls, roofs and floors",
            "The insulation quality score, roof efficiency, wall efficiency and floor descriptions were influential in the feature importance results. "
            "Fabric upgrades should therefore be a central retrofit priority.",
            "Fabric-first priority",
        )

        rec_card(
            "3. Focus local interventions on older and detached properties",
            "Built form and construction age help explain EPC differences. Detached and older properties often have greater heat loss risk due to exposed surfaces and less efficient construction standards.",
            "Targeted retrofit",
        )

        rec_card(
            "4. Use predictive modelling to support property prioritisation",
            "The trained model can be used as a decision-support tool to flag property profiles that are likely to have lower EPC ratings. "
            "This could help local authorities and housing providers prioritise engagement.",
            "Data-driven targeting",
        )

        rec_card(
            "5. Improve EPC data quality for future analysis",
            "Unknown and missing values reduce analytical certainty. More complete and standardised assessment records would improve future modelling, monitoring and policy evaluation.",
            "Data quality",
        )

        warn_box(
            "The dashboard is a visual demonstration tool. The Jupyter notebook remains the primary reproducible evidence for the coursework submission."
        )

    # TAB 7
    with tabs[6]:
        section(
            "Repository Check",
            "Input file check",
            "All dashboard files should be in the same folder as app.py.",
        )

        for name, path in FILES.items():
            render_file_row(name, path)


if __name__ == "__main__":
    main()