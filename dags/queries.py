class Query:

    @staticmethod
    def load_v_table():
        sql = """
            MERGE INTO TASKS.TASK_1.V_TABLE
                USING ( 
                SELECT CSV_PARSER.V
                -- Query the stage for one file or use a pattern for multiple
                FROM @TASKS.TASK_1.GCS_STAGE (FILE_FORMAT => TASKS.TASK_1.TEXT_FORMAT, PATTERN=>'.*.csv') STG
                -- Lateral join to call our UDTF
                JOIN LATERAL TASKS.TASK_1.PARSE_CSV(STG.$1, ',', '"') 
                -- Partition by file to support multiple files at once
                OVER (PARTITION BY METADATA$FILENAME 
                -- Order by row number to ensure headers are first in each window
                ORDER BY METADATA$FILE_ROW_NUMBER) AS CSV_PARSER ) AS src ON V_TABLE.v: ID = src.v: ID
                WHEN NOT MATCHED THEN INSERT (V_TABLE.v) VALUES (src.v);
        """
        return sql

    @staticmethod
    def load_col_table():
        sql = """
            MERGE INTO TASKS.TASK_1.COL_TABLE
                USING TASKS.TASK_1.V_TABLE AS src ON COL_TABLE.ID = src.v:ID::INT                           
                WHEN NOT MATCHED THEN INSERT (COL_TABLE.ID, 
                                              COL_TABLE.NAME, 
                                              COL_TABLE.YEAR, 
                                              COL_TABLE.METACRITIC_RATING, 
                                              COL_TABLE.REVIEWER_RATING,
                                              COL_TABLE.POSITIVITY_RATIO, 
                                              COL_TABLE.TO_BEAT_MAIN, 
                                              COL_TABLE.TO_BEAT_EXTRA, 
                                              COL_TABLE.TO_BEAT_COMPLETIONIST, 
                                              COL_TABLE.EXTRA_CONTENT_LENGTH, 
                                              COL_TABLE.TAGS,
                                              COL_TABLE.INSERT_DT
                                              ) 
                                      VALUES (src.v: ID ,
                                              COALESCE(src.v: NAME, 'n. a.'),
                                              COALESCE(src.v: YEAR, -1),
                                              COALESCE(src.v: METACRITIC_RATING, -1),
                                              COALESCE(src.v: REVIEWER_RATING, -1),
                                              COALESCE(src.v: POSITIVITY_RATIO, -1),
                                              COALESCE(src.v: TO_BEAT_MAIN, -1),
                                              COALESCE(src.v: TO_BEAT_EXTRA, -1),
                                              COALESCE(src.v: TO_BEAT_COMPLETIONIST, -1),
                                              COALESCE(src.v: EXTRA_CONTENT_LENGTH, -1),
                                              src.v: TAGS,
                                              CURRENT_DATE);
        """
        return sql

    @staticmethod
    def load_max_rating_table():
        sql = """
            INSERT OVERWRITE INTO TASKS.TASK_1.RATING_TABLE
                SELECT YEAR, 
                       MAX(METACRITIC_RATING) AS max_metacritic_rating, 
                       MAX(REVIEWER_RATING) AS max_reviewer_rating
                FROM TASKS.TASK_1.COL_TABLE
                WHERE YEAR != -1
                GROUP BY YEAR 
        """
        return sql
