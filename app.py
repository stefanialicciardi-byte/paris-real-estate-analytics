import streamlit as st
from data_loader import load_dvf, load_rent, load_green, load_planned
from pathlib import Path

st.set_page_config(
    page_title="Paris Real Estate",
    layout="wide",
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
st.title("Real Estate in Paris 2025")

st.markdown("---")

# ── Context ───────────────────────────────────────────────────────────────────
st.subheader("Project Context")

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("""
Fluctuations in the housing market can have major social, economic, and political impacts.
In recent years, organisations like the World Economic Forum and the European Parliament
have spoken of a wide-sweeping **housing crisis**. Leading up to Paris's mayoral election
in March 2026, France24 reported that the *"capital's housing crisis could determine the
city's next mayor."*

Historically, rent caps have been one intervention for ensuring fair access to affordable
housing. In Paris, they were reinstated most recently in 2019. Additionally, Paris joins other big 
cities that are investing in infrastructure that enhances quality of life, particularly 
by expanding and improving access to urban green spaces. **Using Paris's Open Data sources,
this project looks at relationship between property transaction prices, rent controls, and urban
green-space availability across Paris.**
    """)

with col_right:
    ASSETS_DIR = Path(__file__).parent.parent / "assets"
    paris_path = ASSETS_DIR / "paris.png"

    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    if paris_path.exists():
        st.image(str(paris_path), use_container_width=True)
    else:
        st.warning("Image not found. Place paris.png in the assets/ folder.")
    st.caption("Free image by Andreas Weilguny accessed via Unsplash (2025)")
      
    

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
        <strong>Price vs. Rent Control</strong><br>
        How do actual transaction prices per m² compare to the legal rent control values across Paris?
        </div>
        """,
        unsafe_allow_html=True,
    )
with q2:
    st.markdown(
        """
        <div style="background:#f8f9fa; border-radius:8px; padding:14px 18px; margin-bottom:12px;">
        <strong>Green Space & Property Values</strong><br>
        Is there a measurable relationship between green-space coverage and property prices
        at the arrondissement level?
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("---")
st.caption("Paris Real Estate • Stefania Licciardi • Victoria Ford • Andrés Lill • May 2026")
