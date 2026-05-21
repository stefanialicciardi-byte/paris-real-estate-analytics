-- Paris Real Estate: Star Schema
-- Database: Snowflake


-- 1: Create database and schema

CREATE DATABASE IF NOT EXISTS PARIS_REALESTATE;
USE DATABASE PARIS_REALESTATE;

CREATE SCHEMA IF NOT EXISTS STAR;
USE SCHEMA STAR;


-- 2: Drop tables if they already exist (in case of re-running the script)

DROP TABLE IF EXISTS FACT_TRANSACTION;
DROP TABLE IF EXISTS DIM_DATE;
DROP TABLE IF EXISTS DIM_ARRONDISSEMENT;
DROP TABLE IF EXISTS DIM_LOCATION;
DROP TABLE IF EXISTS DIM_QUARTER;
DROP TABLE IF EXISTS DIM_PROPERTY_TYPE;


-- 3: Dimension tables

-- dim_date
-- One row per unique transaction date.
-- Splits the date into year, month, quarter, day for easy filtering.
CREATE OR REPLACE TABLE DIM_DATE (
    date_id          INTEGER       PRIMARY KEY,   -- format: YYYYMMDD e.g. 20250315
    date             DATE          NOT NULL, -- format:YYYY-MM-DD
    year             INTEGER       NOT NULL,
    month            INTEGER       NOT NULL,
    quarter          INTEGER       NOT NULL,
    month_name       VARCHAR(10)   NOT NULL,
    week             INTEGER       NOT NULL,
    day              INTEGER       NOT NULL,
    day_of_week      INTEGER       NOT NULL,
    day_name         VARCHAR(10)   NOT NULL,
    is_weekend       BOOLEAN       NOT NULL
);

-- dim_arrondissement
-- One row per arrondissement (1-20 for Paris).
-- Also stores aggregated green space metrics so we avoid a spatial join.
CREATE TABLE DIM_ARRONDISSEMENT (
    arrondissement_id     INTEGER       PRIMARY KEY,  -- equals postal_code e.g. 75006
    arrondissement_number INTEGER       NOT NULL,
    arrondissement_name   VARCHAR(100),
    -- Aggregated from existing green spaces
    green_space_count     INTEGER,
    total_green_area_m2   FLOAT,
    avg_green_space_area  FLOAT,
    -- Aggregated from planned green spaces
    planned_projects      INTEGER,
    total_added_green_m2  FLOAT
);

-- Drop old DIM_STREET table (renamed to DIM_LOCATION)
DROP TABLE IF EXISTS DIM_STREET;

-- dim_location
-- One row per unique street.
-- Contains address and geocoding info (denormalized for Star Schema simplicity).
CREATE TABLE DIM_LOCATION (
    location_id       INTEGER       PRIMARY KEY AUTOINCREMENT,
    street_code     VARCHAR(10),
    street_name     VARCHAR(200),
    street_type     VARCHAR(100),
    street_number   FLOAT,
    postal_code     INTEGER,
    address         VARCHAR(300),
    latitude        FLOAT,
    longitude       FLOAT,
    matched_address VARCHAR(300)
);

-- dim_quarter
-- One row per rent control quarter/zone.
-- Rent thresholds are stored directly here (denormalized).
CREATE TABLE DIM_QUARTER (
    quarter_id          INTEGER       PRIMARY KEY,
    zone_id             INTEGER,
    quarter_name        VARCHAR(200),
    avg_reference_rent  FLOAT,
    rent_band_min       FLOAT,
    rent_band_max       FLOAT
);

-- dim_property_type
-- Small lookup table for property types.
CREATE OR REPLACE TABLE DIM_PROPERTY_TYPE (
    property_type_id   INTEGER       PRIMARY KEY AUTOINCREMENT,
    property_type      VARCHAR(100)
);


-- dim_green_spaces
-- Table of existing green spaces in Paris. One record per green space.  
-- Has a spatial relationship with FACT_TRANSACTION (proximity to)
create or replace TABLE PARIS_REALESTATE.STAR.DIM_GREEN_SPACES (
	GREEN_SPACE_ID NUMBER(38,0) PRIMARY KEY NOT NULL,
	GREEN_SPACE_NAME VARCHAR(16777216) NOT NULL,
	GREEN_SPACE_TYPE VARCHAR(16777216) NOT NULL,
	CATEGORY VARCHAR(16777216) NOT NULL,
	POSTAL_CODE NUMBER(38,0) NOT NULL,
	POLYGON_AREA NUMBER(38,1),
	OPENING_YEAR NUMBER(38,0),
	GEO_SHAPE VARCHAR(16777216) NOT NULL,
	GEO_POINT VARCHAR(16777216) NOT NULL,
	LON NUMBER(38,16) NOT NULL,
	LAT NUMBER(38,15) NOT NULL,
	GEOMETRY VARCHAR(16777216) NOT NULL
);


-- 4: Fact table

-- fact_transaction
-- One row per DVF property transaction.
-- All dimension keys stored as foreign keys.
CREATE TABLE FACT_TRANSACTION (
    transaction_key  VARCHAR(100)  PRIMARY KEY,
    -- Foreign keys to dimensions
    date_id          INTEGER       REFERENCES DIM_DATE(date_id),
    arrondissement_id INTEGER      REFERENCES DIM_ARRONDISSEMENT(arrondissement_id),
    location_id        INTEGER       REFERENCES DIM_LOCATION(location_id),
    quarter_id       INTEGER       REFERENCES DIM_QUARTER(quarter_id),
    property_type_id INTEGER       REFERENCES DIM_PROPERTY_TYPE(property_type_id),
    -- Measures
    property_value   FLOAT,
    lot_count        INTEGER,
    surface_area     FLOAT,
    room_count       INTEGER,
    price_per_sqm    FLOAT,
    match_score      FLOAT,
    data_quality_flag VARCHAR(50)
);
