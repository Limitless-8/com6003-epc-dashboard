"""
COM6003 — Buckinghamshire EPC Energy Performance Dashboard
Colab/Streamlit-safe version.

This version intentionally avoids custom raw HTML blocks so it renders reliably
through Google Colab + localtunnel. It uses native Streamlit components,
Plotly charts, and the existing notebook outputs in the same folder as app.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

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
    "A": "#1a9641",
    "B": "#52b153",
    "C": "#a6d96a",
    "D": "#ffe600",
    "E": "#f98f20",
    "F": "#e8511a",
    "G": "#cc1b12",
}

PLOT_TEMPLATE = "plotly_white"

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

    for col in ["PROPERTY_TYPE", "BUILT_FORM", "CONSTRUCTION_AGE_BAND", "PROPERTY_AGE_GROUP", "TENURE"]:
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
# Helper functions
# -----------------------------------------------------------------------------
def file_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"File": key, "Path": path.name, "Found": path.exists()}
            for key, path in FILES.items()
        ]
    )


def safe_col(df: pd.DataFrame, col: str) -> bool:
    return df is not None and col in df.columns


def clean_categories(values: Iterable[str]) -> list[str]:
    bad = {"Unknown", "Not Recorded", "NO DATA!", "INVALID!", "nan", "None", "N/A"}
    return [v for v in values if str(v) not in bad]


def style_fig(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=height,
        margin=dict(l=20, r=20, t=65, b=35),
        font=dict(size=13),
        title_font=dict(size=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def rating_distribution_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["CURRENT_ENERGY_RATING"].value_counts().reindex(RATING_ORDER).fillna(0).astype(int)
    total = counts.sum()
    labels = [f"{v:,}<br>{(v / total * 100):.1f}%" if total else "0" for v in counts]
    fig = go.Figure(
        data=[
            go.Bar(
                x=counts.index,
                y=counts.values,
                text=labels,
                textposition="outside",
                marker_color=[RATING_COLORS.get(r, "#64748b") for r in counts.index],
                hovertemplate="Rating %{x}<br>%{y:,} certificates<extra></extra>",
            )
        ]
    )
    fig.update_layout(title="Distribution of Current EPC Ratings", xaxis_title="Energy Rating", yaxis_title="Number of certificates")
    return style_fig(fig, 420)


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
        color_continuous_scale="Teal",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", hovertemplate="%{y}<br>%{x:,}<extra></extra>")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return style_fig(fig, max(360, 30 * len(vc) + 120))


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
        color_continuous_scale="Viridis",
    )
    fig.update_traces(textposition="outside", hovertemplate="%{y}<br>Average score: %{x:.2f}<extra></extra>")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_range=[0, 7.5])
    return style_fig(fig, max(360, 32 * len(grp) + 120))


def floor_area_box(df: pd.DataFrame) -> go.Figure:
    plot_df = df[["CURRENT_ENERGY_RATING", "TOTAL_FLOOR_AREA"]].dropna().copy()
    plot_df = plot_df[plot_df["CURRENT_ENERGY_RATING"].isin(RATING_ORDER)]
    # cap visual extreme tail for readability only
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
    return style_fig(fig, 430)


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
    return style_fig(fig, 460)


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
        color_discrete_sequence=["#2563eb", "#0f766e", "#7c3aed"],
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(yaxis_range=[0, 1.05], xaxis_title="", yaxis_title="Score")
    return style_fig(fig, 430)


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
        color_continuous_scale="Greens",
    )
    fig.update_traces(hovertemplate="%{y}<br>Importance: %{x:.4f}<extra></extra>")
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(500, 28 * n + 140))


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
    grouped = tmp.groupby("Original_Feature", as_index=False)["Perm_Mean"].sum().sort_values("Perm_Mean", ascending=False).head(n)
    grouped = grouped.iloc[::-1]
    fig = px.bar(
        grouped,
        x="Perm_Mean",
        y="Original_Feature",
        orientation="h",
        title=f"Grouped Feature Importance - Top {n}",
        labels={"Perm_Mean": "Summed permutation importance", "Original_Feature": "Original feature"},
        color="Perm_Mean",
        color_continuous_scale="Blues",
    )
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(500, 28 * n + 140))


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
        color_continuous_scale="Oranges",
    )
    fig.update_layout(coloraxis_showscale=False)
    return style_fig(fig, max(500, 28 * n + 140))


def show_image(key: str, caption: str):
    img = load_image(FILES[key])
    if img is None:
        st.warning(f"Missing image: {FILES[key].name}")
    else:
        st.image(img, caption=caption, width="stretch")


# -----------------------------------------------------------------------------
# Sidebar and filtering (Colab/localtunnel-safe: no interactive sidebar widgets)
# -----------------------------------------------------------------------------
def sidebar_filters(df: Optional[pd.DataFrame]) -> Dict[str, str]:
    """Render a stable sidebar without dynamic selectbox/multiselect widgets.
    Some localtunnel sessions fail to fetch Streamlit's widget JS bundles, so this
    showcase version keeps the sidebar static and uses the full dataset.
    """
    st.sidebar.title("⚡ EPC Dashboard")
    st.sidebar.caption("COM6003 Data Science · Buckinghamshire")
    st.sidebar.divider()

    if df is None:
        st.sidebar.error("Dataset not found.")
        return {}

    st.sidebar.subheader("Dataset Summary")
    st.sidebar.metric("Total certificates", f"{len(df):,}")
    st.sidebar.metric("Property types", f"{df['PROPERTY_TYPE'].nunique() if 'PROPERTY_TYPE' in df.columns else 0}")
    st.sidebar.metric("Ratings available", f"{df['CURRENT_ENERGY_RATING'].nunique() if 'CURRENT_ENERGY_RATING' in df.columns else 0}")
    st.sidebar.divider()
    st.sidebar.info(
        "Stable Colab demo mode is enabled. The dashboard uses the full "
        "Buckinghamshire EPC dataset so it remains reliable through localtunnel."
    )
    return {}


def apply_filters(df: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
    return df.copy()


# -----------------------------------------------------------------------------
# Main app
# -----------------------------------------------------------------------------
def main() -> None:
    df_raw = load_epc(FILES["epc"])
    model_df = load_csv(FILES["models"])
    perm_df = load_csv(FILES["perm"])
    rf_df = load_csv(FILES["rf"])

    filters = sidebar_filters(df_raw)
    df = apply_filters(df_raw, filters) if df_raw is not None else None

    st.title("⚡ Buckinghamshire EPC Energy Performance Dashboard")
    st.caption("Data-driven analysis and prediction of domestic Energy Performance Certificate ratings")

    if df_raw is None:
        st.error("The cleaned EPC dataset was not found. Make sure all files are in the same folder as app.py.")
        st.write("### File check")
        for key, path in FILES.items():
            status = "✅ Found" if path.exists() else "❌ Missing"
            st.write(f"{status} — `{path.name}`")
        return

    tabs = st.tabs([
        "Executive Overview",
        "Building Insights",
        "Diagnostic Analysis",
        "Model Performance",
        "Feature Importance",
        "Recommendations",
        "Files",
    ])

    # Executive Overview
    with tabs[0]:
        st.subheader("Executive Overview")
        total = len(df_raw)
        common_rating = df_raw["CURRENT_ENERGY_RATING"].mode()[0]
        cd_pct = df_raw["CURRENT_ENERGY_RATING"].isin(["C", "D"]).mean() * 100
        ac_pct = df_raw["CURRENT_ENERGY_RATING"].isin(["A", "B", "C"]).mean() * 100
        best_accuracy = model_df["Accuracy"].max() if model_df is not None else np.nan
        best_macro = model_df["Macro F1"].max() if model_df is not None else np.nan

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total EPC records", f"{total:,}")
        c2.metric("Most common rating", common_rating)
        c3.metric("C/D rated properties", f"{cd_pct:.1f}%")
        c4.metric("Best accuracy", f"{best_accuracy:.1%}" if pd.notna(best_accuracy) else "N/A")
        c5.metric("Best Macro F1", f"{best_macro:.3f}" if pd.notna(best_macro) else "N/A")

        st.info(
            "Most Buckinghamshire domestic EPCs are concentrated in bands C and D. "
            "A-rated and G-rated certificates are comparatively rare, which also explains why minority classes are harder for models to classify."
        )

        left, right = st.columns([2, 1])
        with left:
            st.plotly_chart(rating_distribution_chart(df), width="stretch", key="overview_rating_distribution")
        with right:
            st.write("#### Filtered stock summary")
            st.metric("Filtered records", f"{len(df):,}", f"{len(df)/len(df_raw)*100:.1f}% of full dataset")
            if safe_col(df, "TOTAL_FLOOR_AREA"):
                st.metric("Average floor area", f"{df['TOTAL_FLOOR_AREA'].mean():.0f} m²")
            st.metric("A-C rated", f"{ac_pct:.1f}%")
            st.write("#### Static notebook figure")
            show_image("fig01", "Notebook output: EPC rating distribution")

    # Building Insights
    with tabs[1]:
        st.subheader("Building Energy Insights")
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

    # Diagnostic Analysis
    with tabs[2]:
        st.subheader("Diagnostic Analysis")
        st.write("These charts explore why energy ratings differ across building characteristics.")

        c1, c2 = st.columns(2)
        with c1:
            if safe_col(df, "BUILT_FORM"):
                st.plotly_chart(average_score_chart(df, "BUILT_FORM", "Mean Rating Score by Built Form"), width="stretch", key="diag_built_form")
        with c2:
            if safe_col(df, "MAIN_FUEL"):
                st.plotly_chart(average_score_chart(df, "MAIN_FUEL", "Mean Rating Score by Main Fuel", top_n=12), width="stretch", key="diag_main_fuel")

        st.success(
            "Diagnostic interpretation: heating system efficiency, hot water efficiency, insulation quality, built form, fuel type and property age all show meaningful links with EPC outcomes."
        )

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

    # Model Performance
    with tabs[3]:
        st.subheader("Model Performance")
        if model_df is None:
            st.error("model_results.csv was not found.")
        else:
            st.plotly_chart(model_comparison_chart(model_df), width="stretch", key="model_comparison_chart")

            best_acc_row = model_df.loc[model_df["Accuracy"].idxmax()]
            best_f1_row = model_df.loc[model_df["Macro F1"].idxmax()]
            c1, c2, c3 = st.columns(3)
            c1.metric("Highest accuracy", f"{best_acc_row['Accuracy']:.1%}", best_acc_row["Model"])
            c2.metric("Best Macro F1", f"{best_f1_row['Macro F1']:.3f}", best_f1_row["Model"])
            baseline = model_df[model_df["Model"].astype(str).str.contains("Dummy", case=False, na=False)]
            if not baseline.empty:
                c3.metric("Dummy baseline accuracy", f"{baseline.iloc[0]['Accuracy']:.1%}")

            st.write("#### Model results")
            for _, row in model_df.iterrows():
                st.write(
                    f"**{row['Model']}** — "
                    f"Accuracy: `{row['Accuracy']:.4f}` · "
                    f"Macro F1: `{row['Macro F1']:.4f}` · "
                    f"Weighted F1: `{row['Weighted F1']:.4f}`"
                )
            st.info(
                "HistGradientBoosting achieved the highest overall accuracy, while Logistic Regression achieved the best Macro F1. "
                "Macro F1 is important because EPC classes are imbalanced, especially for A, F and G ratings."
            )

            c1, c2 = st.columns(2)
            with c1:
                show_image("fig17", "Notebook output: model comparison")
            with c2:
                show_image("fig18", "Notebook output: confusion matrix")

    # Feature Importance
    with tabs[4]:
        st.subheader("Feature Importance")
        st.write(
            "Permutation importance measures how much Macro F1 decreases when a feature is shuffled. "
            "Larger drops indicate stronger predictive influence."
        )
        if perm_df is None:
            st.error("permutation_feature_importance.csv was not found.")
        else:
            top_n = st.slider("Top features to display", min_value=10, max_value=30, value=20, step=1)
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(feature_importance_chart(perm_df, n=top_n), width="stretch", key="perm_importance_chart")
            with c2:
                st.plotly_chart(grouped_importance_chart(perm_df, n=top_n), width="stretch", key="grouped_importance_chart")

            st.write("#### Top permutation importance values")
            for _, row in perm_df.head(top_n).iterrows():
                std_text = f" ± {row['Perm_Std']:.4f}" if "Perm_Std" in perm_df.columns else ""
                st.write(f"**{row['Feature']}** — `{row['Perm_Mean']:.4f}{std_text}`")
            st.success(
                "The strongest factors include hot water efficiency, low-efficiency heating, insulation quality, main heating efficiency, built form, roof efficiency, fuel type and number of rooms."
            )

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

    # Recommendations
    with tabs[5]:
        st.subheader("Evidence-Based Recommendations")
        recommendations = [
            (
                "🔥 Prioritise heating and hot water efficiency improvements",
                "Hot water energy efficiency and low-efficiency heating were among the strongest predictors. Upgrading inefficient heating and hot water systems should be a priority intervention.",
            ),
            (
                "🧱 Target insulation upgrades",
                "Insulation quality, wall efficiency, roof efficiency and floor-related features were influential. Retrofit programmes should prioritise fabric improvements before or alongside system upgrades.",
            ),
            (
                "🏘️ Focus on older and detached properties",
                "Built form and construction age influence rating differences. Detached and older properties are useful candidates for targeted support because they often have greater heat-loss risk.",
            ),
            (
                "📊 Use prediction to support local authority targeting",
                "The trained model can help identify property profiles likely to fall into lower EPC bands. This could support future prioritisation, subject to data governance and validation.",
            ),
            (
                "📋 Improve EPC data quality",
                "Unknown or missing fields reduce certainty. Better completeness in future EPC records would improve analysis, interpretation and predictive modelling.",
            ),
        ]
        for title, body in recommendations:
            with st.container(border=True):
                st.write(f"#### {title}")
                st.write(body)

        st.warning(
            "Limitations: EPC ratings estimate standardised energy performance rather than actual household consumption. "
            "Class imbalance, assessor variation, missing values and local-authority specificity should be considered when interpreting results."
        )

    # Files
    with tabs[6]:
        st.subheader("Input File Check")
        st.caption("All dashboard files should be in the same folder as app.py.")
        found_count = sum(1 for path in FILES.values() if path.exists())
        st.metric("Files found", f"{found_count}/{len(FILES)}")
        for key, path in FILES.items():
            status = "✅ Found" if path.exists() else "❌ Missing"
            size = f"{path.stat().st_size / 1024:.1f} KB" if path.exists() else "—"
            st.write(f"{status} — `{path.name}` — {size}")


if __name__ == "__main__":
    main()
