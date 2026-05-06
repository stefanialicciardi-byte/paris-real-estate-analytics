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
st.info("""
* **The most expensive arrondissements don't necessarily have more green spaces**: This suggests that location and centrality are stronger price drivers, while green spaces provide useful additional context.
* **High property prices follow high reference rent values when accounding for room number**: The high demand, short supply of small, 1-room units in the city translates to higher prices in both the sale and rental markets.   
* **Owners hold smaller properties in popular areas**: Properties with higher reference rents tend to have lower transaction volumes. In the case of 1-room properties, this may reflect a preference for holding onto smaller units rather than selling them.
""")

# -------------------------
#  Challenges and Lessons Learned
# -------------------------
st.markdown("---") 

st.header("Challenges and solutions looking forward")

# Add spacing under header
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------
# Reusable card component
# -------------------------

def render_card(title: str, paragraphs: list[str]):

    # Escape content to avoid breaking HTML
    content_html = "".join([
        f"<p>{html.escape(p)}</p>" for p in paragraphs
    ])

    st.markdown(
        f"""
        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        ">
            <strong style="font-size:1.05rem;">{title}</strong>

            <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
                {content_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------
# Layout (2x2 grid)
# -------------------------
r1c1, r1c2 = st.columns(2, gap="large")
r2c1, r2c2 = st.columns(2, gap="large")

# -------------------------
# Row 1 - Card
# -------------------------
with r1c1:
    render_card(
        "Manual steps slow pipeline and increase error risk",
        [
            "🛠 The main weakness of our ETL pipeline is the manual uploads involved at multiple steps in the pipeline.",
            "✅ To ensure consistency, there are checkpoints along the way where necessary data uploads are flagged.",
            "💡 Looking forward, one solution would be to integrate the entire pipeline into Snowflake (which was not possible with a trial account)."
        ]
    )

# -------------------------
# Row 1 - Image
# -------------------------
with r1c2:
    ASSETS_DIR = Path(__file__).parent.parent / "assets"
    etl_path = ASSETS_DIR / "ETL.png"

    # Add spacing above image for alignment
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    if etl_path.exists():
        st.image(str(etl_path), use_container_width=True)
    else:
        st.warning("Image not found. Place ETL.png in the assets/ folder.")

# -------------------------
# Add space between rows
# -------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<b>Hello</b>", unsafe_allow_html=True)
# -------------------------
# Row 2 - Card
# -------------------------
with r2c1:
    render_card(
        "Joining Geographic Data",
        [
            "🛠 One significant challenge we faced is how to integrate geographic data into our schema. Since the relationships between variables are spacial, a traditional primary key / foreign key relationship isn't applicable.",
            "✅ Since the scope of our project didn't require a full geospatial schema, our simplified hybrid star model sufficed.",
            "💡 To further develop the geospatial layer, one could create a non-relational database for the geospatial table elements. Along with other providers, Snowflake also supports storing and querying geospatial formats."
        ]
    )

# -------------------------
# Row 2 - Image
# -------------------------
with r2c2:
    geo_path = ASSETS_DIR / "geo.webp"

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    if geo_path.exists():
        st.image(str(geo_path), use_container_width=True)
    else:
        st.warning("Image not found. Place geo.png in the assets/ folder.")
