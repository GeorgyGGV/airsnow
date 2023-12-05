from datetime import datetime
from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

# Create DAG default arguments
args = {
    "owner": "Gio",
    "start_date": datetime(2023, 3, 10, 12, 00)
}
# Create DAG object
dag = DAG(
    dag_id="Georgy",
    default_args=args,
    schedule_interval=None
)

creating_v_table = '''
            CREATE OR REPLACE TABLE TASKS.PUBLIC.task1_v_table AS SELECT 
              CSV_PARSER.V
            -- Query the stage for one file or use a pattern for multiple
            FROM @MY_STAGE (FILE_FORMAT => TEXT_FORMAT, PATTERN=>'.*.csv.gz') STG
            -- Lateral join to call our UDTF
            JOIN LATERAL PARSE_CSV(STG.$1, ',', '"') 
              -- Partition by file to support multiple files at once
            OVER (PARTITION BY METADATA$FILENAME 
              -- Order by row number to ensure headers are first in each window
            ORDER BY METADATA$FILE_ROW_NUMBER) AS CSV_PARSER;
'''

creating_col_table = '''
            CREATE OR REPLACE TABLE TASKS.PUBLIC.task_col_table (
                ID INT,
                NAME VARCHAR,
                YEAR INT,
                METACRITIC_RATING INT,
                REVIEWER_RATING INT,
                POSITIVITY_RATIO FLOAT,
                TO_BEAT_MAIN FLOAT,
                TO_BEAT_EXTRA FLOAT,
                TO_BEAT_COMPLETIONIST FLOAT,
                EXTRA_CONTENT_LENGTH FLOAT,
                TAGS VARCHAR
            ) AS SELECT V: ID, V: NAME, V: YEAR, V: METACRITIC_RATING, V: REVIEWER_RATING, 
              V: POSITIVITY_RATIO, V: TO_BEAT_MAIN, V: TO_BEAT_EXTRA, 
              V: TO_BEAT_COMPLETIONIST, V: EXTRA_CONTENT_LENGTH, V: TAGS  
            FROM task1_v_table;
'''

creating_max_rating_table = '''
            CREATE OR REPLACE TABLE TASKS.PUBLIC.task1_max_rating AS
            SELECT year, MAX(METACRITIC_RATING) AS max_metacritic_rating , MAX(REVIEWER_RATING) AS max_reviewer_rating
            FROM tasks.public.col_table
            GROUP BY year
            ORDER BY year DESC
'''


with dag:
    creating_v_table = SnowflakeOperator(
        sql=creating_v_table,
        snowflake_conn_id="snowflake",
        task_id="creating_v_table",)

    creating_col_table = SnowflakeOperator(
        sql=creating_col_table,
        snowflake_conn_id="snowflake",
        task_id="creating_col_table",)

    creating_max_rating_table = SnowflakeOperator(
        sql=creating_max_rating_table,
        snowflake_conn_id="snowflake",
        task_id="creating_max_rating_table" )


creating_v_table >> creating_col_table >> creating_max_rating_table
