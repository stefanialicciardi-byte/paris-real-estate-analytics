# -------------------------
# Import libraries
# -------------------------
import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import plotly.io as pio

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

st.header("Challenges and solutions going forward")

r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown(
        """
        <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px;">
        <strong>Manual Uploads Slow Pipeline and Increase Risk of Error</strong><br>
        <span style="color:#6b7280; font-size:0.9rem;">
        
        <p> 🛠  The main weakness of our ETL pipeline is the manual uploads involved at multiple steps in the pipeline. 
        
        <p> ✅  To ensure consistency, there are checkpoints along the way were necessary data uploads are flagged.
        
        <p> 💡  Looking forward, one solution would be to integrate the entire pipeline into Snowflake (which was not possible with a trial account).
        </span>
        </div>
        """, unsafe_allow_html=True,
    )
with r1c2:
    st.markdown(
        """
        <div style="border:1px solid #e5e7eb; border-radius:8px; padding:16px;">
        <strong>Joining Geographic Data</strong><br>
        <span style="color:#6b7280; font-size:0.9rem;">
        
        
        One significant challenge we faced is how to integrate geographic data into our schema. Since the relationships between variables are spacial, a traditional primary key / foreign key relationship isn't applicable.
        
        Since the scope of our project didn't require a full geospatial schema, our hybrid star model sufficed.
        
        Looking forward, if the further development of a geospatial layer is key aspect of the analysis, working with PostgreSQL and PostGIS would be a more suitable option.
        </span>
        </div>
        """, unsafe_allow_html=True,
    )
