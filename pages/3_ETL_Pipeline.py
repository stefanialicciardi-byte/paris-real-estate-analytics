import streamlit as st
from pathlib import Path

st.set_page_config(page_title="ETL Pipeline", page_icon="⚙️", layout="wide")

# Header
st.title("ETL / ELT Pipeline")
st.markdown("From raw open data to an analytics-ready Star Schema in Snowflake")
st.markdown("---")

# Pipeline overview image
st.subheader("Pipeline Overview")
pipeline_img = Path("assets/pipeline_overview.png")
if pipeline_img.exists():
    st.image(str(pipeline_img), use_container_width=True)
else:
    st.warning("Pipeline overview image not found. Expected: assets/pipeline_overview.png")

st.markdown("---")

# Pipeline steps
st.subheader("Pipeline Steps")

tab1, tab2, tab3, tab4 = st.tabs([
    "① Extract", "② Transform", "③ Load to Snowflake", "④ Populate Star Schema"
])

with tab1:
    st.markdown("### Data Extraction")
    st.markdown("""
DVF transaction data was downloaded directly from **data.gouv.fr** as a CSV file
for département 75 (Paris). Rent control, green spaces, and planned green spaces
were retrieved via the **opendata.paris.fr API** using Python requests in Google Colab.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**DVF: direct CSV download**")
        with st.expander("Show code"):
            st.code("""import pandas as pd

# DVF data from data.gouv.fr
url = (
    "https://files.data.gouv.fr/geo-dvf/"
    "latest/csv/2025/departements/75.csv"
)
df = pd.read_csv(url)

# Keep only Paris postal codes
df = df[df['code_postal'].between(75001, 75020)]
print(f"Loaded: {len(df):,} rows")""", language="python")

    with col2:
        st.markdown("**Rent Control: API pagination**")
        with st.expander("Show code"):
            st.code("""import requests

base = "https://opendata.paris.fr/api/explore/v2.1"
url  = f"{base}/catalog/datasets/encadrement-loyers-paris/records"
params = {"limit": 100, "offset": 0}

records = []
while True:
    r = requests.get(url, params=params).json()
    records.extend(r["results"])
    if len(r["results"]) < 100:
        break
    params["offset"] += 100

df_rent = pd.DataFrame(records)""", language="python")

with tab2:
    st.markdown("### DVF Transformation: Key Steps")
    st.markdown("""
The main transformation aggregates DVF from **multiple lot rows per transaction**
to **one row per transaction**, geocodes addresses via the Géoplateforme API,
computes price per m², and applies data quality flags.
    """)

    st.markdown("""
**Steps applied in sequence:**

1. **Deduplicate and build composite transaction key** — construct a unique key from year, date, commune, section, plot number, and transaction number
2. **Sort by property type priority** — Apartment first, so the primary type survives aggregation
3. **Aggregate to 1 row per transaction** — `groupby` on the composite key, take first value per field
4. **Sum surface area + room count** — residential lots only (Apartment / House), summed separately and merged back
5. **Apply data quality flags** — flag records with price/m² > 30,000, surface area < 9 m², or room count > 20
    """)

    with st.expander("Show transformation code"):
        st.code("""# Step 1: Deduplicate and build composite transaction key
COMPOSITE_KEY = [
    'year', 'transaction_date', 'commune_code',
    'section', 'plot_number', 'transaction_number'
]
df['transaction_key'] = (
    df['year'].astype(str) + '_' + df['transaction_date'].astype(str) + '_' +
    df['commune_code'].astype(str) + '_' + df['section'].astype(str) + '_' +
    df['plot_number'].astype(str) + '_' + df['transaction_number'].astype(str)
)

# Step 2: Sort by property type priority (Apartment first)
TYPE_PRIORITY = {'Apartment': 0, 'House': 1, 'Industrial...': 2, 'Outbuilding': 3}
df['_type_rank'] = df['property_type'].map(TYPE_PRIORITY).fillna(99)
df = df.sort_values(COMPOSITE_KEY + ['_type_rank'])

# Step 3: Aggregate: 1 row per transaction
main_agg = df.groupby(COMPOSITE_KEY, as_index=False).agg(
    transaction_key = ('transaction_key', 'first'),
    property_value  = ('property_value',  'first'),
    property_type   = ('property_type',   'first'),
    # ... + 12 more columns
)

# Step 4: Sum surface area + room count for residential lots only
res_agg = df[df['property_type'].isin(['Apartment','House'])].groupby(
    COMPOSITE_KEY, as_index=False
).agg(
    surface_area = ('surface_area', 'sum'),
    room_count   = ('room_count',   'sum'),
)
df_transactions = main_agg.merge(res_agg, on=COMPOSITE_KEY, how='left')

# Step 5: Data quality flags
df_transactions['data_quality_flag'] = 'ok'
df_transactions.loc[df_transactions['price_per_sqm'] > 30_000,
                    'data_quality_flag'] = 'price_per_sqm_high'
df_transactions.loc[df_transactions['surface_area'] < 9,
                    'data_quality_flag'] = 'surface_too_small'
df_transactions.loc[df_transactions['room_count'] > 20,
                    'data_quality_flag'] = 'high_room_count'""", language="python")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Raw rows (2024 + 2025)",          "150,729")
    col2.metric("After deduplication",       "128,685", delta="-14.6% of raw",  delta_color="off")
    col3.metric("After aggregation",          "73,443", delta="-51.3% of raw",  delta_color="off")
    col4.metric("After filtering for 2025",  "38,551",  delta="-74.4% of raw",  delta_color="off")

with tab3:
    st.markdown("### Loading Raw Data into Snowflake")
    st.markdown("""
Transformed CSVs are uploaded to a Snowflake internal stage and loaded into
raw tables in the PUBLIC schema via `COPY INTO`.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Stage + file format setup**")
        with st.expander("Show code"):
            st.code("""-- Create internal stage
CREATE STAGE IF NOT EXISTS project_stage
    DIRECTORY = (ENABLE = true);

-- Define CSV file format
CREATE FILE FORMAT CLASSIC_CSV
    TYPE = 'CSV'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('\\\\N');""", language="sql")

    with col2:
        st.markdown("**COPY INTO raw tables**")
        with st.expander("Show code"):
            st.code("""-- Load DVF data
COPY INTO PARIS_REALESTATE.PUBLIC.DVF_AGGREGATED
FROM @PARIS_REALESTATE.STAR.PROJECT_STAGE
     /dvf_paris_2025_aggregated.csv
FILE_FORMAT = CLASSIC_CSV;

-- Load green spaces
COPY INTO PARIS_REALESTATE.PUBLIC.GREEN_SPACES
FROM @PARIS_REALESTATE.STAR.PROJECT_STAGE
     /green_spaces.csv
FILE_FORMAT = CLASSIC_CSV;""", language="sql")

    st.markdown("""
**Files loaded into PUBLIC schema:**
`DVF_AGGREGATED` · `GREEN_SPACES` · `PLANNED_GREEN_SPACES` · `DATE_TABLE`
    """)

with tab4:
    st.markdown("### Populating the Star Schema")
    st.markdown("""
`INSERT ... SELECT` queries transform and load each dimension and fact table from PUBLIC into STAR.
The dimensions are loaded first, then `FACT_TRANSACTION` with FK lookups.
    """)

    with st.expander("Show code: DIM_ARRONDISSEMENT example"):
        st.code("""-- DIM_ARRONDISSEMENT: aggregate green space metrics on the fly
INSERT INTO PARIS_REALESTATE.STAR.DIM_ARRONDISSEMENT (
    arrondissement_id, arrondissement_number, arrondissement_name,
    green_space_count, total_green_area_m2, planned_projects, total_added_green_m2
)
WITH arrondissements AS (
    SELECT DISTINCT POSTAL_CODE AS arrondissement_id
    FROM PARIS_REALESTATE.PUBLIC.DVF_AGGREGATED
),
gs_agg AS (
    SELECT POSTAL_CODE,
           COUNT(*)         AS green_space_count,
           SUM(POLYGON_AREA) AS total_green_area_m2
    FROM PARIS_REALESTATE.PUBLIC.GREEN_SPACES
    GROUP BY POSTAL_CODE
),
pgs_agg AS (
    SELECT ARRONDISSEMENT + 75000 AS arrondissement_id,
           COUNT(*)               AS planned_projects,
           SUM(ADDED_SPACE_INDICATOR) AS total_added_green_m2
    FROM PARIS_REALESTATE.PUBLIC.PLANNED_GREEN_SPACES
    GROUP BY ARRONDISSEMENT
)
SELECT a.arrondissement_id, MOD(a.arrondissement_id, 100),
       CONCAT(MOD(a.arrondissement_id, 100)::VARCHAR, 'e arrondissement'),
       gs.green_space_count, gs.total_green_area_m2,
       pgs.planned_projects, pgs.total_added_green_m2
FROM arrondissements a
LEFT JOIN gs_agg  gs  ON gs.arrondissement_id  = a.arrondissement_id
LEFT JOIN pgs_agg pgs ON pgs.arrondissement_id = a.arrondissement_id;""", language="sql")

    st.markdown("---")

# Implementation Summary
st.subheader("Implementation Summary")

summary_img = Path("assets/implementation_summary.png")
if summary_img.exists():
    st.image(str(summary_img), use_container_width=True)
else:
    st.warning("Implementation summary image not found. Expected: assets/implementation_summary.png")
