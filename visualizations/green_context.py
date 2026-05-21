from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st



TRANSACTION_PATH = "data/dvf_paris_2025_aggregated.csv"
GREEN_PATH = "data/green_spaces.csv"
PLANNED_PATH = "data/planned_green_spaces.csv"


def load_transaction_data(path: str = TRANSACTION_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["price_per_sqm"].notna()].copy()
    df = df[df["price_per_sqm"] > 0]
    df = df[df["price_per_sqm"] <= df["price_per_sqm"].quantile(0.99)]

    df["arrondissement"] = pd.to_numeric(
        df["postal_code"].astype(str).str[-2:],
        errors="coerce",
    )
    return df


def load_green_data(path: str = GREEN_PATH) -> pd.DataFrame:
    green = pd.read_csv(path)
    green["arrondissement"] = pd.to_numeric(
        green["postal_code"].astype(str).str[-2:],
        errors="coerce",
    )
    return green


def load_planned_data(path: str = PLANNED_PATH) -> pd.DataFrame:
    planned = pd.read_csv(path)
    planned["arrondissement"] = pd.to_numeric(
        planned["arrondissement"],
        errors="coerce",
    )
    return planned


def prepare_dataset() -> pd.DataFrame:
    tx = load_transaction_data()
    green = load_green_data()
    planned = load_planned_data()

    tx_agg = (
        tx.groupby("arrondissement", as_index=False)
        .agg(
            median_price_per_sqm=("price_per_sqm", "median"),
            transaction_count=("transaction_key", "count"),
        )
    )

    green_agg = (
        green.groupby("arrondissement", as_index=False)
        .agg(existing_green_spaces=("green_space_id", "count"))
    )

    planned_agg = (
        planned.groupby("arrondissement", as_index=False)
        .agg(planned_green_projects=("project_name", "count"))
    )

    df = tx_agg.merge(green_agg, on="arrondissement", how="left")
    df = df.merge(planned_agg, on="arrondissement", how="left")
    df = df.fillna(
        {
            "existing_green_spaces": 0,
            "planned_green_projects": 0,
        }
    )

    df = df[df["arrondissement"].notna()].copy()
    df["arrondissement_label"] = df["arrondissement"].astype(int).astype(str)
    return df.sort_values("arrondissement")


def chart_price_by_arrondissement(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="arrondissement_label",
        y="median_price_per_sqm",
        title="Median Price per sqm by Arrondissement",
        labels={
            "arrondissement_label": "Arrondissement",
            "median_price_per_sqm": "Median price per sqm (EUR)",
        },
        color="median_price_per_sqm",
        color_continuous_scale="Blues",
    )
    fig.update_xaxes(type="category")
    return fig


def chart_green_space_by_arrondissement(df: pd.DataFrame):
    long_df = df.melt(
        id_vars="arrondissement_label",
        value_vars=["existing_green_spaces", "planned_green_projects"],
        var_name="type",
        value_name="count",
    )

    long_df["type"] = long_df["type"].replace(
        {
            "existing_green_spaces": "Existing green spaces",
            "planned_green_projects": "Planned green projects",
        }
    )

    fig = px.bar(
        long_df,
        x="arrondissement_label",
        y="count",
        color="type",
        barmode="group",
        title="Existing vs Planned Green Spaces by Arrondissement",
        labels={
            "arrondissement_label": "Arrondissement",
            "count": "Count",
            "type": "Type",
        },
        color_discrete_map={
            "Existing green spaces": "#1B5E20",
            "Planned green projects": "#A5D6A7",
        },
    )
    fig.update_xaxes(type="category")
    return fig


def chart_price_vs_green_space(df: pd.DataFrame):
    fig = px.scatter(
        df,
        x="existing_green_spaces",
        y="median_price_per_sqm",
        size="transaction_count",
        text="arrondissement_label",
        title="Median Price per sqm vs Existing Green Space Count",
        labels={
            "existing_green_spaces": "Existing green space count",
            "median_price_per_sqm": "Median price per sqm (EUR)",
            "transaction_count": "Transactions",
            "arrondissement_label": "Arrondissement",
        },
        color="median_price_per_sqm",
        color_continuous_scale="Viridis",
    )
    fig.update_traces(textposition="top center")
    return fig


def render_dashboard():
    st.title("Paris Real Estate and Green Spaces")
    st.caption(
        "This dashboard compares property prices with existing and planned green spaces across Paris. "
        "Unlike the interactive map, it focuses on arrondissement-level comparisons."
    )

    st.header("Do arrondissements with more green spaces tend to have higher property prices?")

    df = prepare_dataset()

    c1, c2, c3 = st.columns(3)
    c1.metric("Median sale price / sqm", f"{df['median_price_per_sqm'].median():,.0f} EUR")
    c2.metric("Total existing green spaces", f"{int(df['existing_green_spaces'].sum()):,}")
    c3.metric("Total planned projects", f"{int(df['planned_green_projects'].sum()):,}")

    st.markdown(
        """
        This dashboard focuses on three simple arrondissement-level comparisons:
        1. the first chart shows which arrondissements are more expensive
        2. the second chart compares existing and planned green spaces
        3. the third chart compares price level and existing green-space count
        """
    )

    st.plotly_chart(chart_price_by_arrondissement(df), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_green_space_by_arrondissement(df), use_container_width=True)
        st.caption(
            "Dark green shows existing green spaces today. Light green shows planned green projects, "
            "so you can compare current green areas with future investment by arrondissement."
        )
    with col2:
        st.plotly_chart(chart_price_vs_green_space(df), use_container_width=True)
        st.caption(
            "Each point is one arrondissement. This chart helps check whether arrondissements with more "
            "existing green spaces also tend to have higher or lower median prices."
        )

    st.info(
        "Key takeaway: the most expensive arrondissements are not the ones with the highest number of green spaces. "
        "This suggests that location and centrality are stronger price drivers, while green spaces provide useful additional context."
    )

    st.dataframe(
        df[
            [
                "arrondissement_label",
                "median_price_per_sqm",
                "transaction_count",
                "existing_green_spaces",
                "planned_green_projects",
            ]
        ],
        use_container_width=True,
    )


def run_streamlit_app():
    st.set_page_config(page_title="Paris Real Estate and Green Spaces", layout="wide")
    render_dashboard()


if __name__ == "__main__":
    if st is None or px is None:
        print("This file is intended for Streamlit + Plotly.")
        print("Install with: pip install streamlit plotly pandas")
    else:
        run_streamlit_app()


