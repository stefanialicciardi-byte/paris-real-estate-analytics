# Paris Real Estate 2025 Project

Analytics Engineering project analysing property values, rent control zones, and urban green spaces in Paris.

**Live dashboard:** https://paris-real-estate-ae.streamlit.app/

**Team:** Stefania Licciardi, Victoria Ford, Andrés Lill

---

## Project Overview

This project integrates four public datasets from the French government and the City of Paris into a unified analytics pipeline, ending in an interactive Streamlit dashboard.

The datasets cover property transactions (DVF 2025), rent control thresholds (encadrement des loyers), existing green spaces, and planned urban greening projects across Paris's 20 arrondissements.

---

## Dashboard Pages

**Home**: Project context, research questions, and live KPIs  
**Data Sources**: Four datasets, scope decisions, and limitations  
**Data Modeling**: From 3NF to Star Schema, ER diagram, and design decisions  
**ETL Pipeline**: Extraction, transformation, Snowflake loading, and SQL populate scripts  
**Analysis**: Interactive Folium map of sale prices, rent control zones, and green spaces  

---

## Folder Structure

```
paris-real-estate-ae/
├── app.py                         # Home page
├── data_loader.py                 # Shared data loading functions
├── requirements.txt               # Python dependencies
├── assets/
│   └── star_schema.png            # Star schema diagram
├── data/
│   ├── dvf_paris_2025_aggregated.csv
│   ├── api_rent_control_2025.csv
│   ├── green_spaces.csv
│   └── planned_green_spaces.csv
└── pages/
    ├── 1_Data_Sources.py
    ├── 2_Data_Modeling.py
    ├── 3_ETL_Pipeline.py
    └── 4_Analysis.py
```

---

## Data Sources

| Dataset | Source | Rows |
|---|---|---|
| DVF Transactions 2025 | data.gouv.fr | 38,551 |
| Rent Control 2025 | opendata.paris.fr | 320 |
| Existing Green Spaces | opendata.paris.fr | 2,509 |
| Planned Green Spaces | opendata.paris.fr | 71 |

---

## Tech Stack

Python, Pandas, Streamlit, Folium, GeoPandas, Snowflake, SQL
