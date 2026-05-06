import streamlit as st
import pandas as pd
from data_loader import load_dvf, load_rent, load_green, load_planned

st.set_page_config(page_title="Data Sources", page_icon=":globe_with_meridians:", layout="wide")

dvf     = load_dvf()
rent    = load_rent()
green   = load_green()
planned = load_planned()

#  Header 
st.title("Data Sources")
st.markdown("Four public datasets from the French government and the City of Paris · 2025")
st.markdown("---")

#  Source cards 
st.subheader("Datasets")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div style="border:1px solid #F2F2F7; border-radius:8px; padding:16px; margin-bottom:12px; background-color:#F2F2F7">
        <strong>01 · DVF: Demandes de Valeurs Foncières</strong><br>
        <span style="color:#6b7280; font-size:0.85rem;">data.gouv.fr · Updated every 6 months</span><br><br>
        Official French government dataset of all declared real estate transactions.
        Contains sale prices, property types, surface areas, addresses, and cadastral references.
        One row per property lot per transaction, which were aggregated to one row per transaction in pre-processing.<br><br>
        <strong>38,551 transactions · 2025</strong>
        </div>
        """, unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="border:1px solid #D9FADA; border-radius:8px; padding:16px; background-color:#D9FADA">
        <strong>03 · Existing Green Spaces</strong><br>
        <span style="color:#6b7280; font-size:0.85rem;">opendata.paris.fr · Département des Espaces Verts</span><br><br>
        Inventory of all public green spaces in Paris: parks, gardens, promenades, tree pits,
        and planters. Includes polygon geometry, surface area in m², category, and opening year.<br><br>
        <strong>2,509 green spaces</strong>
        </div>
        """, unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div style="border:1px solid #D9E2FA; border-radius:8px; padding:16px; margin-bottom:12px; background-color:#D9E2FA">
        <strong>02 · Rent Control: Encadrement des Loyers</strong><br>
        <span style="color:#6b7280; font-size:0.85rem;">opendata.paris.fr · Updated annually in July</span><br><br>
        Legal rent thresholds per quartier and room count, set by the City of Paris since 2019.
        Contains reference rent, minimum and maximum rent per m² for each of the 80 rent-control zones.<br><br>
        <strong>320 rows · 80 quartiers × 4 room categories</strong>
        </div>
        """, unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="border:1px solid #D9FADA; border-radius:8px; padding:16px; background-color:#D9FADA">
        <strong>04 · Planned Green Spaces</strong><br>
        <span style="color:#6b7280; font-size:0.85rem;">opendata.paris.fr · Département des Espaces Verts</span><br><br>
        Pipeline of planned urban greening projects by arrondissement and sector.
        Contains project names, completion dates, operation types, and planned surface
        additions in m².<br><br>
        <strong>71 planned projects · 2025–2030</strong>
        </div>
        """, unsafe_allow_html=True,
    )

st.markdown("---")

#  Scope 
st.subheader("Scope & Key Decisions")

col_l, col_r = st.columns(2)
with col_l:
    st.markdown("""
**Timeframe:** Analysis is limited to 2025 transactions only.

**Property types for price analysis:** Since rent caps apply only to residential properties,
the main price-per-m² analysis focuses on apartments and houses. Commercial units, outbuildings,
and transactions without a valid residential surface are retained in the dataset for
transparency and quality checks, but excluded from the clean price-per-m² analysis.

**Relevant DVF variables:** transaction date, property value, property type, surface area,
room count, price per m², address, longitude and latitude.
    """)
with col_r:
    st.markdown("""
**Rent control matching:** Paris is divided into 80 quartiers, each assigned to one of 14
rent control zones. Using geographic polygons, each DVF property is matched to its
rent control zone via point-in-polygon spatial join.

**Green space join:** Planned green spaces are joined by arrondissement. Existing green spaces
require a spatial join and remain a point for further modelling.
    """)

st.markdown("---")

# ── Limitations ───────────────────────────────────────────────────────────────
st.subheader("Limitations")
st.markdown(
    """
    <div style="background:#fff8f0; border-left:5px solid #f59e0b; padding:16px 20px; border-radius:6px;">
    <ul style="margin:0; padding-left:18px; color:#1f2937; font-size:0.95rem; line-height:1.8;">
    <li>The DVF dataset does not include the source document ID for each transaction, which necessitated creating a composite primary key based on multiple variables.
    <li>The DVF does not include construction period or furnished/unfurnished status, limiting exact matching to rent-control categories. Rent-control values were averaged across room-count categories to obtain a representative zone-level value for mapping.</li>
    <li>Planned green spaces are only available at arrondissement level, so no street-level spatial join is possible to match directly to a rent control zone.</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ── Data preview ──────────────────────────────────────────────────────────────
st.subheader("Data Preview")

tab1, tab2, tab3, tab4 = st.tabs([
    "DVF Transactions", "Rent Control", "Green Spaces", "Planned Green Spaces"
])

with tab1:
    st.caption(f"{len(dvf):,} rows · {len(dvf.columns)} columns · showing first 10")
    st.dataframe(dvf.head(10), use_container_width=True)

with tab2:
    st.caption(f"{len(rent):,} rows · {len(rent.columns)} columns · showing first 10")
    st.dataframe(rent.head(10), use_container_width=True)

with tab3:
    st.caption(f"{len(green):,} rows · {len(green.columns)} columns · showing first 10")
    st.dataframe(green.head(10), use_container_width=True)

with tab4:
    st.caption(f"{len(planned):,} rows · {len(planned.columns)} columns · showing first 10")
    st.dataframe(planned.head(10), use_container_width=True)
