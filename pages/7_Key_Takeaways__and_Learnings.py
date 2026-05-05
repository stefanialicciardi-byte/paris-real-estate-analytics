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
    page_title="Key Takeaways and Lessons Learned",
    page_icon=":bulb:",
    layout="wide",
)

# -------------------------
# Header
# -------------------------
st.title("Key Takeaways and Learnings")
st.caption(
    "In this final section, we summarize our key analytical findings and lessons learned from the project."
)

# -------------------------
#  Conclusions of the analysis
# -------------------------
st.header("Key Takeaways from the Data")
st.markdown("...")

# -------------------------
#  Assessment of goal achievement
# -------------------------
st.header("Did we achieve our project objectives?")
st.markdown("""
We laid the technical foundation for monitoring property values and rent control data, achieving most of our objectives:   
:white_check_mark:    A robust database schema
:white_check_mark:    Analytical visualisations tracking key metrics and patterns
:toolbox:    An efficient ETL pipeline...
""")

# -------------------------
#  Challenges and Lessons Learned
# -------------------------
st.header("Challenges and Lessons Learned")
st.markdown("""

**Manual Uploads Slow Pipeline and Increase Risk of Error**	
:question:    The main weakness of our ETL pipeline is the manual uploads involved at multiple steps in the pipeline. 
:white_check_mark:    To ensure consistency, there are checkpoints along the way were necessary data uploads are flagged.
:bulb:    Looking forward, one solution would be to integrate the entire pipeline into Snowflake (which was not possible with a trial account).

**Joining Geographic Data**
:question:    One significant challenge we faced is how to integrate geographic data into our schema. Since the relationships between variables are spacial, a traditional primary key / foreign key relationship isn't applicable.
:white_check_mark:     Since the scope of our project didn't require a full geospatial schema, our hybrid star model sufficed.
:bulb:    Looking forward, 

""")
