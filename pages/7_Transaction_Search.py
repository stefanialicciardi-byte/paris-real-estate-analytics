import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import folium
import requests
from streamlit_folium import st_folium
from shapely.geometry import shape
from data_loader import load_dvf, load_rent

st.set_page_config(
    page_title="Transaction Search",
    layout="wide",
)

#  Load data
dvf_raw  = load_dvf()
rent_raw = load_rent()

#  Quarter geometry (needed for spatial join on selected transaction)
@st.cache_data
def build_quartier_gdf(_rent_df):
    unique_q = _rent_df.drop_duplicates("quarter_id")[
        ["quarter_id", "quarter_name", "postal_code", "geo_shape"]
    ].copy()
    geoms = [shape(json.loads(r["geo_shape"])["geometry"]) for _, r in unique_q.iterrows()]
    gdf = gpd.GeoDataFrame(unique_q, geometry=geoms, crs="EPSG:4326")
    return gdf

q_gdf = build_quartier_gdf(rent_raw)

@st.cache_data(ttl=86400)
def load_arrondissement_geojson():
    from shapely.geometry import shape, mapping, MultiPolygon
    url = (
        "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
        "arrondissements/exports/geojson?lang=fr&timezone=Europe%2FParis"
    )
    try:
        data = requests.get(url, timeout=10).json()
    except Exception:
        return None
    clean = []
    for feat in data.get("features", []):
        geom = shape(feat["geometry"])
        if isinstance(geom, MultiPolygon):
            geom = max(geom.geoms, key=lambda p: p.area)
        feat = dict(feat)
        feat["geometry"] = mapping(geom)
        clean.append(feat)
    data["features"] = clean
    return data

arr_geojson = load_arrondissement_geojson()

#  Header
st.title("Transaction Search")
st.markdown("Filter and explore individual DVF apartment transactions · Paris 2025")
st.markdown("---")

#  Sidebar: rent room selector
with st.sidebar:
    st.markdown("## Controls")
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
    st.caption("DVF 2025 · Rent control data · Open Data Paris")

#  Prepare transaction dataframe
transaction_df = dvf_raw.copy()

if "arrondissement" not in transaction_df.columns:
    if "postal_code" in transaction_df.columns:
        transaction_df["arrondissement"] = (
            transaction_df["postal_code"]
            .astype(str)
            .str.extract(r"(75\d{3})")[0]
            .str[-2:]
        )
        transaction_df["arrondissement"] = pd.to_numeric(
            transaction_df["arrondissement"], errors="coerce"
        )
    else:
        transaction_df["arrondissement"] = np.nan

if "transaction_date" in transaction_df.columns:
    transaction_df["transaction_date_sort"] = pd.to_datetime(
        transaction_df["transaction_date"], errors="coerce"
    )
    transaction_df["transaction_month"] = transaction_df["transaction_date_sort"].dt.month
    transaction_df["transaction_month_label"] = transaction_df["transaction_date_sort"].dt.strftime("%B")

quality_label_map = {
    "ok": "Clean records only",
    "price_per_sqm_high": "Flagged: unusually high price per m²",
    "surface_too_small": "Flagged: unusually small surface area",
    "high_room_count": "Flagged: unusually high room count",
}

def format_quality_label(flag):
    return quality_label_map.get(str(flag), str(flag).replace("_", " ").title())

def ordinal(n):
    n = int(n)
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd','th'][min(n % 10, 4)]}"

#  Filters
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    arr_values = sorted(
        transaction_df["arrondissement"].dropna().astype(int).unique().tolist()
    )
    selected_arrondissement = st.selectbox(
        "Arrondissement",
        options=["All"] + arr_values,
        format_func=lambda x: "All arrondissements" if x == "All" else f"{int(x)}{['th','st','nd','rd','th'][min(int(x) % 10, 4)]} arrondissement",
    )

with filter_col2:
    property_values = sorted(
        transaction_df["property_type"].dropna().astype(str).unique().tolist()
    ) if "property_type" in transaction_df.columns else []
    selected_property_type = st.selectbox(
        "Property type",
        options=["All"] + property_values,
        format_func=lambda x: "All property types" if x == "All" else x,
    )

with filter_col3:
    quality_values = [
        flag for flag in ["ok", "price_per_sqm_high", "surface_too_small", "high_room_count"]
        if flag in transaction_df["data_quality_flag"].dropna().unique().tolist()
    ]
    extra_quality_values = sorted(
        [flag for flag in transaction_df["data_quality_flag"].dropna().unique().tolist()
         if flag not in quality_values]
    )
    selected_quality = st.selectbox(
        "Data quality",
        options=["All"] + quality_values + extra_quality_values,
        index=1 if "ok" in quality_values else 0,
        format_func=lambda x: "All records" if x == "All" else format_quality_label(x),
    )

with filter_col4:
    if "transaction_month" in transaction_df.columns:
        month_lookup = (
            transaction_df[["transaction_month", "transaction_month_label"]]
            .dropna()
            .drop_duplicates()
            .sort_values("transaction_month")
        )
        month_options = ["All"] + month_lookup["transaction_month"].astype(int).tolist()
        month_label_map = dict(
            zip(month_lookup["transaction_month"].astype(int), month_lookup["transaction_month_label"])
        )
    else:
        month_options = ["All"]
        month_label_map = {}

    selected_month = st.selectbox(
        "Transaction month",
        options=month_options,
        format_func=lambda x: "All months" if x == "All" else month_label_map.get(int(x), str(x)),
    )

#  Apply filters
filtered_transactions = transaction_df.copy()

if selected_arrondissement != "All":
    filtered_transactions = filtered_transactions[
        filtered_transactions["arrondissement"] == int(selected_arrondissement)
    ]

if selected_property_type != "All" and "property_type" in filtered_transactions.columns:
    filtered_transactions = filtered_transactions[
        filtered_transactions["property_type"].astype(str) == selected_property_type
    ]

if selected_quality != "All":
    filtered_transactions = filtered_transactions[
        filtered_transactions["data_quality_flag"] == selected_quality
    ]

if selected_month != "All" and "transaction_month" in filtered_transactions.columns:
    filtered_transactions = filtered_transactions[
        filtered_transactions["transaction_month"] == int(selected_month)
    ]

#  Search
search_query = st.text_input(
    "Search within filtered transactions",
    placeholder="Street, address, transaction key, date, or property type",
)

if search_query and len(search_query.strip()) >= 2:
    q = search_query.strip().upper()
    searchable_cols = [
        c for c in ["address", "transaction_key", "transaction_date", "property_type", "postal_code"]
        if c in filtered_transactions.columns
    ]
    if searchable_cols:
        mask = pd.Series(False, index=filtered_transactions.index)
        for col in searchable_cols:
            mask = mask | filtered_transactions[col].fillna("").astype(str).str.upper().str.contains(q, regex=False)
        filtered_transactions = filtered_transactions[mask]

#  Sort
filtered_transactions = filtered_transactions.copy()
if "transaction_date_sort" in filtered_transactions.columns:
    filtered_transactions = filtered_transactions.sort_values(
        "transaction_date_sort", ascending=False, na_position="last"
    )

if "data_quality_flag" in filtered_transactions.columns:
    filtered_transactions["data_quality"] = filtered_transactions["data_quality_flag"].apply(format_quality_label)

preview_cols = [
    c for c in [
        "transaction_date", "address", "arrondissement", "property_type",
        "surface_area", "room_count", "property_value", "price_per_sqm",
        "data_quality", "transaction_key",
    ]
    if c in filtered_transactions.columns
]

#  Results table + detail panel
if filtered_transactions.empty:
    st.info("No transactions found. Try changing the filters or using a broader search term.")
else:
    st.markdown(f"### {len(filtered_transactions):,} transactions")

    preview = filtered_transactions[preview_cols].head(100).copy()
    st.dataframe(preview, use_container_width=True, hide_index=True)

    st.markdown("---")

    selection_limit = min(500, len(filtered_transactions))
    selection_df = filtered_transactions.head(selection_limit).copy()

    def format_transaction_option(idx):
        row = selection_df.loc[idx]
        address   = row.get("address", "Unknown address")
        date      = row.get("transaction_date", "—")
        price     = row.get("price_per_sqm", np.nan)
        rooms     = row.get("room_count", np.nan)
        price_txt = f"€{price:,.0f}/m²" if pd.notna(price) else "no €/m²"
        rooms_txt = f"{int(rooms)} room(s)" if pd.notna(rooms) else "rooms unknown"
        return f"{address} · {date} · {rooms_txt} · {price_txt}"

    selected_idx = st.selectbox(
        "Select a transaction",
        options=selection_df.index.tolist(),
        format_func=format_transaction_option,
    )

    selected_row = selection_df.loc[selected_idx]

    #  Spatial join to get quarter
    selected_with_quarter = selected_row.copy()
    has_coords = pd.notna(selected_row.get("lon")) and pd.notna(selected_row.get("lat"))

    if has_coords:
        selected_gdf = gpd.GeoDataFrame(
            pd.DataFrame([selected_row]),
            geometry=gpd.points_from_xy([selected_row["lon"]], [selected_row["lat"]]),
            crs="EPSG:4326",
        )
        joined = gpd.sjoin(
            selected_gdf[["transaction_key", "geometry"]],
            q_gdf[["quarter_id", "quarter_name", "geometry"]],
            how="left",
            predicate="within",
        )
        if not joined.empty:
            selected_with_quarter["quarter_id"]   = joined.iloc[0].get("quarter_id")
            selected_with_quarter["quarter_name"] = joined.iloc[0].get("quarter_name")

    rent_lookup = rent_raw[rent_raw["room_count"] == room_count].set_index("quarter_id")[
        ["reference_rent", "min_rent", "max_rent", "quarter_name"]
    ]

    flag       = selected_with_quarter.get("data_quality_flag", "ok")
    flag_color = "#dc2626" if flag != "ok" else "#16a34a"
    qid        = selected_with_quarter.get("quarter_id")
    rent_row   = rent_lookup.loc[qid] if (pd.notna(qid) and qid in rent_lookup.index) else None

    # Layout: detail tables left (2/3), mini-map right (1/3)
    col_detail, col_map = st.columns([2, 1])

    with col_detail:
        col_l, col_r = st.columns(2)
        arr_val = selected_with_quarter.get("arrondissement")
        flag_badge_bg  = "#fee2e2" if flag != "ok" else "#dcfce7"
        flag_badge_txt = "#991b1b" if flag != "ok" else "#166534"

        card_style = (
            "background:#f8f9fa; border-radius:8px; border:1px solid #e5e7eb;"
            "padding:16px 18px; height:100%;"
        )
        row_style  = "display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #f0f0f0; font-size:13.5px;"
        label_style = "color:#6b7280;"
        value_style = "color:#111827; font-weight:500; text-align:right; max-width:60%;"

        with col_l:
            st.markdown("**Transaction Details**")
            st.markdown(
                f"""<div style="{card_style}">
  <div style="{row_style}"><span style="{label_style}">Key</span><span style="{value_style}">{selected_with_quarter.get('transaction_key', '—')}</span></div>
  <div style="{row_style}"><span style="{label_style}">Date</span><span style="{value_style}">{selected_with_quarter.get('transaction_date', '—')}</span></div>
  <div style="{row_style}"><span style="{label_style}">Address</span><span style="{value_style}">{selected_with_quarter.get('address', '—')}</span></div>
  <div style="{row_style}"><span style="{label_style}">Arrondissement</span><span style="{value_style}">{ordinal(arr_val) if pd.notna(arr_val) else '—'}</span></div>
  <div style="{row_style}"><span style="{label_style}">Property type</span><span style="{value_style}">{selected_with_quarter.get('property_type', '—')}</span></div>
  <div style="{row_style}"><span style="{label_style}">Surface area</span><span style="{value_style}">{f"{selected_with_quarter['surface_area']:.1f} m²" if pd.notna(selected_with_quarter.get('surface_area')) else '—'}</span></div>
  <div style="{row_style}"><span style="{label_style}">Rooms</span><span style="{value_style}">{int(selected_with_quarter['room_count']) if pd.notna(selected_with_quarter.get('room_count')) else '—'}</span></div>
  <div style="{row_style}"><span style="{label_style}">Property value</span><span style="{value_style}">{f"€{selected_with_quarter['property_value']:,.0f}" if pd.notna(selected_with_quarter.get('property_value')) else '—'}</span></div>
  <div style="{row_style}"><span style="{label_style}">Price / m²</span><span style="{value_style}">{f"€{selected_with_quarter['price_per_sqm']:,.0f}" if pd.notna(selected_with_quarter.get('price_per_sqm')) else '—'}</span></div>
  <div style="display:flex; justify-content:space-between; padding:5px 0; font-size:13.5px;"><span style="{label_style}">Data quality</span><span style="background:{flag_badge_bg}; color:{flag_badge_txt}; font-size:12px; font-weight:500; padding:2px 10px; border-radius:12px;">{format_quality_label(flag)}</span></div>
</div>""",
                unsafe_allow_html=True,
            )

        with col_r:
            if rent_row is not None:
                quarter_name = selected_with_quarter.get("quarter_name", rent_row.get("quarter_name", "—"))
                ref  = rent_row["reference_rent"]
                rmin = rent_row["min_rent"]
                rmax = rent_row["max_rent"]
                implied = f"€{ref * selected_with_quarter['surface_area']:,.0f} / month" if pd.notna(selected_with_quarter.get("surface_area")) else None
                implied_html = f'''<div style="margin-top:12px; background:#eff6ff; border-radius:6px; padding:10px 12px; font-size:13px; color:#1e40af;">Implied monthly rent at reference: <strong>{implied}</strong></div>''' if implied else ""
                st.markdown(f"**Rent Control · {room_label}**")
                st.markdown(
                    f"""<div style="{card_style}">
  <div style="{row_style}"><span style="{label_style}">Quarter</span><span style="{value_style}">{quarter_name}</span></div>
  <div style="{row_style}"><span style="{label_style}">Min rent</span><span style="{value_style}">€{rmin:.1f} /m²</span></div>
  <div style="{row_style}"><span style="{label_style}">Reference rent</span><span style="{value_style}">€{ref:.1f} /m²</span></div>
  <div style="display:flex; justify-content:space-between; padding:5px 0; font-size:13.5px;"><span style="{label_style}">Max rent</span><span style="{value_style}">€{rmax:.1f} /m²</span></div>
  {implied_html}
</div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.info("No rent-control data available for this location.")

    with col_map:
        st.markdown("**Location**")
        if has_coords:
            lat = float(selected_row["lat"])
            lon = float(selected_row["lon"])
            address_label = selected_with_quarter.get("address", "")

            mini_map = folium.Map(
                location=[48.8566, 2.3522],
                zoom_start=11,
                tiles="CartoDB positron",
                zoom_control=True,
                scrollWheelZoom=False,
                dragging=True,
                attributionControl=False,
            )


            if arr_geojson:
                folium.GeoJson(
                    arr_geojson,
                    name="Arrondissements",
                    style_function=lambda x: {
                        "fillColor": "transparent",
                        "color": "#888888",
                        "weight": 1.2,
                        "fillOpacity": 0,
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["l_aroff"],
                        aliases=[""],
                        style=(
                            "background-color: white;"
                            "border: 1px solid #ccc;"
                            "border-radius: 4px;"
                            "font-family: sans-serif;"
                            "font-size: 12px;"
                            "padding: 4px 8px;"
                        ),
                        sticky=False,
                    ),
                ).add_to(mini_map)

            folium.CircleMarker(
                location=[lat, lon],
                radius=9,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color="#1565C0",
                fill_opacity=1,
                tooltip=address_label,
            ).add_to(mini_map)

            st_folium(mini_map, width="100%", height=440, returned_objects=[])
        else:
            st.info("No coordinates available for this transaction.")
