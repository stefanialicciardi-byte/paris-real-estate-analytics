import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Data Modeling", page_icon=":hammer_and_wrench:", layout="wide")

ASSETS_DIR = Path(__file__).parent.parent / "assets"

#  Header 
st.title("Data Modeling")
st.markdown("From Third Normal Form to Star Schema: Design decisions and trade-offs")
st.markdown("---")

# -------------------------
#  Core finding 
# -------------------------
st.markdown(
    """
    <div style="background:#f0f4ff; border-left:5px solid #3b6fd4; padding:16px 20px; border-radius:6px; margin-bottom:24px;">
    <strong>Design Decision</strong><br>
    <span style="font-size:0.97rem; color:#1f2937;">
    We initially built a full 3NF Snowflake Schema, then moved to a Star Schema for analytical usability.
    The central fact table is <strong>FACT_TRANSACTION</strong>, surrounded by five dimension tables.
    </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "① Third Normal Form (3NF)",
    "② Star Schema (Denormalization)",
    "③ Star Schema Diagram & Table Descriptions",
    "④ Data Quality Flags"
])

# -------------------------
# TAB 1 — 3NF
# -------------------------
with tab1:
    st.subheader("Step 1: Third Normal Form (3NF)")
    st.markdown("""
    In the first stage, we structured the data into a 3NF model to organise the different source datasets
    in a clear, consistent, and logically separated way. This step helped us:

    - Reduce redundancy and preserve the original granularity of each dataset
    - Define the relationships between main entities: property transactions, rent control records,
      existing green spaces, planned green-space projects, addresses, property types, and geographic areas
    - Understand how the datasets were connected before moving to denormalization

    The 3NF model gave us a strong relational foundation (11 tables total) but required complex
    multi-step joins for any analytical query.
    """)

# -------------------------
# TAB 2 — Star Schema
# -------------------------
with tab2:
    st.subheader("Step 2: Star Schema (Denormalization)")
    st.markdown("""
    We moved from the 3NF model to a Star Schema mainly because it is easier to query and better
    suited for analytical use. The normalized structure would have required chained joins across
    many tables. The Star Schema simplified this by centering the model around **FACT_TRANSACTION**,
    with surrounding dimensions for date, location, arrondissement, property type, and rent-control context.

    **Key benefits:**
    - Simple joins 
    - Faster aggregations in SQL and BI tools
    - More intuitive for the whole team to read and write queries

    **Key trade-off:**
    Green spaces cannot be connected to transactions through a simple key relationship — their
    integration depends on spatial logic (PostGIS / point-in-polygon) and remains a point for
    further modelling. As a pragmatic solution, green-space metrics are aggregated at arrondissement
    level and stored directly in **DIM_ARRONDISSEMENT**.
    """)

# -------------------------
# TAB 3 — Schema + Tables
# -------------------------
with tab3:
    # Schema diagram
    st.subheader("Star Schema Diagram")
    st.caption("Diagram includes a spatial layer (dim_green_spaces) for potential future integration.")

    schema_path = ASSETS_DIR / "star_schema.png"
    if schema_path.exists():
        st.image(str(schema_path), use_container_width=True)
    else:
        st.warning("Schema diagram not found. Place star_schema.png in the assets/ folder.")

    st.markdown("---")

    # Table descriptions
    st.subheader("Table Descriptions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px; margin-bottom:12px;">
            <strong>FACT_TRANSACTION</strong> &nbsp;<span style="color:#6b7280; font-size:0.85rem;">38,551 rows</span><br>
            One row per DVF property transaction. Contains all foreign keys to dimensions plus
            the core measures: property_value, surface_area, price_per_sqm, room_count,
            match_score, and data_quality_flag.
            </div>

            <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px; margin-bottom:12px;">
            <strong>DIM_DATE</strong><br>
            One row per unique transaction date. Splits the date into year, month, quarter,
            week, day, day_of_week, day_name, and is_weekend for time-based filtering.
            </div>

            <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px;">
            <strong>DIM_LOCATION</strong><br>
            One row per unique street. Contains street code, name, type, postal code,
            full address, latitude, longitude, and geocoding metadata.
            Originally named DIM_STREET — renamed because it contains more than street info.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px; margin-bottom:12px;">
            <strong>DIM_ARRONDISSEMENT</strong><br>
            One row per arrondissement. Acts as the analytical spine connecting all four
            source datasets. Stores aggregated green-space metrics (count, total area, planned
            projects) to avoid a spatial join at query time.
            </div>

            <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px; margin-bottom:12px;">
            <strong>DIM_QUARTER</strong><br>
            One row per rent-control quartier. Contains zone_id, quarter_name, and the
            aggregated rent thresholds: avg_reference_rent, rent_band_min, rent_band_max.
            </div>

            <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px;">
            <strong>DIM_PROPERTY_TYPE</strong><br>
            Small lookup table for the four property types in DVF: Apartment, House,
            Industrial/Commercial, and Outbuilding.
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------------
# TAB 4 — Data Quality
# -------------------------
with tab4:
    st.subheader("Data Quality Flags")
    st.markdown("""
    A `data_quality_flag` column in FACT_TRANSACTION marks suspicious records.
    These rows are **not deleted** and remain available for inspection, while
    clean analyses filter to `flag = 'ok'`.
    """)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ok (clean)", "37,720", "97.8% retained", delta_arrow="off")
    col2.metric("price_per_sqm_high", "537", "Likely institutional", delta_color="off", delta_arrow="off")
    col3.metric("surface_too_small", "196", "< 9 m²: likely parking", delta_color="off", delta_arrow="off")
    col4.metric("high_room_count", "98", "> 20 rooms: likely building", delta_color="off", delta_arrow="off")
