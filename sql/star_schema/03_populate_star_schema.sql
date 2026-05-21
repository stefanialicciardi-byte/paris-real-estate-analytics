/*/ Populate the Star Schema Tables with csv files from the project_stage /*/


-- Indicate database and schema 
USE DATABASE PARIS_REALESTATE;
USE SCHEMA STAR;


---------------------
-- Populate tables 
---------------------

-- DIM_DATE
INSERT INTO PARIS_REALESTATE.STAR.dim_date
SELECT *
FROM PARIS_REALESTATE.PUBLIC.date_table;


-- DIM_PROPERTY_TYPE
INSERT INTO PARIS_REALESTATE.STAR.DIM_PROPERTY_TYPE
SELECT DISTINCT property_type_code as PROPERTY_TYPE_CODE, property_type as PROPERTY_TYPE
FROM PARIS_REALESTATE.PUBLIC.DVF_AGGREGATED;

-- DIM_LOCATION
-- One row per unique street (deduplicated by street_code + postal_code).
INSERT INTO PARIS_REALESTATE.STAR.DIM_LOCATION (
    street_code,
    street_name,
    street_type,
    street_number,
    postal_code,
    address,
    latitude,
    longitude,
    matched_address
)
SELECT DISTINCT
    STREET_CODE,
    STREET_NAME,
    STREET_TYPE,
    STREET_NUMBER,
    POSTAL_CODE,
    ADDRESS,
    LAT,
    LON,
    MATCHED_ADDRESS
FROM PARIS_REALESTATE.PUBLIC.DVF_AGGREGATED
WHERE STREET_CODE IS NOT NULL;


-- DIM_ARRONDISSEMENT
-- One row per arrondissement with aggregated green space metrics.
INSERT INTO PARIS_REALESTATE.STAR.DIM_ARRONDISSEMENT (
    arrondissement_id,
    arrondissement_number,
    arrondissement_name,
    green_space_count,
    total_green_area_m2,
    avg_green_space_area,
    planned_projects,
    total_added_green_m2
)
WITH arrondissements AS (
    SELECT DISTINCT POSTAL_CODE AS arrondissement_id
    FROM PARIS_REALESTATE.PUBLIC.DVF_AGGREGATED
    WHERE POSTAL_CODE IS NOT NULL
),
gs_agg AS (
    SELECT
        POSTAL_CODE                     AS arrondissement_id,
        COUNT(*)                        AS green_space_count,
        SUM(POLYGON_AREA)               AS total_green_area_m2,
        AVG(POLYGON_AREA)               AS avg_green_space_area
    FROM PARIS_REALESTATE.PUBLIC.GREEN_SPACES
    GROUP BY POSTAL_CODE
),
pgs_agg AS (
    SELECT
        ARRONDISSEMENT + 75000          AS arrondissement_id,
        COUNT(*)                        AS planned_projects,
        SUM(ADDED_SPACE_INDICATOR)      AS total_added_green_m2
    FROM PARIS_REALESTATE.PUBLIC.PLANNED_GREEN_SPACES
    GROUP BY ARRONDISSEMENT
)
SELECT
    a.arrondissement_id,
    MOD(a.arrondissement_id, 100)       AS arrondissement_number,
    CONCAT(MOD(a.arrondissement_id, 100)::VARCHAR, 'e arrondissement') AS arrondissement_name,
    gs.green_space_count,
    gs.total_green_area_m2,
    gs.avg_green_space_area,
    pgs.planned_projects,
    pgs.total_added_green_m2
FROM arrondissements a
LEFT JOIN gs_agg  gs  ON gs.arrondissement_id  = a.arrondissement_id
LEFT JOIN pgs_agg pgs ON pgs.arrondissement_id = a.arrondissement_id;


-- DIM_QUARTER
-- Requires RENT_CONTROL table.

INSERT INTO PARIS_REALESTATE.STAR.DIM_QUARTER (
    quarter_id,
    zone_id,
    quarter_name,
    avg_reference_rent,
    rent_band_min,
    rent_band_max
)
SELECT
   QUARTER_ID,
    ZONE_ID,
    QUARTER_NAME,
    AVG(REFERENCE_RENT)     AS avg_reference_rent,
    AVG(MIN_RENT)           AS rent_band_min,
    AVG(MAX_RENT)           AS rent_band_max
FROM PARIS_REALESTATE.PUBLIC.RENT_CONTROL
GROUP BY QUARTER_ID, ZONE_ID, QUARTER_NAME;


-- DIM_GREEN_SPACES
-- Populated directly from green_spaces (no joins needed)
INSERT INTO PARIS_REALESTATE.STAR.DIM_GREEN_SPACES
SELECT  
GREEN_SPACE_ID,
GREEN_SPACE_NAME,
GREEN_SPACE_TYPE,
CATEGORY,
POSTAL_CODE,
POLYGON_AREA,
OPENING_YEAR,
GEO_SHAPE,
GEO_POINT,
LON,
LAT,
GEOMETRY
FROM PARIS_REALESTATE.PUBLIC.GREEN_SPACES;


-- FACT_TRANSACTION
-- One row per DVF transaction with all foreign keys resolved.
INSERT INTO PARIS_REALESTATE.STAR.FACT_TRANSACTION (
    transaction_key, date_id, arrondissement_id, location_id,
    quarter_id, property_type_id, property_value, lot_count,
    surface_area, room_count, price_per_sqm, match_score, data_quality_flag
)
WITH joined AS (
    SELECT
        d.TRANSACTION_KEY,
        TO_NUMBER(TO_CHAR(d.TRANSACTION_DATE, 'YYYYMMDD')) AS date_id,
        d.POSTAL_CODE AS arrondissement_id,
        l.LOCATION_ID AS location_id,
        NULL AS quarter_id,
        pt.PROPERTY_TYPE_ID,
        d.PROPERTY_VALUE, d.LOT_COUNT, d.SURFACE_AREA,
        d.ROOM_COUNT, d.PRICE_PER_SQM, d.MATCH_SCORE, d.DATA_QUALITY_FLAG
    FROM PARIS_REALESTATE.PUBLIC.DVF_AGGREGATED d
    LEFT JOIN PARIS_REALESTATE.STAR.DIM_LOCATION l
        ON l.STREET_CODE = d.STREET_CODE
        AND l.POSTAL_CODE = d.POSTAL_CODE
    LEFT JOIN PARIS_REALESTATE.STAR.DIM_PROPERTY_TYPE pt
        ON pt.PROPERTY_TYPE = d.PROPERTY_TYPE
)