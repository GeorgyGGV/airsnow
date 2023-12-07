from datetime import datetime
from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from queries import Query


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

with dag:

    loading_v_table = SnowflakeOperator(
        sql=Query.load_v_table(),
        snowflake_conn_id="snowflake",
        task_id="loading_v_table"
    )
    loading_col_table = SnowflakeOperator(
        sql=Query.load_col_table(),
        snowflake_conn_id="snowflake",
        task_id="loading_col_table"
    )
    loading_max_rating_table = SnowflakeOperator(
        sql=Query.load_max_rating_table(),
        snowflake_conn_id="snowflake",
        task_id="loading_max_rating_table"
    )

    loading_v_table >> loading_col_table >> loading_max_rating_table

