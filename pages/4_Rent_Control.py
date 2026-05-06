# -------------------------
# Import libraries
# -------------------------
import streamlit as st
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import shape
import plotly.express as px
import plotly.io as pio
from data_loader import load_dvf, load_rent

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Rent Control Analysis",
    page_icon="📊",
    layout="wide",
)

# -------------------------
# Global plot style
# -------------------------
pio.templates.default = "plotly_white"

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Rent Control Analysis",
    page_icon="📊",
    layout="wide",
)

# -------------------------
# Header
# -------------------------
st.title("Rent Control Analysis")
st.caption(
    "This page dives deeper into the relationship between property transaction data and rent controls in Paris in 2025. "
    "The *quartiers* of Paris are assigned to one of the city's 14 rent control zones. Properties are located within one of these zones using a spatial point-in-polygon join."
)


# -------------------------
# Sidebar filter
# -------------------------
with st.sidebar:
    st.markdown("## Filters")
    st.markdown("---")
    st.markdown("### Number of Rooms")

    room_label = st.radio(
        "Number of rooms",
        options=["All", "1 room", "2 rooms", "3 rooms", "4+ rooms"],
        index=0,
        label_visibility="collapsed"
    )

    room_map = {
        "1 room": 1,
        "2 rooms": 2,
        "3 rooms": 3,
        "4+ rooms": 4
    }

st.caption(f"Filter applied: {room_label}")
st.markdown("---")

# -------------------------
# Load data
# -------------------------
dvf_raw = load_dvf()
rent_raw = load_rent()


# -------------------------
# STEP 1: Clean DVF FIRST
# -------------------------
dvf = dvf_raw[
    (dvf_raw["data_quality_flag"] == "ok") &
    (dvf_raw["price_per_sqm"].notna()) &
    (dvf_raw["lat"].notna()) &
    (dvf_raw["lon"].notna())
].copy()


# -------------------------
# STEP 2: Apply filter BEFORE any aggregation or spatial logic
# -------------------------
if room_label != "All":
    selected_room = room_map[room_label]

    if selected_room < 4:
        dvf = dvf[dvf["room_count"] == selected_room]
    else:
        dvf = dvf[dvf["room_count"] >= 4]


# -------------------------
# STEP 3: Convert to GeoDataFrame AFTER filtering
# -------------------------
dvf_gdf = gpd.GeoDataFrame(
    dvf,
    geometry=gpd.points_from_xy(dvf["lon"], dvf["lat"]),
    crs="EPSG:4326"
)

# -------------------------
# STEP 4: Prepare rent polygons
# -------------------------
rent_unique = rent_raw.drop_duplicates("quarter_id").copy()

geoms = [
    shape(json.loads(row["geo_shape"])["geometry"])
    for _, row in rent_unique.iterrows()
]

rent_gdf = gpd.GeoDataFrame(
    rent_unique,
    geometry=geoms,
    crs="EPSG:4326"
)

# -------------------------
# STEP 5: Spatial join (NO underscore → ensures cache updates properly)
# -------------------------

def spatial_join(dvf_gdf, rent_gdf):
    return gpd.sjoin(
        dvf_gdf,
        rent_gdf[["quarter_id", "geometry"]],
        how="inner",
        predicate="within"
    )

joined = spatial_join(dvf_gdf, rent_gdf)

# -------------------------
# STEP 6: Aggregate AFTER filtering + join
# -------------------------
dvf_grouped = (
    joined.groupby(["quarter_id", "room_count"])
    .agg(
        median_price=("price_per_sqm", "median"),
        n_tx=("price_per_sqm", "count")
    )
    .reset_index()
)

# -------------------------
# STEP 7: Merge with rent data
# -------------------------
df = pd.merge(rent_raw, dvf_grouped, on=["quarter_id", "room_count"], how="inner")
df = df.dropna(subset=["reference_rent", "median_price"])

# -------------------------
# KPI row & Data Preview
# -------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Zones analyzed", len(rent_raw['zone_id'].unique()))
c2.metric("Min. rent (€/m²)", f"{rent_raw["min_rent"].min():.2f}")
c3.metric("Median reference rent (€/m²)", f"{rent_raw['reference_rent'].median():.2f}")
c4.metric("Max. rent (€/m²)", f"{rent_raw["max_rent"].max():.2f}")

st.markdown("---")

# -------------------------
# Basic bar chart, median rent control levels relate to room count
# -------------------------

st.header("Is reference rent higher for properties with more rooms?")
st.caption("Contrary to our expecations, median reference rent is **highest for 1-room properties**, and decreases as room count increases.")


# group rent_raw by room count, calculating median reference rent
rent_by_room = (
    rent_raw.groupby("room_count").agg(median_rent=("reference_rent", "median")).reset_index()
)

# Plotly bar chart of reference rent by room count
fig0 = px.bar(
    rent_by_room,
    x="room_count",
    y="median_rent",
    labels={'room_count': 'Number of Rooms', 'median_rent': 'Reference Rent (€/m²)'},
)

# Plot barchart
st.plotly_chart(fig0, width='content')

# Update hover template (tooltoip) to show all info
fig0.update_traces(
    hovertemplate=
    "<b>Number of rooms:</b> %{x}<br>" +
    "<b>Median Reference Rent:</b> %{y:.2f} €/m²<br>" +
    "<extra></extra>")

# -----------------------
# Scatter plot
# -----------------------

st.header("How do median transaction prices per m² compare to reference rent values?")
st.caption("""
Each point represents the median reference rent by quarter and room count, sized by the number of transactions. The color gradient indicates median price levels. Filtering for a specific **number of rooms** more clearly shows the relationship between the two variables.
""")

# Create figure
fig1 = px.scatter(
    df,
    x="reference_rent",
    y="median_price",
    size="n_tx",
    color="zone_id",
    labels={'reference_rent': 'Reference Rent (€/m²)', 'median_price': 'Median Price (€/m²)', 'n_tx': 'Number of Transactions'},
    color_continuous_scale="Viridis"   
)    

# Update hover template (tooltoip) to show all info
fig1.update_traces(
    hovertemplate=
    "<b>Zone:</b> %{marker.color}<br>" +
    "<b>Transactions:</b> %{marker.size:,.0f}<br>" +
    "<b>Median Price:</b> %{y:.2f} €/m²<br>" +
    "<b>Reference Rent:</b> %{x:.2f} €/m²<br>" +
    "<extra></extra>")

# Update colorscale
fig1.update_layout(
    coloraxis_colorbar=dict(
        title="Zone"
    )
)

st.plotly_chart(fig1, use_container_width=True)

# -------------------------
# Boxplot 
# -------------------------

# Add question header
st.header("How do property prices vary across rent control levels?")
st.caption("Here, median prices are categorized into quartiles based on their reference rent values. As with the previous plot, defining the room type shows a clearer relationship between property price and rent control level.")

df["rent_bin"] = pd.qcut(
    df["reference_rent"],
    q=4,
    labels=["Low", "Mid-Low", "Mid-High", "High"]
)

fig2 = px.box(
    df,
    x="rent_bin",
    y="median_price",
    color="rent_bin",
    labels={'rent_bin': 'Reference Rent Category', 'median_price': 'Median Price (€/m²)'}
)

fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)


# -------------------------
# Barchart -  Relationship between rent control and no. transactions
# -------------------------

st.header("Do zones with higher rent caps have more transactions?")
st.caption("Although there is no clear-cut pattern, zones with higher reference rents (e.g. Zone 1) tend to have fewer transactions, while zones with lower reference rents show more transactions.")

# Group df by zone_id, counting transactions and averaging reference rent
tx_df = df.groupby("zone_id").agg(
    n_tx=("n_tx", "sum"),
    reference_rent=("reference_rent", "mean")
).reset_index()

# Sort by transaction count
tx_df["zone_id"] = tx_df["zone_id"].astype(str)
tx_df = tx_df.sort_values("n_tx", ascending=False)

# Bar chart of transactions by zone, colored by reference rent
fig4 = px.bar(
    tx_df,
    x="zone_id",
    y="n_tx",
    color="reference_rent",
    category_orders={"zone_id": tx_df["zone_id"].tolist()},
    labels={'zone_id': 'Zone', 'n_tx': 'Number of Transactions'},
    color_continuous_scale="Blues",
)
# Update colorscale
fig4.update_layout(
    coloraxis_colorbar=dict(
        title="Reference Rent (€/m²)"
    )
)
# Update hover template (tooltoip) to show all info
fig4.update_traces(
    hovertemplate=
    "<b>Zone:</b> %{x}<br>" +
    "<b>Transactions:</b> %{y:,.0f}<br>" +
    "<b>Reference Rent:</b> %{marker.color:.2f} €/m²<br>" +
    "<extra></extra>")

# Remove unneeded legend
fig4.update_layout(showlegend=False)

# Plot figure
st.plotly_chart(fig4, width='content')


# -------------------------
# Insights
# -------------------------
st.markdown("---")

st.header("Observations & Insights")

st.info("""
**Classic case of supply & demand**: Reference rents tend to be higher for 1-room properties, reflecting high demand for small, more affordable units in the city, e.g. for students or tourists.

**Owners hold on to smaller properties in popular areas**: Properties with higher reference rents tend to have lower transaction volumes. In the case of 1-room properties, this may reflect a preference for holding onto smaller units rather than selling them. On the other hand, higher transaction volumes can indicate a more active and liquid real estate market.

**Low reference Rents are connected to low property prices, but other factors count**: 
Overall, we see that we see that lower reference rents are connected to lower property prices, but there is a lot of overlap in property prices across levels. This suggests that factors beyond rent control heavily influence property values (such as location).
""")

st.markdown("---")

st.markdown("**Data Preview**")
st.caption("This table shows a sample of properties with their corresponding rent control information and transaction details.")
st.dataframe(df[['zone_id', 'postal_code', 'quarter_id', 'quarter_name', 'room_count', 'min_rent', 'reference_rent', 'max_rent', 'median_price', 'n_tx']].sort_values(['zone_id', 'quarter_id', 'room_count', 'min_rent'], ascending=True).head(40), width='content', height=200, hide_index=True)

