# -------------------------
# Import libraries
# -------------------------
import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import plotly.io as pio
from pathlib import Path

from data_loader import load_dvf, load_rent

# -------------------------
# Global plot style
# -------------------------
pio.templates.default = "plotly_white"

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Conclusion",
    page_icon=":bulb:",
    layout="wide",
)

# -------------------------
# Header
# -------------------------
st.title("Conclusion")
st.caption(
    "In this final section, we summarize our key analytical findings and lessons learned from the project."
)

# -------------------------
#  Conclusions of the analysis
# -------------------------
st.markdown("---") 
st.header("Key findings from the data")

col1, col2 = st.columns(2)
# First column with insights--------------
with col2:
    st.markdown(
        """
        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
        ">

        <!-- Insight 1 -->
        <div style="margin-bottom:20px;">
            <strong style="font-size:1.05rem;">High reference rent values follow high property prices</strong>
            <div style="color:#6b7280; font-size:0.95rem; margin-top:8px;">
                The high demand, short supply of small, centrally located units translates to higher prices in both the sale and rental markets.
            </div>
        </div>

        <!-- Insight 2 -->
        <div style="margin-bottom:20px;">
            <strong style="font-size:1.05rem;">Low market liquidity in central areas</strong>
            <div style="color:#6b7280; font-size:0.95rem; margin-top:8px;">
                Low market liquidity central areas: High reference rent zones tend to have lower transaction volumes. 
                In the case of 1-room properties, this may reflect an owner's preference for holding onto smaller, centrally located units.
            </div>
        </div>

        <!-- Insight 3 -->
        <div>
            <strong style="font-size:1.05rem;">The most expensive living areas aren't the most green</strong>
            <div style="color:#6b7280; font-size:0.95rem; margin-top:8px;">
                Location and centrality are stronger price drivers, while green spaces provide useful additional context.
            </div>
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
# Second column with image -------------------  
with col1:
    ASSETS_DIR = Path(__file__).parent.parent / "assets"
    map_path = ASSETS_DIR / "map.png"

    # Add spacing above image
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    if map_path.exists():
        st.image(str(map_path), use_container_width=True)
    else:
        st.warning("Image not found. Place map.png in the assets/ folder.")



# -------------------------
#  Challenges and Lessons Learned
# -------------------------
st.markdown("---") 

st.header("Challenges and solutions looking forward")

# Add space under header
st.markdown("<br>", unsafe_allow_html=True)

# Create columns with gap
r1c1, r1c2 = st.columns(2, gap="large")
r2c1, r2c2 = st.columns(2, gap="large")

with r1c1:
    st.markdown(
        """
        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
        ">
        <strong style="font-size:1.05rem;">Manual steps slow pipeline and increase error risk</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        <p>🛠  The main weakness of our ETL pipeline is the manual uploads involved at multiple steps in the pipeline.</p>
        <p>✅  To ensure consistency, there are checkpoints along the way where necessary data uploads are flagged.</p>
        <p>💡  Looking forward, one solution would be to integrate the entire pipeline into Snowflake (which was not possible with a trial account).</p>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r1c2:
    ASSETS_DIR = Path(__file__).parent.parent / "assets"
    etl_path = ASSETS_DIR / "ETL.png"

    # Add spacing above image
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    if etl_path.exists():
        st.image(str(etl_path), use_container_width=True)
    else:
        st.warning("Image not found. Place ETL.png in the assets/ folder.")

# Add space between rows
st.markdown("<br><br>", unsafe_allow_html=True)

with r2c1:
    st.markdown(
        """
        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
        ">
        <strong style="font-size:1.05rem;">Managing geospacial data</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        <p>🛠  One significant challenge we faced is how to integrate geographic data into our schema. Since the relationships between variables are spacial, a traditional primary key / foreign key relationship isn't applicable.</p>
        <p>✅  Since the scope of our project didn't require a full geospatial schema, our simplified hybrid star model sufficed.</p>
        <p>💡  To further develop the geospatial layer, one could create a non-relational database for the geospatial table elements. Along with tools like PostGIS or MongoDB, Snowflake also supports storing and querying geospatial formats.</p>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r2c2:
    geo_path = ASSETS_DIR / "geo.webp"

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    if geo_path.exists():
        st.image(str(geo_path), use_container_width=True)
    else:
        st.warning("Image not found. Place geo.png in the assets/ folder.")
