import streamlit as st
from data_loader import load_dvf, load_rent, load_green, load_planned
from pathlib import Path

st.set_page_config(
    page_title="Paris Real Estate",
    layout="wide",
    page_icon=":information_source:",
)

# ── Load data for KPIs ────────────────────────────────────────────────────────
dvf     = load_dvf()
rent    = load_rent()
green   = load_green()
planned = load_planned()

dvf_clean        = dvf[dvf["data_quality_flag"] == "ok"]
total_transactions = len(dvf_clean)
median_price     = dvf_clean["price_per_sqm"].median()
avg_ref_rent     = rent["reference_rent"].mean()
n_green_spaces   = len(green)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Real Estate in Paris in 2025")

st.markdown("---")

# ── Context ───────────────────────────────────────────────────────────────────

col_left, col_right = st.columns([3, 2])
with col_left:
    st.markdown("\n")
    st.markdown("\n")
    st.markdown("\n")
    st.subheader("Project Context")
    st.markdown("""
Fluctuations in the housing market can have major social, economic, and political impacts.
In recent years, organisations like the World Economic Forum and the European Parliament
have spoken of a wide-sweeping **housing crisis**. 

Rent levels and proximity to green spaces can be indicators of the supply and accessibility 
of affordable housing. **Using Paris's Open Data sources, this project looks 
at relationship between property transaction prices, rent controls, and urban
green space availability across Paris.**
    """)

with col_right:
    ASSETS_DIR = Path(__file__).parent / "assets"
    paris_path = ASSETS_DIR / "paris.jpg"
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    if paris_path.exists():
        st.image(str(paris_path), use_container_width=True)
    else:
        st.warning("Image not found. Place paris.png in the assets/ folder.")
    st.caption("Andreas Weilguny, Unsplash (2025)")
      
    

st.markdown("---")

# ── Objectives ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background:#f0f4ff; border-left:5px solid #3b6fd4; padding:16px 20px; border-radius:6px;">
<strong>Project Objective</strong><br>
<span style="font-size:0.95rem; color:#1f2937;">
Lay the technical foundation for monitoring property values and rent-cap data provided
by the City of Paris, including a robust database schema, an efficient ETL pipeline,
and analytical visualisations tracking key metrics and patterns.
</span>
</div>
""",
unsafe_allow_html=True,
)

st.markdown("---")

# ── Research questions ────────────────────────────────────────────────────────
st.subheader("Research Questions")

q1, q2 = st.columns(2)
with q1:
    st.markdown(
        """
        <div style="background:#f8f9fa; border-radius:8px; padding:14px 18px; margin-bottom:12px;">
        <strong>Property Prices & Rent Control</strong><br>
        How do actual transaction prices per m² compare to the legal rent control values across Paris?
        </div>
        """,
        unsafe_allow_html=True,
    )
with q2:
    st.markdown(
        """
        <div style="background:#f8f9fa; border-radius:8px; padding:14px 18px; margin-bottom:12px;">
        <strong>Property Prices & Green Spaces</strong><br>
        Is there a measurable relationship between green-space coverage and property prices
        at the arrondissement level?
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("---")

# ── Table of Contents ─────────────────────────────────────────────
st.subheader("Project Contents")

# Row 1
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div style="
            border:1px solid #f0f4ff;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            background-color:#f0f4ff;
        ">
        <strong style="font-size:1.05rem;">① Introduction</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        Overview of the Paris housing context, project objectives, and key research questions explored in the analysis.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div style="
            border:1px solid #f8f9fa;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            background-color:#f8f9fa;
        ">
        <strong style="font-size:1.05rem;">② Data Sources</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        Presentation of the open datasets used, including DVF transactions, rent-control zones, and green-space datasets.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Row 2
col3, col4 = st.columns(2)

with col3:
    st.markdown(
        """
        <div style="
            border:1px solid #f8f9fa;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            background-color:#f8f9fa;
        ">
        <strong style="font-size:1.05rem;">③ Data Modeling</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        Explanation of the transition from a normalized 3NF schema to an analytical Star Schema model.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
        <div style="
            border:1px solid #f8f9fa;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            background-color:#f8f9fa;
        ">
        <strong style="font-size:1.05rem;">④ ETL Pipeline</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        Description of the extraction, transformation, cleaning, geocoding, and loading workflow used to prepare the datasets.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Row 3
col5, col6 = st.columns(2)

with col5:
    st.markdown(
        """
        <div style="
            border:1px solid #f8f9fa;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            background-color:#f8f9fa;
        ">
        <strong style="font-size:1.05rem;">⑤ Analysis</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        Interactive analysis pages exploring rent control, green spaces, and integrated geospatial visualisations of Paris.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col6:
    st.markdown(
        """
        <div style="
            border:1px solid #f8f9fa;
            border-radius:10px;
            padding:22px;
            margin-bottom:20px;
            line-height:1.6;
            background-color:#f8f9fa;
        ">
        <strong style="font-size:1.05rem;">⑥ Conclusion</strong><br>

        <div style="color:#6b7280; font-size:0.95rem; margin-top:12px;">
        Final discussion of the project's findings, limitations, technical challenges, and future improvements.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("---")
st.caption("Paris Real Estate • Stefania Licciardi • Victoria Ford • Andrés Lill • May 2026")
