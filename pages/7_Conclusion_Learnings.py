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
st.header("Assessment of Goal Achievement")
st.markdown("...")

# -------------------------
#  Lessons learned and future directions
# -------------------------
st.header("Lessons Learned and Future Directions")
st.markdown("...")