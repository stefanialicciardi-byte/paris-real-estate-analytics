import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import os
from pathlib import Path
from shapely.geometry import shape
from shapely.wkt import loads as wkt_loads
import branca.colormap as cm
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colorbar import ColorbarBase
from data_loader import load_dvf, load_rent, load_green, load_planned

st.set_page_config(
    page_title="Integrated Map",
    layout="wide",
)

#  Load data
dvf_raw   = load_dvf()
rent_raw  = load_rent()
green_raw = load_green()
plan_raw  = load_planned()

n_ok = (dvf_raw["data_quality_flag"] == "ok").sum()

#  Sidebar controls
with st.sidebar:
    st.markdown("## Map Controls")
    st.markdown("---")
    st.markdown("### Reference Rent")
    room_label = st.radio(
        "Number of rooms",
        options=["1 room", "2 rooms", "3 rooms", "4 rooms +"],
        index=1,
        label_visibility="collapsed"
    )
    room_map   = {"1 room": 1, "2 rooms": 2, "3 rooms": 3, "4 rooms +": 4}
    room_count = room_map[room_label]

    st.markdown("---")
    st.markdown("### Layers")
    show_dvf     = st.checkbox("Sale price (€/m²)",    value=True)
    show_rent    = st.checkbox("Reference rent",         value=True)
    show_green   = st.checkbox("Existing green spaces", value=True)
    show_planned = st.checkbox("Planned green spaces",  value=True)

    st.markdown("---")
    st.caption("DVF 2025 · Rent control data · Open Data Paris")

#  Header
st.title("Analysis")
st.markdown("Interactive map of sale prices, rent-control zones, and green spaces · Paris 2025")
st.markdown("---")

#  KPIs
dvf_clean    = dvf_raw[dvf_raw["data_quality_flag"] == "ok"]
avg_ref_rent = rent_raw[rent_raw["room_count"] == room_count]["reference_rent"].mean()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Clean Transactions", f"{n_ok:,}")
col2.metric("Median Price / m²", f"€{dvf_clean['price_per_sqm'].median():,.0f}")
col3.metric(f"Avg. Reference Rent ({room_label})", f"€{avg_ref_rent:.1f} /m²")
col4.metric("Green Spaces", f"{len(green_raw):,}")

st.markdown("---")

#  Map helpers
@st.cache_data
def build_quartier_gdf(_rent_df):
    unique_q = _rent_df.drop_duplicates("quarter_id")[
        ["quarter_id", "quarter_name", "postal_code", "geo_shape"]
    ].copy()
    geoms = [shape(json.loads(r["geo_shape"])["geometry"]) for _, r in unique_q.iterrows()]
    gdf = gpd.GeoDataFrame(unique_q, geometry=geoms, crs="EPSG:4326")
    gdf["arrondissement"] = gdf["postal_code"].astype(str).str[-2:].astype(int)
    return gdf

@st.cache_data
def compute_dvf_stats(_dvf_df, _q_gdf):
    dvf_clean = _dvf_df[
        (_dvf_df["price_per_sqm"].notna()) &
        (_dvf_df["lon"].notna()) &
        (_dvf_df["data_quality_flag"] == "ok")
    ].copy()
    dvf_pts = gpd.GeoDataFrame(
        dvf_clean,
        geometry=gpd.points_from_xy(dvf_clean.lon, dvf_clean.lat),
        crs="EPSG:4326"
    )
    joined = gpd.sjoin(dvf_pts, _q_gdf[["quarter_id", "geometry"]], how="left", predicate="within")
    stats = (
        joined.groupby("quarter_id")
        .agg(median_price=("price_per_sqm", "median"), n_tx=("price_per_sqm", "count"))
        .reset_index()
    )
    return _q_gdf.merge(stats, on="quarter_id", how="left")

@st.cache_data
def build_green_gdf(_green_df):
    import ast
    filtered = _green_df[_green_df["polygon_area"] > 500].copy()
    geoms, idx_keep = [], []
    for idx, row in filtered.iterrows():
        try:
            geo = ast.literal_eval(row["geo_shape"])
            if geo.get("type") == "Feature":
                geoms.append(shape(geo["geometry"]))
            else:
                geoms.append(shape(geo))
            idx_keep.append(idx)
        except Exception:
            pass
    filtered = filtered.loc[idx_keep].copy().reset_index(drop=True)
    filtered["_geom"] = geoms
    gdf = gpd.GeoDataFrame(filtered, geometry="_geom", crs="EPSG:4326")
    max_a = gdf["polygon_area"].max()
    gdf["opacity"] = (0.25 + 0.55 * (gdf["polygon_area"] / max_a)).clip(0.25, 0.8)
    return gdf

q_gdf     = build_quartier_gdf(rent_raw)
dvf_gdf   = compute_dvf_stats(dvf_raw, q_gdf)
green_gdf = build_green_gdf(green_raw)

#  Map build
TOOLTIP_STYLE = (
    "background-color: white;"
    "border: 1px solid #ccc;"
    "border-radius: 4px;"
    "font-family: sans-serif;"
    "font-size: 13px;"
    "padding: 6px 10px;"
)

def draw_colorbar(hex_colors, vmin, vmax, label):
    fig, ax = plt.subplots(figsize=(4, 0.45))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(bottom=0.55)
    cmap = mcolors.LinearSegmentedColormap.from_list("custom", hex_colors)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cb   = ColorbarBase(ax, cmap=cmap, norm=norm, orientation="horizontal")
    cb.set_label(label, fontsize=9, color="#444", labelpad=4)
    cb.ax.tick_params(labelsize=8, colors="#444")
    cb.outline.set_visible(False)
    return fig

def ordinal(n):
    n = int(n)
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd','th'][min(n % 10, 4)]}"

def feat(geometry, props):
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": geometry, "properties": props}
    ]}

def build_map():
    m = folium.Map(
        location=[48.8566, 2.3522],
        zoom_start=12,
        tiles="CartoDB positron",
        zoom_control=True,
        scrollWheelZoom=False
    )

    valid    = dvf_gdf[dvf_gdf["median_price"].notna()]
    dvf_vmin = valid["median_price"].quantile(0.05)
    dvf_vmax = valid["median_price"].quantile(0.95)
    dvf_cmap = cm.LinearColormap(
        colors=["#FFF176", "#FF9800", "#D32F2F"],
        vmin=dvf_vmin, vmax=dvf_vmax, caption="Sale price (€/m²)"
    )

    rent_sel  = rent_raw[rent_raw["room_count"] == room_count]
    rent_cmap = cm.LinearColormap(
        colors=["#E3F2FD", "#1565C0"],
        vmin=rent_sel["reference_rent"].min(),
        vmax=rent_sel["reference_rent"].max(),
        caption=f"Reference rent {room_label} (€/m²)"
    )

    if show_dvf and show_rent:
        dvf_layer = folium.FeatureGroup(name="Sale price (€/m²)", show=True)
        for _, row in dvf_gdf.iterrows():
            if pd.isna(row["median_price"]):
                continue
            color = dvf_cmap(max(dvf_vmin, min(dvf_vmax, row["median_price"])))
            folium.GeoJson(
                row["geometry"].__geo_interface__,
                style_function=lambda x, c=color: {
                    "fillColor": c, "color": "#ffffff", "weight": 0.4, "fillOpacity": 0.7
                }
            ).add_to(dvf_layer)
        dvf_layer.add_to(m)

        rent_layer = folium.FeatureGroup(name="Reference rent", show=True)
        for _, row in rent_sel.iterrows():
            try:
                geojson = json.loads(row["geo_shape"])
                color   = rent_cmap(row["reference_rent"])
                arr_num = str(row["postal_code"])[-2:].lstrip("0") or "1"
                qid     = row["quarter_id"]
                dvf_row = dvf_gdf[dvf_gdf["quarter_id"] == qid]
                if not dvf_row.empty and pd.notna(dvf_row.iloc[0]["median_price"]):
                    d = dvf_row.iloc[0]
                    props   = {
                        "Quarter":        row["quarter_name"],
                        "Arrondissement": ordinal(arr_num),
                        "Median price":   f"{d['median_price']:,.0f} €/m²",
                        "Transactions":   str(int(d["n_tx"])) if pd.notna(d.get("n_tx")) else "—",
                        "Min rent":       f"{row['min_rent']} €/m²",
                        "Reference rent": f"{row['reference_rent']} €/m²",
                        "Max rent":       f"{row['max_rent']} €/m²",
                    }
                    fields  = ["Quarter","Arrondissement","Median price","Transactions",
                               "Min rent","Reference rent","Max rent"]
                    aliases = ["Quarter:","Arrondissement:","Median price:","Transactions:",
                               "Min rent:","Reference rent:","Max rent:"]
                else:
                    props   = {
                        "Quarter":        row["quarter_name"],
                        "Arrondissement": ordinal(arr_num),
                        "Min rent":       f"{row['min_rent']} €/m²",
                        "Reference rent": f"{row['reference_rent']} €/m²",
                        "Max rent":       f"{row['max_rent']} €/m²",
                    }
                    fields  = ["Quarter","Arrondissement","Min rent","Reference rent","Max rent"]
                    aliases = ["Quarter:","Arrondissement:","Min rent:","Reference rent:","Max rent:"]
                folium.GeoJson(
                    feat(geojson["geometry"], props),
                    style_function=lambda x, c=color: {
                        "fillColor": c, "color": "#90CAF9", "weight": 0.7, "fillOpacity": 0.45
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=fields, aliases=aliases,
                        style=TOOLTIP_STYLE, sticky=True
                    )
                ).add_to(rent_layer)
            except Exception:
                pass
        rent_layer.add_to(m)

    elif show_dvf:
        layer = folium.FeatureGroup(name="Sale price (€/m²)", show=True)
        for _, row in dvf_gdf.iterrows():
            if pd.isna(row["median_price"]):
                continue
            color = dvf_cmap(max(dvf_vmin, min(dvf_vmax, row["median_price"])))
            folium.GeoJson(
                feat(row["geometry"].__geo_interface__, {
                    "Quarter":        row["quarter_name"],
                    "Arrondissement": ordinal(row["arrondissement"]),
                    "Median price":   f"{row['median_price']:,.0f} €/m²",
                    "Transactions":   str(int(row["n_tx"])) if pd.notna(row.get("n_tx")) else "—",
                }),
                style_function=lambda x, c=color: {
                    "fillColor": c, "color": "#ffffff", "weight": 0.4, "fillOpacity": 0.7
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["Quarter","Arrondissement","Median price","Transactions"],
                    aliases=["Quarter:","Arrondissement:","Median price:","Transactions:"],
                    style=TOOLTIP_STYLE, sticky=True
                )
            ).add_to(layer)
        layer.add_to(m)

    elif show_rent:
        layer = folium.FeatureGroup(name="Reference rent", show=True)
        for _, row in rent_sel.iterrows():
            try:
                geojson = json.loads(row["geo_shape"])
                color   = rent_cmap(row["reference_rent"])
                arr_num = str(row["postal_code"])[-2:].lstrip("0") or "1"
                folium.GeoJson(
                    feat(geojson["geometry"], {
                        "Quarter":        row["quarter_name"],
                        "Arrondissement": ordinal(arr_num),
                        "Min rent":       f"{row['min_rent']} €/m²",
                        "Reference rent": f"{row['reference_rent']} €/m²",
                        "Max rent":       f"{row['max_rent']} €/m²",
                    }),
                    style_function=lambda x, c=color: {
                        "fillColor": c, "color": "#90CAF9", "weight": 0.7, "fillOpacity": 0.55
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["Quarter","Arrondissement","Min rent","Reference rent","Max rent"],
                        aliases=["Quarter:","Arrondissement:","Min rent:","Reference rent:","Max rent:"],
                        style=TOOLTIP_STYLE, sticky=True
                    )
                ).add_to(layer)
            except Exception:
                pass
        layer.add_to(m)

    if show_green:
        layer = folium.FeatureGroup(name="Existing green spaces", show=True)
        for _, row in green_gdf.iterrows():
            try:
                area_str = f"{row['polygon_area']:,.0f} m²" if pd.notna(row["polygon_area"]) else "—"
                folium.GeoJson(
                    feat(row["_geom"].__geo_interface__, {
                        "Name": row["green_space_name"],
                        "Type": row["green_space_type"],
                        "Area": area_str,
                    }),
                    style_function=lambda x, op=float(row["opacity"]): {
                        "fillColor": "#4CAF50", "color": "#2E7D32",
                        "weight": 0.5, "fillOpacity": op
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["Name","Type","Area"],
                        aliases=["Name:","Type:","Area:"],
                        style=TOOLTIP_STYLE, sticky=True
                    )
                ).add_to(layer)
            except Exception:
                pass
        layer.add_to(m)

    if show_planned:
        layer = folium.FeatureGroup(name="Planned green spaces", show=True)
        for _, row in plan_raw.iterrows():
            if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
                continue
            area_str = f"{row['added_space_indicator']:,.0f} m²" if pd.notna(row["added_space_indicator"]) and row["added_space_indicator"] > 0 else "—"
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=7,
                color="#1B5E20",
                weight=2,
                fill=True,
                fill_color="#66BB6A",
                fill_opacity=0.9,
                tooltip=folium.Tooltip(
                    f"<div style='{TOOLTIP_STYLE}'>"
                    f"<b>{row['project_name']}</b><br>"
                    f"<span style='color:#555'>Arrondissement:</span> {ordinal(row['arrondissement'])}<br>"
                    f"<span style='color:#555'>New green area:</span> {area_str}<br>"
                    f"<span style='color:#555'>{'Completed:' if int(row['completion_date']) <= 2025 else 'Est. completion:'}</span> {row['completion_date']}"
                    f"</div>",
                    sticky=True
                )
            ).add_to(layer)
        layer.add_to(m)

    return m

#  Colorbars
if show_dvf or show_rent:
    valid    = dvf_gdf[dvf_gdf["median_price"].notna()]
    dvf_vmin = valid["median_price"].quantile(0.05)
    dvf_vmax = valid["median_price"].quantile(0.95)
    rent_sel = rent_raw[rent_raw["room_count"] == room_count]
    cb_left, cb_right = st.columns(2)
    with cb_left:
        if show_dvf:
            fig = draw_colorbar(["#FFF176","#FF9800","#D32F2F"], dvf_vmin, dvf_vmax, "Sale price (€/m²)")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    with cb_right:
        if show_rent:
            fig = draw_colorbar(["#E3F2FD","#1565C0"],
                                rent_sel["reference_rent"].min(),
                                rent_sel["reference_rent"].max(),
                                f"Reference rent {room_label} (€/m²)")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

#  Map
m = build_map()
st_folium(m, width="100%", height=700, returned_objects=[])

#  Data notes
n_flagged = (dvf_raw["data_quality_flag"] != "ok").sum()
st.markdown("---")
with st.expander("Data Notes"):
    st.markdown(f"""
**Sale price layer:** Based on {n_ok:,} apartment transactions from the DVF dataset, Paris 2025.
{n_flagged:,} records were excluded based on data quality flags: price_per_sqm_high (n=537),
surface_too_small (n=196), high_room_count (n=98).
Each quartier shows the **median** price per m² to limit the influence of outliers.

**Reference rent layer:** Based on the Paris rent-control framework (*encadrement des loyers*), 2025 edition.
Rents are expressed in €/m² of living space and vary by quartier and number of rooms.
Min and max values represent the legal lower and upper bounds around the reference rent.

**Green spaces:** Source: Open Data Paris. Existing spaces filtered to polygon area > 500 m².
Planned spaces represent projects with a confirmed completion date.
""")
