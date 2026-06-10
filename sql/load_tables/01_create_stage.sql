/*/ Indicating database and schema to use /*/
USE DATABASE PARIS_REALESTATE;
USE SCHEMA STAR;

/*/ Creating the staging area for our pre-processed csv files /*/
CREATE STAGE IF NOT EXISTS project_stage 
	DIRECTORY = ( ENABLE = true ) 
	COMMENT = 'Staging area for the preprocessed csv files of Paris real estate data';